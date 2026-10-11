"""Read source intervals without merging sources or filtering oblasts."""

from pathlib import Path
import warnings

import pandas as pd


def _parse_times(df: pd.DataFrame) -> pd.DataFrame:
    for column in ("started_at", "finished_at"):
        df[column] = pd.to_datetime(df[column], utc=True, format="ISO8601", errors="coerce")
    validate(df)
    return df


def load_official(path: str | Path) -> pd.DataFrame:
    """Drop exact raw duplicates, then derive duration from UTC timestamps."""
    df = pd.read_csv(path).drop_duplicates()
    df = _parse_times(df)
    df["duration_s"] = (df["finished_at"] - df["started_at"]).dt.total_seconds()
    df["naive_guess"] = df["duration_s"].eq(3600)
    return df[["oblast", "raion", "hromada", "level", "started_at",
               "finished_at", "duration_s", "naive_guess"]].reset_index(drop=True)


def load_volunteer(path: str | Path) -> pd.DataFrame:
    """Read volunteer intervals, preserving its supplied imputation flag."""
    df = pd.read_csv(path).rename(columns={"region": "oblast"})
    df = _parse_times(df)
    return df[["oblast", "started_at", "finished_at", "naive"]]


def validate(df: pd.DataFrame) -> None:
    """Reject missing/invalid times; warn about, but retain, spans over 24 h."""
    if df[["started_at", "finished_at"]].isna().any().any():
        raise ValueError("Intervals contain NaT timestamps")
    durations = df["finished_at"] - df["started_at"]
    if durations.lt(pd.Timedelta(0)).any():
        raise ValueError("Intervals have finished_at < started_at")
    count = int(durations.gt(pd.Timedelta(hours=24)).sum())
    if count:
        warnings.warn(f"{count} intervals longer than 24 h (retained)",
                      UserWarning, stacklevel=2)


def valid_end(df: pd.DataFrame, hours: float = 48) -> pd.Timestamp:
    """max(started_at) - hours, bounded by API max(fetched_at) when supplied.

    Compute on the full source, before region/definition/imputation exclusions.
    Comparisons clip retained intervals at this endpoint; no end is imputed.
    """
    if hours < 0:
        raise ValueError("hours must be nonnegative")
    source_end = df["started_at"].max()
    if "fetched_at" in df and df["fetched_at"].notna().any():
        source_end = min(source_end, df["fetched_at"].max())
    return source_end - pd.Timedelta(hours=hours)


def trim_tail(df: pd.DataFrame, hours: float = 48) -> pd.DataFrame:
    """Keep starts strictly before valid_end, defined from max(started_at)."""
    cutoff = valid_end(df, hours)
    return df.loc[df["started_at"].lt(cutoff)].copy()


def official_variant(df: pd.DataFrame, variant: str) -> pd.DataFrame:
    """A all; B oblast+raion; C duration <=24 h; D both B and C."""
    if variant not in {"A", "B", "C", "D"}:
        raise ValueError("official variant must be A, B, C or D")
    keep = pd.Series(True, index=df.index)
    if variant in {"B", "D"}:
        keep &= df["level"].isin(["oblast", "raion"])
    if variant in {"C", "D"}:
        keep &= (df["finished_at"] - df["started_at"]).le(pd.Timedelta(hours=24))
    return df.loc[keep].copy()


def load_alerts_in_ua(path: str | Path, air_raid_only: bool = True,
                      variant: str = "all") -> pd.DataFrame:
    """Load API rows, retaining opens and metadata for separate reporting.

    English names share the collector's resolver. Malformed closed timestamps
    raise; genuinely null ends remain NaT and are ignored by interval maths.
    The raw UID is preserved alongside oblast_resolution for auditing fallbacks.
    """
    from airalerts.collect.alerts_in_ua import resolve_oblast

    if variant not in {"all", "red"}:
        raise ValueError("API variant must be all or red")
    df = pd.read_csv(path)
    for column in ("started_at", "finished_at", "fetched_at"):
        if column in df:
            df[column] = pd.to_datetime(df[column], utc=True, format="ISO8601", errors="raise")
    if df["started_at"].isna().any():
        raise ValueError("API intervals contain NaT started_at")
    df["is_open"] = df["finished_at"].isna()
    validate(df.loc[~df["is_open"]])
    resolved = [resolve_oblast(row.get("location_oblast_uid"), row.get("queried_uid"), row.get("oblast"))
                for row in df.to_dict(orient="records")]
    df["oblast"] = [name for name, _ in resolved]
    df["oblast_resolution"] = [method for _, method in resolved]
    df["level"] = df["location_type"]
    for column in ("alert_level", "threat_types"):
        if column not in df:
            df[column] = ""
        df[column] = df[column].fillna("")
    if air_raid_only:
        df = df.loc[df["alert_type"].eq("air_raid")]
    if variant == "red":
        df = df.loc[df["alert_level"].eq("red")]
    return df.reset_index(drop=True)
