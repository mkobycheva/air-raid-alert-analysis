"""UTC interval coverage; callers select sources and exclude unwanted oblasts."""

import numpy as np
import pandas as pd


def _window(start: str | pd.Timestamp, end: str | pd.Timestamp
            ) -> tuple[pd.Timestamp, pd.Timestamp]:
    start, end = pd.Timestamp(start), pd.Timestamp(end)
    start = start.tz_localize("UTC") if start.tzinfo is None else start.tz_convert("UTC")
    end = end.tz_localize("UTC") if end.tzinfo is None else end.tz_convert("UTC")
    if pd.isna(start) or pd.isna(end) or end <= start:
        raise ValueError("Window must have valid timestamps with end > start")
    return start, end


def _clipped(df: pd.DataFrame, start: pd.Timestamp,
             end: pd.Timestamp) -> pd.DataFrame:
    rows = df.loc[df["started_at"].lt(end) & df["finished_at"].gt(start),
                  ["oblast", "started_at", "finished_at"]].copy()
    if "is_open" in df:
        rows = rows.loc[~df.loc[rows.index, "is_open"].fillna(False)]
    rows["started_at"] = rows["started_at"].clip(lower=start)
    rows["finished_at"] = rows["finished_at"].clip(upper=end)
    return rows.loc[rows["finished_at"].gt(rows["started_at"])]


def hourly_grid(df: pd.DataFrame, start: str | pd.Timestamp,
                end: str | pd.Timestamp) -> pd.DataFrame:
    """Compatibility wrapper for hour-aligned time_grid(..., freq='60min')."""
    start, end = _window(start, end)
    if start != start.floor("h"):
        raise ValueError("Hourly grid start must be hour-aligned")
    return time_grid(df, start, end)


def time_grid(df: pd.DataFrame, start: str | pd.Timestamp,
              end: str | pd.Timestamp, freq: str = "60min") -> pd.DataFrame:
    """OR positive closed intervals touching bins in [start, end), in UTC.

    Bins are anchored at start. Partial final bins are clipped to end. Open and
    empty intervals cover no time. All input oblasts remain as columns.
    """
    start, end = _window(start, end)
    step = pd.Timedelta(freq)
    if step <= pd.Timedelta(0):
        raise ValueError("freq must be a positive fixed duration")
    index = pd.date_range(start, end, freq=step, inclusive="left", name="hour")
    columns = pd.Index(sorted(df["oblast"].dropna().unique()), name="oblast")
    result = pd.DataFrame(False, index=index, columns=columns)
    for oblast, rows in _clipped(df, start, end).groupby("oblast"):
        left = index.searchsorted(rows["started_at"], side="right") - 1
        right = index.searchsorted(rows["finished_at"], side="left")
        changes = np.zeros(len(index) + 1, dtype=np.int64)
        np.add.at(changes, left, 1)
        np.add.at(changes, right, -1)
        result[oblast] = np.cumsum(changes[:-1]) > 0
    return result


def episodes(df: pd.DataFrame, oblast: str, start: str | pd.Timestamp,
             end: str | pd.Timestamp) -> pd.DataFrame:
    """Merge strictly overlapping closed intervals, clipping to the window.

    Abutting half-open intervals remain separate episodes (no overlap).
    """
    start, end = _window(start, end)
    rows = _clipped(df.loc[df["oblast"].eq(oblast)], start, end).sort_values("started_at")
    merged: list[tuple[pd.Timestamp, pd.Timestamp]] = []
    for a, b in rows[["started_at", "finished_at"]].itertuples(index=False, name=None):
        if merged and a < merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], b))
        else:
            merged.append((a, b))
    result = pd.DataFrame(merged, columns=["started_at", "finished_at"])
    for column in result:
        result[column] = pd.to_datetime(result[column], utc=True)
    return result


def exact_share(df: pd.DataFrame, oblast: str | pd.Timestamp | None = None,
                start: str | pd.Timestamp | None = None,
                end: str | pd.Timestamp | None = None) -> pd.Series | float:
    """Fraction of window covered by each oblast's interval union.

    Use exact elapsed time, including sub-minute precision, without rounding
    or double-counting overlaps. Preserve oblasts with zero coverage.

    Also supports the existing exact_share(df, start, end) Series interface.
    """
    if end is None:
        oblast, start, end = None, oblast, start
    start, end = _window(start, end)
    if oblast is not None:
        merged = episodes(df, str(oblast), start, end)
        return float((merged["finished_at"] - merged["started_at"]).sum() / (end - start))
    result = pd.Series(0.0, index=pd.Index(sorted(df["oblast"].dropna().unique()),
                                        name="oblast"), name="exact_share")
    for oblast, rows in _clipped(df, start, end).groupby("oblast"):
        covered = pd.Timedelta(0)
        union_start, union_end = None, None
        for a, b in rows.sort_values("started_at")[["started_at", "finished_at"]].itertuples(index=False, name=None):
            if union_end is None or a > union_end:
                if union_end is not None:
                    covered += union_end - union_start
                union_start, union_end = a, b
            else:
                union_end = max(union_end, b)
        if union_end is not None:
            covered += union_end - union_start
        result.loc[oblast] = covered / (end - start)
    return result
