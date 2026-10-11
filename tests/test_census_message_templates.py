"""Offline synthetic census tests; the CLI and Telegram are never invoked."""

import asyncio
from datetime import datetime, timedelta, timezone
import logging
import os
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from airalerts.collect import census_message_templates as census
from airalerts.collect.topup_official import TopupError, import_upstream, make_processor


CASES = [
    ("🔴 14:40 Повітряна тривога в Київська область", "activated", "🔴 {T} Повітряна тривога в {LOC}"),
    ("🟢 15:10 Відбій тривоги в Київська область.", "deactivated", "🟢 {T} Відбій тривоги в {LOC}"),
    ("🟡 15:10 Відбій тривоги в Київська область (тривога ще триває у якомусь районі)",
     "deactivated", "🟡 {T} Відбій тривоги в {LOC} (тривога ще триває у якомусь районі)"),
    ("🔴🔴 16:20 Загроза ударних БпЛА в м. Київ", "activated", "🔴🔴 {T} Загроза ударних БпЛА в {LOC}"),
    ("🔴 16:30 Загроза артобстрілу в Київська область", "activated", "🔴 {T} Загроза артобстрілу в {LOC}"),
    ("🟢 17:00 Відбій загрози ударних БпЛА в Київська область", "deactivated", "🟢 {T} Відбій загрози ударних БпЛА в {LOC}"),
    ("🔴 18:00 Повітряна тривога в Невідоме місце", "unparseable", "🔴 {T} Повітряна тривога в {LOC}"),
]


def message(text: str, message_id: int = 1, hours: int = 0) -> SimpleNamespace:
    return SimpleNamespace(message=text, id=message_id,
                           date=datetime(2026, 10, 10, tzinfo=timezone.utc) + timedelta(hours=hours))


class ParserStub:
    """Return canned upstream results; contain no location or siren parsing."""
    def __init__(self, outputs: dict[int, tuple[Any, Any, Any]], ignored: set[int] | None = None):
        self.outputs = outputs
        self.ignored = ignored or set()
        self.called: list[int] = []
        self.hash_states_by_name = {
            "#known": ("A", "", "", "oblast"),
            "#district": ("A", "B", "", "raion"),
            "#community": ("A", "B", "C", "hromada"),
            "#canonical_alias": ("A", "B", "C", "hromada"),
        }

    def parse_message(self, msg: Any) -> tuple[Any, Any, Any]:
        self.called.append(msg.id)
        return self.outputs[msg.id]

    def is_ignored_message(self, msg: Any) -> bool:
        return msg.id in self.ignored


@pytest.mark.parametrize("line,classification,template", CASES)
def test_synthetic_templates_and_upstream_delegation(line: str, classification: str, template: str) -> None:
    output = (["#known"], classification == "activated", classification == "deactivated")
    if classification == "unparseable":
        output = (None, None, None)
    parser = ParserStub({1: output})
    hashtag = "#unknown" if classification == "unparseable" else "#known"
    msg = message(line + "\n" + hashtag)
    assert census.template_first_line(msg.message) == template
    result, levels, level = census.classify_message(parser, msg)
    assert result == classification
    assert level == ("mixed" if classification == "unparseable" else "oblast")
    assert levels == (frozenset() if classification == "unparseable" else frozenset({"oblast"}))
    assert parser.called == [1]


def test_mixed_known_unknown_levels_and_upstream_alias() -> None:
    parser = ParserStub({1: (["#known", "#district"], True, False),
                         2: (None, None, None), 3: (["#canonical_alias"], False, True)})
    assert census.classify_message(parser, message("start\n#known #district", 1))[1:] == (frozenset({"oblast", "raion"}), "mixed")
    assert census.classify_message(parser, message("notice\n#known #unknown", 2))[1:] == (frozenset({"oblast"}), "mixed")
    assert census.classify_message(parser, message("end\n#original_alias", 3))[1:] == (frozenset({"hromada"}), "hromada")


def test_ignored_and_empty_messages() -> None:
    parser = ParserStub({1: (None, None, None)}, ignored={1})
    assert census.classify_message(parser, message("Тестовий Регіон\n#known"))[0] == "ignored"
    assert census.classify_message(parser, message("", 2)) == ("unparseable", frozenset(), "mixed")
    assert parser.called == [1]


def test_bullet_lists_and_first_line_only() -> None:
    assert census.template_first_line("🟢 17:00 Відбій тривоги в\n• Київ\n• Одеса\n#known") == "🟢 {T} Відбій тривоги в {LOC}"
    assert census.template_first_line("🟢 17:00 Відбій тривоги в • Київ • Одеса") == "🟢 {T} Відбій тривоги в {LOC}"


def test_group_counts_dates_three_distinct_raw_examples() -> None:
    messages = [message(f"🔴 {hour:02}:00 Повітряна тривога в Місто\n#known", hour, hour) for hour in range(1, 6)]
    parser = ParserStub({msg.id: (["#known"], True, False) for msg in messages})
    frame = census.census(list(reversed(messages)), parser)
    assert frame.columns.tolist() == census.COLUMNS
    assert len(frame) == 1
    assert frame.iloc[0]["count"] == 5
    assert frame.iloc[0]["first_seen"] == messages[0].date.isoformat()
    assert frame.iloc[0]["last_seen"] == messages[-1].date.isoformat()
    assert frame.iloc[0]["example_1"] == messages[-1].message.split("\n")[0]
    assert len({frame.iloc[0][f"example_{i}"] for i in range(1, 4)}) == 3
    assert census.census([], parser).empty


def test_descending_fetch_bounds_limit_and_flood_wait(monkeypatch) -> None:
    class SyntheticFlood(Exception):
        seconds = 2
    start = datetime(2026, 10, 10, tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    class Client:
        def __init__(self) -> None:
            self.calls: list[dict[str, Any]] = []
        async def iter_messages(self, channel: str, **kwargs: Any):
            self.calls.append(kwargs)
            if len(self.calls) == 1:
                yield SimpleNamespace(id=10, date=end, message="outside")
                yield SimpleNamespace(id=9, date=start + timedelta(hours=2), message="inside")
                raise SyntheticFlood()
            yield SimpleNamespace(id=8, date=start + timedelta(hours=2), message="same date")
            yield SimpleNamespace(id=7, date=start, message="boundary")
            yield SimpleNamespace(id=6, date=start - timedelta(seconds=1), message="old")
            raise AssertionError("Iterator must stop before reading further")
    waits: list[int] = []
    async def sleep(seconds: int) -> None:
        waits.append(seconds)
    monkeypatch.setattr(census.asyncio, "sleep", sleep)
    async def fetch(client: Client, limit: int | None) -> list[Any]:
        return [msg async for msg in census.iter_range(client, start, end, limit, SyntheticFlood)]
    client = Client()
    assert [msg.id for msg in asyncio.run(fetch(client, None))] == [9, 8, 7]
    assert client.calls[0]["offset_date"] == end
    assert client.calls[1]["offset_id"] == 9
    assert client.calls[1]["offset_date"] is None
    assert all(call["reverse"] is False for call in client.calls)
    assert waits == [2]
    assert [msg.id for msg in asyncio.run(fetch(Client(), 1))] == [9]


def test_missing_environment_name_only(monkeypatch) -> None:
    for pair in census.ENV_NAMES:
        for name in pair:
            monkeypatch.delenv(name, raising=False)
    with pytest.raises(TopupError, match=r"Missing environment variable: API_ID \(or TG_API_ID\)$"):
        census.read_credentials()


def test_topup_environment_aliases_and_precedence(monkeypatch) -> None:
    for pair in census.ENV_NAMES:
        for name in pair:
            monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("TG_API_ID", "123")
    monkeypatch.setenv("TG_API_HASH", "synthetic-hash")
    monkeypatch.setenv("TG_SESSION", "synthetic-session")
    assert census.read_credentials() == (123, "synthetic-hash", "synthetic-session")
    monkeypatch.setenv("API_ID", "456")
    assert census.read_credentials()[0] == 456


def test_dated_output_requires_explicit_overwrite(tmp_path) -> None:
    from datetime import date
    import pandas as pd
    path = tmp_path / census.report_path(date(2026, 3, 1), date(2026, 9, 8)).name
    assert path.name == "census_message_templates_2026-03-01_2026-09-08.csv"
    original = pd.DataFrame({"count": [1]})
    census.write_report(path, original)
    before = path.read_bytes()
    with pytest.raises(TopupError, match="--overwrite"):
        census.write_report(path, pd.DataFrame({"count": [2]}))
    assert path.read_bytes() == before
    census.write_report(path, pd.DataFrame({"count": [2]}), overwrite=True)
    assert pd.read_csv(path)["count"].tolist() == [2]


@pytest.mark.parametrize("line,expected,template", CASES)
def test_real_upstream_synthetic_classification(line: str, expected: str, template: str) -> None:
    root = os.environ.get("UPSTREAM_DIR")
    if not root:
        pytest.skip("UPSTREAM_DIR missing; actual parser classification cannot be verified")
    logging.disable(logging.CRITICAL)
    try:
        module = import_upstream(Path(root))
        parser = make_processor(module, {"last_processed_id": 0, "active_alerts_by_location": {}})
    except (ImportError, OSError, TopupError):
        pytest.skip("Upstream parser or dependency unavailable; parser is never copied into tests")
    tag = next(key for key, value in parser.hash_states_by_name.items() if value[3] == "oblast")
    if expected == "unparseable":
        tag = "#unknown_synthetic_location"
    assert census.classify_message(parser, message(line + "\n" + tag))[0] == expected
