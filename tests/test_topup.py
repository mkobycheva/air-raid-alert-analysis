"""Synthetic messages only; upstream behavior tests skip without its clone."""

import asyncio
from datetime import datetime, timedelta, timezone
import json
import logging
import os
from pathlib import Path
import pickle
from types import ModuleType, SimpleNamespace

import pandas as pd
import pytest

from airalerts.collect import topup_official as topup


def message(message_id: int, hours: float = 0, text: str = "public notice") -> SimpleNamespace:
    return SimpleNamespace(id=message_id, date=datetime(2026, 9, 7, tzinfo=timezone.utc) + timedelta(hours=hours),
                           message=text)


def interval() -> dict[str, str]:
    return dict(zip(topup.COLUMNS, ["A", "", "", "oblast", "2026-09-07 00:00:00+00:00",
                                   "2026-09-07 01:00:00+00:00", "official"]))


class GlueProcessor:
    """A recording stub, deliberately without any upstream parsing logic."""
    def __init__(self, last_id: int = 0):
        self.last_processed_id = last_id
        self.completed_alerts = []
        self.active_alerts_by_location = {}
        self.seen = []

    def parse_message(self, msg):
        return (["location"], True, False) if msg.message == "accepted" else (None, None, None)

    def process_message(self, msg):
        self.seen.append(msg.id)


def test_ordering_replays_and_duplicates() -> None:
    processor = GlueProcessor(last_id=2)
    rows = topup.process_messages(processor, [message(5), message(1), message(3), message(5), message(4, text="")])
    assert processor.seen == [3, 5]
    assert processor.last_processed_id == 5
    assert rows == []
    topup.process_messages(processor, [message(3), message(5)])
    assert processor.seen == [3, 5]


def test_new_closed_rows_not_history_or_duplicate() -> None:
    row = interval()
    old = dict(row, started_at="2026-09-06 00:00:00+00:00", finished_at="2026-09-06 01:00:00+00:00")
    existing = pd.DataFrame([row])
    result = topup.merge_new_rows(existing, [row, old], pd.DataFrame([old, old]))
    assert result.to_dict(orient="records") == [row]
    # Blank CSV locations reload as NaN; canonicalization must still dedupe.
    existing.loc[0, "raion"] = float("nan")
    assert len(topup.merge_new_rows(existing, [row], pd.DataFrame([old]))) == 1


def test_save_resume_idempotency_and_csv_before_state(tmp_path, monkeypatch) -> None:
    csv, state = tmp_path / "topup.csv", tmp_path / "state.pkl"
    processor = GlueProcessor(last_id=5)
    history = pd.DataFrame(columns=topup.COLUMNS)
    topup.save_collection(processor, [interval()], history, csv, state)
    csv_before, state_before = csv.read_bytes(), state.read_bytes()
    topup.save_collection(processor, [interval()], history, csv, state)
    assert csv.read_bytes() == csv_before
    assert state.read_bytes() == state_before
    assert pickle.loads(state_before)["last_processed_id"] == 5
    original_write = topup.atomic_write
    def fail_state(path, content):
        if path == state:
            raise OSError("synthetic write interruption")
        original_write(path, content)
    monkeypatch.setattr(topup, "atomic_write", fail_state)
    processor.last_processed_id = 6
    new_row = dict(interval(), started_at="2026-09-08 00:00:00+00:00", finished_at="2026-09-08 01:00:00+00:00")
    with pytest.raises(OSError):
        topup.save_collection(processor, [new_row], history, csv, state)
    assert pickle.loads(state.read_bytes())["last_processed_id"] == 5
    monkeypatch.setattr(topup, "atomic_write", original_write)
    topup.save_collection(processor, [new_row], history, csv, state)
    assert len(pd.read_csv(csv)) == 2
    assert pickle.loads(state.read_bytes())["last_processed_id"] == 6


def test_missing_companion_csv_refused(tmp_path) -> None:
    state = tmp_path / "state.pkl"
    state.write_bytes(pickle.dumps({"format_version": 1, "last_processed_id": 5, "active_alerts_by_location": {}}))
    with pytest.raises(topup.TopupError, match="CSV|csv"):
        topup.save_collection(GlueProcessor(), [], pd.DataFrame(columns=topup.COLUMNS), tmp_path / "missing.csv", state)


def test_upstream_pickle_copy_and_local_resume(tmp_path) -> None:
    upstream_pickle = tmp_path / "upstream.pkl"
    sidecar = tmp_path / "upstream_last_id.txt"
    original = pickle.dumps({"synthetic_location": SimpleNamespace(started_at=message(1).date)})
    upstream_pickle.write_bytes(original)
    sidecar.write_text("5")
    module = SimpleNamespace(pkl_file_path=upstream_pickle, last_processed_id_path=sidecar)
    local = tmp_path / "local.pkl"
    state = topup.load_state(module, local)
    state["active_alerts_by_location"].clear()
    assert upstream_pickle.read_bytes() == original
    assert not local.exists()
    local.write_bytes(pickle.dumps(dict(state, last_processed_id=10)))
    assert topup.load_state(module, local)["last_processed_id"] == 10


@pytest.mark.parametrize("mode,texts", [
    ("diagnose", ["accepted"]),
    ("collect", []),
    ("collect", ["rejected", "rejected", "accepted"]),
])
def test_runtime_diagnose_and_hard_stops_write_nothing(tmp_path, monkeypatch, mode, texts) -> None:
    """Mock Telegram transport only; exercise the real orchestration guards."""
    class SyntheticFlood(Exception):
        seconds = 1
    rows = [message(topup.BASELINE_ID + i + 1, text=text) for i, text in enumerate(texts)]
    class Client:
        def __init__(self, *args, **kwargs):
            pass
        async def connect(self):
            pass
        async def disconnect(self):
            pass
        async def is_user_authorized(self):
            return True
        async def get_messages(self, *args, **kwargs):
            return rows[-1:]
        async def iter_messages(self, *args, **kwargs):
            for row in rows:
                yield row
    transport = ModuleType("telethon")
    transport.TelegramClient = Client
    errors = ModuleType("telethon.errors")
    errors.FloodWaitError = SyntheticFlood
    sessions = ModuleType("telethon.sessions")
    sessions.StringSession = lambda value: None
    for name, module in [("telethon", transport), ("telethon.errors", errors), ("telethon.sessions", sessions)]:
        monkeypatch.setitem(topup.sys.modules, name, module)
    monkeypatch.chdir(tmp_path)
    for name, value in [("TG_API_ID", "123"), ("TG_API_HASH", "synthetic-hash"), ("TG_SESSION", "synthetic-session")]:
        monkeypatch.setenv(name, value)
    monkeypatch.setattr(topup, "import_upstream", lambda root: None)
    monkeypatch.setattr(topup, "load_state", lambda module: {})
    monkeypatch.setattr(topup, "make_processor", lambda module, state: GlueProcessor(topup.BASELINE_ID))
    args = SimpleNamespace(mode=mode, summary=None)
    result = asyncio.run(topup.run(args, topup.credentials(), tmp_path))
    assert result == (0 if mode == "diagnose" else 2)
    assert list(tmp_path.iterdir()) == []


def test_diagnostic_hard_stops_and_samples() -> None:
    processor = GlueProcessor(last_id=topup.BASELINE_ID)
    now = datetime(2026, 9, 7, tzinfo=timezone.utc)
    messages = [message(topup.BASELINE_ID + i, text="rejected" * 80) for i in range(1, 15)]
    summary = topup.diagnostic(processor, messages, messages[:5], now)
    assert summary["new_messages"] == 14
    assert summary["accepted"] == 0
    assert len(summary["rejected_samples"]) == 10
    assert all(len(sample["text"]) == 300 for sample in summary["rejected_samples"])
    assert len(summary["new_messages_per_day_last_60_days"]) == 60
    assert summary["new_messages_per_day_last_60_days"]["2026-09-07"] == 14
    assert processor.last_processed_id == topup.BASELINE_ID
    assert "rejects most" in topup.hard_stop(summary)
    empty = topup.diagnostic(processor, [], [], now)
    assert "silent after that id" in topup.hard_stop(empty)
    half = dict(summary, accepted=7, rejected=7)
    assert topup.hard_stop(half) is None


def test_flood_retry_continues_after_last_seen_id(monkeypatch) -> None:
    class SyntheticFlood(Exception):
        seconds = 2
    class Client:
        def __init__(self):
            self.calls = []
        async def iter_messages(self, channel, **kwargs):
            self.calls.append(kwargs)
            if len(self.calls) == 1:
                yield message(3)
                raise SyntheticFlood()
            yield message(4)
    waits = []
    async def sleep(seconds):
        waits.append(seconds)
    monkeypatch.setattr(topup.asyncio, "sleep", sleep)
    client = Client()
    rows = asyncio.run(topup.fetch_messages(client, 2, SyntheticFlood, max_id=5))
    assert [row.id for row in rows] == [3, 4]
    assert [call["min_id"] for call in client.calls] == [2, 3]
    assert all(call["max_id"] == 5 and call["wait_time"] == 1 for call in client.calls)
    assert waits == [2]


@pytest.mark.parametrize("missing", ["TG_API_ID", "TG_API_HASH", "TG_SESSION"])
def test_missing_credentials_name_only(monkeypatch, missing) -> None:
    # Missing variables are tested without reading real credentials or network.
    for name in ("TG_API_ID", "TG_API_HASH", "TG_SESSION"):
        monkeypatch.delenv(name, raising=False)
    if missing != "TG_API_ID":
        monkeypatch.setenv("TG_API_ID", "123")
    if missing == "TG_SESSION":
        monkeypatch.setenv("TG_API_HASH", "synthetic-placeholder")
    with pytest.raises(topup.TopupError, match=f"Missing environment variable: {missing}$"):
        topup.credentials()


def test_json_redaction_remains_valid() -> None:
    result = topup.safe_json({"text": "synthetic-placeholder", "id": 123456}, ("synthetic-placeholder", "123"))
    assert json.loads(result) == {"text": "[REDACTED]", "id": 123456}


def test_metrics_level_comparison_and_empty_topup() -> None:
    raw = pd.DataFrame([dict(interval(), started_at="2026-09-06 00:00:00+00:00")])
    frame = pd.DataFrame([interval()])
    summary = topup.collection_metrics(frame, raw)
    assert summary["duplicates_vs_raw"] == 0
    assert summary["share_duration_3600s"] == 1
    assert not summary["level_share_mismatch_gt10_percentage_points"]
    changed = frame.assign(level="raion")
    assert topup.collection_metrics(changed, raw)["level_share_mismatch_gt10_percentage_points"]
    empty = topup.collection_metrics(pd.DataFrame(columns=topup.COLUMNS), raw)
    assert empty["rows"] == 0
    assert empty["share_duration_3600s"] is None


@pytest.fixture
def upstream_processor():
    root = os.environ.get("UPSTREAM_DIR")
    if not root:
        pytest.skip("UPSTREAM_DIR missing; upstream parser unavailable (glue tests run independently)")
    logging.disable(logging.CRITICAL)
    try:
        module = topup.import_upstream(Path(root))
        return topup.make_processor(module, {"active_alerts_by_location": {}, "last_processed_id": 0})
    except (ImportError, OSError, topup.TopupError):
        pytest.skip("Upstream parser or dependencies unavailable; no parser logic is copied into tests")


def alert_text(processor, activated: bool) -> str:
    hashtag = next(key for key, location in processor.hash_states_by_name.items() if location[3] == "oblast")
    return ("🔴 Повітряна тривога" if activated else "🟢 Відбій тривоги") + "\n" + hashtag


def test_upstream_fresh_start(upstream_processor) -> None:
    p = upstream_processor
    topup.process_messages(p, [message(1, text=alert_text(p, True))])
    assert len(p.active_alerts_by_location) == 1
    assert not p.completed_alerts


def test_upstream_close(upstream_processor) -> None:
    p = upstream_processor
    rows = topup.process_messages(p, [message(1, text=alert_text(p, True)), message(2, 1, alert_text(p, False))])
    assert len(rows) == 1
    assert not p.active_alerts_by_location
    assert pd.Timestamp(rows[0]["finished_at"]) - pd.Timestamp(rows[0]["started_at"]) == timedelta(hours=1)


def test_upstream_restart_within_three_hours(upstream_processor) -> None:
    p = upstream_processor
    topup.process_messages(p, [message(1, text=alert_text(p, True)), message(2, 2, alert_text(p, True))])
    assert not p.completed_alerts
    assert next(iter(p.active_alerts_by_location.values())).started_at == message(2, 2).date


def test_upstream_restart_after_three_hours(upstream_processor) -> None:
    p = upstream_processor
    rows = topup.process_messages(p, [message(1, text=alert_text(p, True)), message(2, 4, alert_text(p, True))])
    assert len(rows) == 1
    assert pd.Timestamp(rows[0]["finished_at"]) - pd.Timestamp(rows[0]["started_at"]) == timedelta(hours=1)
    assert next(iter(p.active_alerts_by_location.values())).started_at == message(2, 4).date


def test_upstream_rejected_message(upstream_processor) -> None:
    p = upstream_processor
    rejected = message(1, text="synthetic unrecognized notice\n#unknown_synthetic_location")
    assert not topup.accepts(p, rejected)
    topup.process_messages(p, [rejected])
    assert p.last_processed_id == 1
    assert not p.active_alerts_by_location and not p.completed_alerts
