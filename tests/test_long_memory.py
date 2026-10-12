import numpy as np
import pandas as pd
import pytest

from airalerts.features import GROUP_L, observed_features, own_features
from airalerts.panel import build_panel


def test_long_memory_and_future_perturbation():
    events = pd.DataFrame([
        ("A", "raion", "2026-01-01 00:00", "2026-01-02 01:00"),
        ("A", "raion", "2026-01-03 00:00", "2026-01-04 01:00"),
        ("B", "raion", "2026-01-02 12:30", "2026-01-02 13:20"),
    ], columns=["oblast", "level", "started_at", "finished_at"])
    for col in ("started_at", "finished_at"):
        events[col] = pd.to_datetime(events[col], utc=True)
    panel = build_panel(events, "2026-01-01", "2026-01-05", leads=(0,), day_windows=(), week_windows=(), alphas=(), oblasts=["A", "B"])
    adjacent = {"A": ("B",), "B": ("A",)}
    fast = observed_features(events, panel, adjacent, include_long_memory=True)
    rng = np.random.default_rng(42)
    for t in rng.choice(panel["T"].unique(), 5, replace=False):
        changed = events.loc[events.started_at.le(t)].copy()
        changed.loc[changed.finished_at.gt(t), "finished_at"] = pd.NaT
        altered = panel.copy()
        altered.loc[altered["T"].gt(t), "state"] = rng.integers(0, 2, altered["T"].gt(t).sum()).astype(bool)
        result = observed_features(changed, altered, adjacent, include_long_memory=True)
        pd.testing.assert_frame_equal(fast.loc[fast["T"].eq(t)].reset_index(drop=True), result.loc[result["T"].eq(t)].reset_index(drop=True))
        for oblast in ("A", "B"):
            own = own_features(events, oblast, t, include_long_memory=True)
            masked = own_features(changed, oblast, t, include_long_memory=True)
            for name in GROUP_L:
                assert own[name] == pytest.approx(masked[name])
                assert fast.loc[fast.oblast.eq(oblast) & fast["T"].eq(t), name].iloc[0] == pytest.approx(own[name])
    row = fast.loc[fast.oblast.eq("A") & fast["T"].eq(pd.Timestamp("2026-01-01 01:00", tz="UTC"))].iloc[0]
    assert row.share_672h == pytest.approx(1 / 672)
    assert row.ewma_14d == pytest.approx(1 - 2 ** (-1 / 336))
    zero = fast.loc[fast.oblast.eq("A") & fast["T"].eq(pd.Timestamp("2026-01-01", tz="UTC"))].iloc[0]
    assert zero.ewma_14d == 0
