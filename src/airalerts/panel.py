"""Variant-B hourly panel: causal observations, bounded labels, local clocks."""

from pathlib import Path

import numpy as np
import pandas as pd

from airalerts.grid import episodes, time_grid, _window
from airalerts.io import official_variant

DEFAULT_LEADS = (0, 1, 2, 3, 4, 5, 6, 12, 24)


def save_frame(frame: pd.DataFrame, path: Path) -> Path:
    """Prefer parquet; offline installations without pyarrow use csv.gz."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        import pyarrow  # noqa: F401
    except ImportError:
        path = path.with_suffix(".csv.gz")
        frame.to_csv(path, index=False, compression={"method": "gzip", "mtime": 0})
    else:
        frame.to_parquet(path, index=False)
    return path


def _prefix_coverage(merged: pd.DataFrame, boundaries: pd.DatetimeIndex) -> np.ndarray:
    """Elapsed union seconds before each boundary, using existing episodes()."""
    if merged.empty:
        return np.zeros(len(boundaries))
    a = pd.DatetimeIndex(merged.started_at).as_unit("ns").asi8
    b = pd.DatetimeIndex(merged.finished_at).as_unit("ns").asi8
    t = boundaries.as_unit("ns").asi8
    pos = np.searchsorted(b, t, side="right")
    cumulative = np.r_[0., np.cumsum((b - a) / 1e9)]
    next_pos = np.minimum(pos, len(a) - 1)
    partial = np.clip((t - a[next_pos]) / 1e9, 0, (b[next_pos] - a[next_pos]) / 1e9)
    return cumulative[pos] + np.where(pos < len(a), partial, 0)


def _profile(signal: np.ndarray, index: pd.DatetimeIndex, hours: int,
             lead: int, weekly: bool) -> np.ndarray:
    local = index.tz_convert("Europe/Kyiv")
    keys = local.hour.to_numpy() + (24 * local.dayofweek.to_numpy() if weekly else 0)
    target = (index + pd.Timedelta(hours=lead)).tz_convert("Europe/Kyiv")
    wanted = target.hour.to_numpy() + (24 * target.dayofweek.to_numpy() if weekly else 0)
    result = np.zeros(len(index))
    upper = np.arange(len(index))  # exclude the current, incompletely observed hour
    lower = np.maximum(upper - hours, 0)
    for key in np.unique(wanted):
        matches = keys == key
        count = np.r_[0, np.cumsum(matches)]
        positives = np.r_[0, np.cumsum(signal * matches)]
        selected = wanted == key
        numerator = positives[upper[selected]] - positives[lower[selected]]
        denominator = count[upper[selected]] - count[lower[selected]]
        result[selected] = np.divide(numerator, denominator, out=np.zeros(len(numerator)), where=denominator > 0)
    return result


def build_panel(df: pd.DataFrame, start: str | pd.Timestamp, end: str | pd.Timestamp,
                leads: tuple[int, ...] = DEFAULT_LEADS, variant: str = "B",
                day_windows: tuple[int, ...] = (7, 14, 28), week_windows: tuple[int, ...] = (4, 8),
                alphas: tuple[float, ...] = (.01, .05, .1, .3, .6),
                history_days: int = 28, end_cap_hours: int = 72,
                excluded: tuple[str, ...] = ("Luhanska oblast", "Crimea", "Sevastopol"),
                oblasts: list[str] | None = None) -> pd.DataFrame:
    """Build [start,end) without any target hour extending beyond end.

    End is the available label boundary, not a retrospectively fitted parameter.
    Warmup covers all requested trailing windows. Missing ends extend only the
    as-of observation history, never supply future labels. Profiles/SES columns
    are fixed-candidate causal observations; models select candidates on TRAIN.
    """
    start, end = _window(start, end)
    if start != start.floor("h") or end != end.floor("h"):
        raise ValueError("Panel boundaries must be whole UTC hours")
    if any(k < 0 for k in leads) or any(n <= 0 for n in (*day_windows, *week_windows)):
        raise ValueError("Leads/windows must be nonnegative/positive")
    if any(not 0 < alpha <= 1 for alpha in alphas):
        raise ValueError("SES alpha must lie in (0,1]")
    selected = official_variant(df, variant)
    selected = selected.loc[~selected.oblast.isin(excluded)].copy()
    # Geography is independent of the chosen level definition: a region with
    # only excluded hromada rows still has a zero variant-B state.
    oblasts = sorted(b for b in (oblasts if oblasts is not None else df.oblast.unique()) if b not in excluded)
    selected = selected.loc[selected.started_at.lt(end)].copy()
    warmup = max(history_days, max(day_windows, default=0), 7 * max(week_windows, default=0))
    context = start - pd.Timedelta(days=warmup)
    index = pd.date_range(context, end, freq="h", inclusive="left")
    observed = selected.copy()
    observed["finished_at"] = observed.finished_at.fillna(end).clip(upper=end)
    observed = observed.drop(columns="is_open", errors="ignore")
    touch = time_grid(observed, context, end).reindex(columns=oblasts, fill_value=False)
    truth = time_grid(selected.loc[selected.finished_at.notna()], context, end).reindex(columns=oblasts, fill_value=False)
    frames = []
    for oblast in oblasts:
        rows = observed.loc[observed.oblast.eq(oblast)]
        changes = np.zeros(len(index) + 1, dtype=int)
        good = rows.finished_at.gt(rows.started_at)
        left = index.searchsorted(rows.loc[good, "started_at"], side="left")
        right = index.searchsorted(rows.loc[good, "finished_at"], side="left")
        np.add.at(changes, left, 1)
        np.add.at(changes, right, -1)
        state = np.cumsum(changes[:-1]) > 0
        frame = pd.DataFrame({"oblast": oblast, "T": index, "state": state})
        signal = touch[oblast].to_numpy(dtype=float)
        for lag in range(1, 7):
            frame[f"touch_prev_{lag}"] = np.r_[np.zeros(lag), signal[:-lag]].astype(bool)
        cumulative = _prefix_coverage(episodes(observed, oblast, context, end), index)
        for hours in (6, 24, 168, history_days * 24):
            low = np.maximum(np.arange(len(index)) - hours, 0)
            frame[f"share_{hours}h"] = (cumulative - cumulative[low]) / (hours * 3600)
        finishes = pd.DatetimeIndex(selected.loc[selected.oblast.eq(oblast), "finished_at"].dropna().sort_values())
        positions = finishes.searchsorted(index, side="right") - 1
        elapsed = np.full(len(index), float(end_cap_hours))
        good_pos = positions >= 0
        elapsed[good_pos] = (index[good_pos] - finishes.take(positions[good_pos])).total_seconds() / 3600
        frame["hours_since_end"] = np.clip(elapsed, 0, end_cap_hours)
        local = index.tz_convert("Europe/Kyiv")
        for name, values, period in [("hour", local.hour, 24), ("weekday", local.dayofweek, 7)]:
            frame[name + "_sin"] = np.sin(2 * np.pi * values / period)
            frame[name + "_cos"] = np.cos(2 * np.pi * values / period)
        for alpha in alphas:
            frame[f"ses_{alpha:g}"] = pd.Series(signal).ewm(alpha=alpha, adjust=False).mean().shift(1).fillna(0).to_numpy()
        for k in leads:
            y = truth[oblast].shift(-k).astype("boolean")
            unknown = selected.loc[selected.oblast.eq(oblast) & selected.finished_at.isna(), "started_at"]
            if not unknown.empty:
                # Unclosed input has no settled target truth. Conservatively
                # withhold labels from its first affected hour onwards.
                y = y.mask(index + pd.Timedelta(hours=k) >= unknown.min().floor("h"))
            frame[f"y_{k}"] = y.to_numpy()
            for n in day_windows:
                frame[f"day_{n}_k{k}"] = _profile(signal, index, n * 24, k, False)
            for m in week_windows:
                frame[f"week_{m}_k{k}"] = _profile(signal, index, m * 168, k, True)
        frames.append(frame.loc[frame["T"].ge(start)])
    panel = pd.concat(frames, ignore_index=True).sort_values(["T", "oblast"]).reset_index(drop=True)
    panel["nationwide_state"] = panel.groupby("T").state.transform("sum").astype(int)
    for k in leads:
        panel[f"y_{k}"] = panel[f"y_{k}"].astype("boolean")
    return panel
