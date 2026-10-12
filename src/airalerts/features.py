"""Group A/B observations at T; fitted rates use only the fold's TRAIN.

No calendar fields, STL components or future labels enter transform().
"""

import pandas as pd
import numpy as np

from airalerts.grid import episodes, exact_share, time_grid
from airalerts.io import official_variant
from airalerts.neighbors import NEIGHBORS, validate_neighbors
from airalerts.panel import _prefix_coverage

GROUP_A = ("active_now", "hours_since_end", "elapsed_in_alert",
           "share_1h", "share_6h", "share_24h", "share_168h", "starts_24h")
GROUP_B = ("base_rate", "neighbor_share_now", "neighbor_share_6h", "national_active_count")
GROUP_L = ("share_672h", "ewma_14d")
EWMA_START = pd.Timestamp("2022-03-15", tz="UTC")


def hourly_ewma(rows: pd.DataFrame, oblast: str, times: pd.DatetimeIndex) -> np.ndarray:
    """Fixed zero initialization; completed-hour touch bits, 336-hour half-life."""
    if times.min() < EWMA_START or any(times != times.floor("h")):
        raise ValueError("EWMA times must be whole hours since 2022-03-15 UTC")
    end = times.max()
    if end == EWMA_START:
        return np.zeros(len(times))
    signal = time_grid(rows.loc[rows.oblast.eq(oblast)], EWMA_START, end).reindex(columns=[oblast], fill_value=False)[oblast]
    values = pd.Series(np.r_[0., signal.to_numpy(dtype=float)]).ewm(halflife=14 * 24, adjust=False).mean().to_numpy()
    boundaries = pd.date_range(EWMA_START, end, freq="h")
    return pd.Series(values, index=boundaries).reindex(times).to_numpy()


def observed_features(events: pd.DataFrame, panel: pd.DataFrame,
                      neighbors: dict[str, tuple[str, ...]] | None = None,
                      include_long_memory: bool = False,
                      final_test: bool = False) -> pd.DataFrame:
    """Vectorized equivalent of own_features over the existing bounded panel.

    Merging full intervals is safe here: coverage/starts at or before T and the
    start of its ongoing episode are unchanged by any strictly future event.
    No future end value is exposed: only whether the interval is ongoing at T.
    Includes unfitted context; base_rate is added separately on each fold TRAIN.
    """
    neighbors = NEIGHBORS if neighbors is None else neighbors
    validate_neighbors(panel.oblast.unique().tolist(), neighbors)
    if panel.empty or (not final_test and panel["T"].ge(pd.Timestamp("2026-08-01", tz="UTC")).any()):
        raise ValueError("Require nonempty panel wholly before reserved TEST")
    end = panel["T"].max() + pd.Timedelta(hours=1)
    rows = official_variant(events, "B")
    rows = rows.loc[rows.started_at.lt(end)].drop(columns="is_open", errors="ignore").copy()
    rows["finished_at"] = rows.finished_at.fillna(end).clip(upper=end)
    pieces = []
    for oblast, group in panel.groupby("oblast", sort=True):
        group = group.sort_values("T")
        times = pd.DatetimeIndex(group["T"])
        regional = rows.loc[rows.oblast.eq(oblast)]
        low = min(regional.started_at.min(), times.min() - pd.Timedelta(hours=168)) if len(regional) else times.min() - pd.Timedelta(hours=168)
        union = episodes(regional, oblast, low, end, merge_adjacent=True)
        starts = pd.DatetimeIndex(union.started_at)
        finishes = pd.DatetimeIndex(union.finished_at)
        position = starts.searchsorted(times, side="right") - 1
        known = position >= 0
        active = np.zeros(len(times), dtype=bool)
        elapsed = np.zeros(len(times))
        since = np.full(len(times), 168.)
        if known.any():
            active[known] = finishes.take(position[known]) > times[known]
            elapsed[active] = (times[active] - starts.take(position[active])).total_seconds() / 3600
            closed = known & ~active
            since[closed] = np.minimum(168, (times[closed] - finishes.take(position[closed])).total_seconds() / 3600)
        since[active] = 0
        values = pd.DataFrame({"oblast": oblast, "T": times, "active_now": active.astype(float),
                               "hours_since_end": since, "elapsed_in_alert": elapsed,
                               "starts_24h": starts.searchsorted(times, side="right") - starts.searchsorted(times - pd.Timedelta(hours=24), side="right")})
        high = _prefix_coverage(union, times)
        for hours in ((1, 6, 24, 168, 672) if include_long_memory else (1, 6, 24, 168)):
            values[f"share_{hours}h"] = (high - _prefix_coverage(union, times - pd.Timedelta(hours=hours))) / (hours * 3600)
        if include_long_memory:
            values["ewma_14d"] = hourly_ewma(regional, oblast, times)
        pieces.append(values)
    result = pd.concat(pieces, ignore_index=True)
    state = result.pivot(index="T", columns="oblast", values="active_now")
    share = result.pivot(index="T", columns="oblast", values="share_6h")
    if state.isna().any().any():
        raise ValueError("Require complete panel geography at every T")
    for oblast, adjacent in neighbors.items():
        chosen = result.oblast.eq(oblast)
        times = result.loc[chosen, "T"]
        result.loc[chosen, "neighbor_share_now"] = state.loc[times, list(adjacent)].mean(axis=1).to_numpy()
        result.loc[chosen, "neighbor_share_6h"] = share.loc[times, list(adjacent)].mean(axis=1).to_numpy()
        result.loc[chosen, "national_active_count"] = state.loc[times].sum(axis=1).to_numpy()
    return result.sort_values(["T", "oblast"]).reset_index(drop=True)


def own_features(events: pd.DataFrame, oblast: str, T: str | pd.Timestamp,
                 cap_hours: int = 168, include_long_memory: bool = False) -> dict[str, float]:
    """Exact union exposure; starts count transitions into an oblast alert.

    Starts use (T-24h,T], rather than counting simultaneous raion starts.
    Unknown/future ends are replaced only internally by T+1 second. Abutting
    intervals are one continuous state, preserving elapsed time at T.
    """
    t = pd.Timestamp(T)
    t = t.tz_localize("UTC") if t.tzinfo is None else t.tz_convert("UTC")
    if pd.isna(t) or t != t.floor("h") or cap_hours <= 0:
        raise ValueError("T must be a whole UTC hour and cap_hours positive")
    rows = official_variant(events, "B")
    rows = rows.loc[rows.oblast.eq(oblast) & rows.started_at.le(t)].copy()
    unknown = rows.finished_at.isna() | rows.finished_at.gt(t)
    rows.loc[unknown, "finished_at"] = t + pd.Timedelta(seconds=1)
    rows = rows.drop(columns="is_open", errors="ignore")
    rows = rows.loc[rows.finished_at.gt(rows.started_at)]
    active = bool(rows.finished_at.gt(t).any())
    low = min(rows.started_at.min(), t - pd.Timedelta(hours=168)) if len(rows) else t - pd.Timedelta(hours=168)
    union = episodes(rows, oblast, low, t + pd.Timedelta(seconds=1), merge_adjacent=True)
    current = union.loc[union.finished_at.gt(t)]
    elapsed = (t - current.started_at.iloc[-1]).total_seconds() / 3600 if active else 0.
    closed = union.loc[union.finished_at.le(t)]
    since = 0. if active else min(cap_hours, (t - closed.finished_at.max()).total_seconds() / 3600) if len(closed) else float(cap_hours)
    result = {"active_now": float(active), "hours_since_end": float(since),
              "elapsed_in_alert": elapsed,
              "starts_24h": float((union.started_at.gt(t - pd.Timedelta(hours=24)) & union.started_at.le(t)).sum())}
    for hours in ((1, 6, 24, 168, 672) if include_long_memory else (1, 6, 24, 168)):
        result[f"share_{hours}h"] = exact_share(rows, oblast, t - pd.Timedelta(hours=hours), t)
    if include_long_memory:
        result["ewma_14d"] = float(hourly_ewma(rows, oblast, pd.DatetimeIndex([t]))[0])
    return result


class AsOfFeatures:
    """Freeze TRAIN rates, then derive current context from causal panel rows.

    Panel state/share_6h must come from build_panel's as-of observations.
    Transform accesses panel rows at T only, and events started no later than T.
    """

    def __init__(self, neighbors: dict[str, tuple[str, ...]] | None = None) -> None:
        self.neighbors = NEIGHBORS if neighbors is None else neighbors
        self.base_rates: pd.Series | None = None

    def fit(self, train: pd.DataFrame, valid_start: str | pd.Timestamp,
            embargo_hours: int = 25) -> "AsOfFeatures":
        boundary = pd.Timestamp(valid_start)
        boundary = boundary.tz_localize("UTC") if boundary.tzinfo is None else boundary.tz_convert("UTC")
        if embargo_hours < 25 or train.empty:
            raise ValueError("Require nonempty TRAIN and >=25-hour embargo")
        if train["T"].ge(boundary - pd.Timedelta(hours=embargo_hours)).any():
            raise ValueError("Rate fitting includes rows outside embargoed TRAIN")
        if train.y_0.isna().any():
            raise ValueError("TRAIN base rates require known y_0")
        validate_neighbors(train.oblast.unique().tolist(), self.neighbors)
        self.base_rates = train.groupby("oblast").y_0.mean()
        return self

    def transform(self, events: pd.DataFrame, panel: pd.DataFrame,
                  rows: pd.DataFrame) -> pd.DataFrame:
        if self.base_rates is None:
            raise ValueError("Fit on TRAIN before transforming")
        required = set(self.neighbors)
        output = []
        for t, requested in rows.groupby("T", sort=True):
            context = panel.loc[panel["T"].eq(t)].set_index("oblast")
            if context.index.has_duplicates or set(context.index) != required:
                raise ValueError("Each T needs exactly one causal panel row per oblast")
            national = float(context.state.sum())
            for oblast in requested.oblast:
                if oblast not in required:
                    raise ValueError("Requested oblast is outside fitted geography")
                values = own_features(events, oblast, t)
                adjacent = list(self.neighbors[oblast])
                values.update(base_rate=float(self.base_rates.loc[oblast]),
                              neighbor_share_now=float(context.loc[adjacent, "state"].mean()),
                              neighbor_share_6h=float(context.loc[adjacent, "share_6h"].mean()),
                              national_active_count=national)
                output.append({"oblast": oblast, "T": t, **values})
        return pd.DataFrame(output, columns=["oblast", "T", *GROUP_A, *GROUP_B])
