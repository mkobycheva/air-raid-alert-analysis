import numpy as np
import pandas as pd
import pytest

from airalerts.compare import daily_presence, intersection_hours, overlap_flags, pair_table, template_group, utc
from airalerts.grid import episodes, exact_share, time_grid
from airalerts.io import official_variant, valid_end


def frame(rows: list[tuple[str, str, str, str]]) -> pd.DataFrame:
    result = pd.DataFrame(rows, columns=["oblast", "level", "started_at", "finished_at"])
    for col in ("started_at", "finished_at"):
        result[col] = pd.to_datetime(result[col], utc=True, format="ISO8601")
    return result


def test_definition_variants_do_not_mix_oblasts() -> None:
    df = frame([("A", "oblast", "2026-01-01", "2026-01-01 01:00"),
                ("A", "raion", "2026-01-01", "2026-01-02 06:00"),
                ("A", "hromada", "2026-01-01", "2026-01-01 02:00"),
                ("B", "hromada", "2026-01-01", "2026-01-02 06:00")])
    assert official_variant(df, "A").index.tolist() == [0, 1, 2, 3]
    assert official_variant(df, "B").index.tolist() == [0, 1]
    assert official_variant(df, "C").index.tolist() == [0, 2]
    assert official_variant(df, "D").index.tolist() == [0]
    with pytest.raises(ValueError):
        official_variant(df, "E")


def test_half_open_30min_union_and_episodes() -> None:
    df = frame([("A", "raion", "2026-01-01 14:40", "2026-01-01 15:10"),
                ("A", "hromada", "2026-01-01 14:50", "2026-01-01 15:20"),
                ("A", "oblast", "2026-01-01 15:30", "2026-01-01 16:00")])
    assert time_grid(df, "2026-01-01 14:00", "2026-01-01 16:00", "30min")["A"].tolist() == [False, True, True, True]
    assert len(episodes(df, "A", "2026-01-01 14:00", "2026-01-01 16:00")) == 2
    assert exact_share(df, "A", "2026-01-01 14:00", "2026-01-01 16:00") == pytest.approx(70 / 120)


def test_tail_uses_starts_not_closures() -> None:
    df = frame([("A", "oblast", "2026-01-01", "2026-02-01"),
                ("A", "oblast", "2026-01-05", "2026-01-05 01:00")])
    assert valid_end(df) == utc("2026-01-03")


def test_conditional_probabilities_and_intersection() -> None:
    a = frame([("A", "raion", "2026-01-01 00:00", "2026-01-01 02:00")])
    b = frame([("A", "oblast", "2026-01-01 01:00", "2026-01-01 03:00")])
    start, end = utc("2026-01-01"), utc("2026-01-01 04:00")
    row = pair_table(a, b, "a", "b", start, end, "test", ["A"]).iloc[0]
    assert row.p_a_given_b_60min == .5
    assert row.p_b_given_a_60min == .5
    assert row.a_total_hours == 2
    assert intersection_hours(a, b, "A", start, end) == 1
    assert overlap_flags(b, a, "A", start, end).tolist() == [True]
    later = b.copy()
    later["started_at"] = utc("2026-01-01 02:00")
    assert overlap_flags(later, a, "A", start, end).tolist() == [False]
    zero = pair_table(a, b.iloc[:0], "a", "b", start, end, "test", ["A"]).iloc[0]
    assert np.isnan(zero.p_a_given_b_60min)


def test_kyiv_daily_presence_dst() -> None:
    start = pd.Timestamp("2026-03-28", tz="Europe/Kyiv").tz_convert("UTC")
    end = pd.Timestamp("2026-03-31", tz="Europe/Kyiv").tz_convert("UTC")
    df = frame([("A", "raion", "2026-03-28 23:30", "2026-03-29 00:30")])
    daily = daily_presence(df, start, end, ["A"])
    assert daily["A"].tolist() == [False, True, False]
    assert (daily.index[2] - daily.index[1]).total_seconds() == 23 * 3600


@pytest.mark.parametrize("text,group", [("Повітряна тривога", "siren"), ("Відбій загрози застосування КАБ", "KAB"),
                                        ("Загроза артобстрілу", "artillery"), ("Загроза ударних БпЛА", "UAV"),
                                        ("Загроза балістичного удару", "ballistic-missile")])
def test_template_groups(text: str, group: str) -> None:
    assert template_group(text) == group


def test_offline_pipeline_missing_api_and_determinism(tmp_path, monkeypatch) -> None:
    from airalerts import compare
    official = frame([("Lvivska oblast", "oblast", "2024-01-01", "2024-01-01 01:00"),
                      ("Lvivska oblast", "hromada", "2024-05-01", "2024-05-02 06:00"),
                      ("Lvivska oblast", "raion", "2026-09-07", "2026-09-07 01:00")])
    official["raion"], official["hromada"] = "R", "H"
    volunteer = frame([("Lvivska oblast", "oblast", "2024-01-01", "2024-01-01 02:00"),
                       ("Lvivska oblast", "oblast", "2026-10-10", "2026-10-10 01:00")])
    volunteer["naive"] = False
    monkeypatch.setattr(compare, "load_official", lambda path: official.copy())
    monkeypatch.setattr(compare, "load_volunteer", lambda path: volunteer.copy())
    out = tmp_path / "compare"
    kwargs = dict(raw_dir=tmp_path, api_path=tmp_path / "missing.csv", census_dir=tmp_path,
                  out=out, start=utc("2022-03-15"), plots=False)
    tables = compare.run_comparison(**kwargs)
    assert len(tables["official_volunteer"]) == 24
    assert "SKIPPED alerts.in.ua" in (out / "source_comparison.md").read_text()
    before = (out / "official_volunteer.csv").read_bytes()
    (out / "api_counts.csv").write_text("field,value,count\nold,stale,10\n")
    compare.run_comparison(**kwargs)
    assert (out / "official_volunteer.csv").read_bytes() == before
    assert pd.read_csv(out / "api_counts.csv").empty
    from airalerts.collect.alerts_in_ua import normalise
    from datetime import datetime, timezone
    api_path = tmp_path / "empty_api.csv"
    normalise({}, datetime(2026, 10, 11, tzinfo=timezone.utc)).to_csv(api_path, index=False)
    kwargs["api_path"] = api_path
    compare.run_comparison(**kwargs)
    assert "SKIPPED API comparison: no usable trimmed overlap" in (out / "source_comparison.md").read_text()
