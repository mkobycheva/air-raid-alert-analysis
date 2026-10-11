import pandas as pd
import pytest

from airalerts.grid import exact_share, hourly_grid
from airalerts.io import load_official, load_volunteer, trim_tail, validate


def intervals(*rows: tuple[str, str, str, str]) -> pd.DataFrame:
    df = pd.DataFrame(rows, columns=["oblast", "level", "started_at", "finished_at"])
    for column in ("started_at", "finished_at"):
        df[column] = pd.to_datetime("2026-02-01 " + df[column], utc=True, format="ISO8601")
    return df


@pytest.mark.parametrize("start,end,expected", [
    ("14:40", "15:10", [True, True]),
    ("14:00", "15:00", [True, False]),
    ("12:00", "13:00", [False, False]),
    ("16:00", "17:00", [False, False]),
    ("15:00", "15:00", [False, False]),
    ("14:30", "14:30", [False, False]),
    ("13:30", "16:30", [True, True]),
])
def test_hour_boundaries(start: str, end: str, expected: list[bool]) -> None:
    grid = hourly_grid(intervals(("A", "oblast", start, end)),
                       "2026-02-01 14:00", "2026-02-01 16:00")
    assert grid["A"].tolist() == expected
    assert str(grid.index.tz) == "UTC"
    assert grid["A"].dtype == bool


def test_overlaps_and_levels() -> None:
    df = intervals(("A", "oblast", "14:10", "14:50"),
                   ("A", "raion", "14:20", "15:10"),
                   ("A", "hromada", "15:20", "15:30"),
                   ("B", "oblast", "12:00", "13:00"))
    grid = hourly_grid(df, "2026-02-01 14:00", "2026-02-01 16:00")
    assert grid["A"].tolist() == [True, True]
    assert not grid["B"].any()
    shares = exact_share(df, "2026-02-01 14:00", "2026-02-01 16:00")
    assert shares["A"] == pytest.approx(70 / 120)
    assert shares["B"] == 0


def test_exact_clips_and_preserves_seconds() -> None:
    df = intervals(("A", "oblast", "13:00", "14:30:30"),
                   ("A", "raion", "14:20", "16:30"))
    assert exact_share(df, "2026-02-01 14:00", "2026-02-01 16:00")["A"] == 1
    assert exact_share(df.iloc[:1], "2026-02-01 14:00", "2026-02-01 16:00")["A"] == pytest.approx(30.5 / 120)


def test_partial_final_hour() -> None:
    df = intervals(("A", "oblast", "15:40", "16:00"))
    grid = hourly_grid(df, "2026-02-01 14:00", "2026-02-01 15:30")
    assert grid["A"].tolist() == [False, False]


def test_loaders(tmp_path) -> None:
    official = tmp_path / "official.csv"
    row = "A,,,oblast,2026-02-01 14:00,2026-02-01 15:00,official\n"
    official.write_text("oblast,raion,hromada,level,started_at,finished_at,source\n" + row * 2)
    loaded = load_official(official)
    assert len(loaded) == 1
    assert loaded["duration_s"].iloc[0] == 3600
    assert loaded["naive_guess"].iloc[0]
    assert str(loaded["started_at"].dt.tz) == "UTC"
    volunteer = tmp_path / "volunteer.csv"
    volunteer.write_text("region,started_at,finished_at,naive\nA,2026-02-01 14:00,2026-02-01 14:30,True\n")
    assert load_volunteer(volunteer).columns.tolist() == ["oblast", "started_at", "finished_at", "naive"]


def test_validate_and_trim() -> None:
    df = pd.DataFrame({"started_at": pd.to_datetime(["2026-02-01", "2026-02-03", "2026-02-04"], utc=True),
                       "finished_at": pd.to_datetime(["2026-02-01 01:00", "2026-02-03 01:00", "2026-02-05 00:00"], utc=True)})
    validate(df)
    assert trim_tail(df).index.tolist() == [0]
    bad = df.copy()
    bad.loc[0, "finished_at"] = pd.NaT
    with pytest.raises(ValueError, match="NaT"):
        validate(bad)
    bad.loc[0, "finished_at"] = pd.Timestamp("2026-01-31", tz="UTC")
    with pytest.raises(ValueError, match="finished_at"):
        validate(bad)
    bad.loc[0, "finished_at"] = pd.Timestamp("2026-02-03", tz="UTC")
    with pytest.warns(UserWarning, match="1 intervals longer than 24 h"):
        validate(bad)
    assert len(bad) == 3
