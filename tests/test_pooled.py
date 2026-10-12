import numpy as np
import pandas as pd
import pytest

from airalerts.features import GROUP_A, GROUP_B, observed_features, own_features
from airalerts.panel import build_panel
from airalerts.pooled import PooledLogistic, fold_data, recency_weights
from airalerts.splits import FoldParams


def sample():
    rows = pd.DataFrame([
        ("A", "raion", "2026-01-01 03:10", "2026-01-02 08:00"),
        ("A", "oblast", "2026-01-02 08:00", "2026-01-03 07:20"),
        ("A", "hromada", "2026-01-01", "2026-01-05"),
        ("B", "raion", "2026-01-02 01:00", "2026-01-02 03:00"),
        ("B", "raion", "2026-01-03 14:00", "2026-01-04 14:00"),
    ], columns=["oblast", "level", "started_at", "finished_at"])
    for col in ["started_at", "finished_at"]:
        rows[col] = pd.to_datetime(rows[col], utc=True, format="mixed")
    panel = build_panel(rows, "2026-01-01", "2026-01-05", leads=(0, 1, 24),
                        day_windows=(), week_windows=(), alphas=(.01, .05, .1, .3, .6), oblasts=["A", "B"])
    return rows, panel


def test_exact_feature_schema_and_vectorized_future_invariance():
    assert GROUP_A == ("active_now", "hours_since_end", "elapsed_in_alert", "share_1h", "share_6h", "share_24h", "share_168h", "starts_24h")
    assert GROUP_B == ("base_rate", "neighbor_share_now", "neighbor_share_6h", "national_active_count")
    events, panel = sample()
    adjacency = {"A": ("B",), "B": ("A",)}
    fast = observed_features(events, panel, adjacency)
    rng = np.random.default_rng(42)
    for t in rng.choice(panel["T"].unique(), 10, replace=False):
        before = fast.loc[fast["T"].eq(t)].reset_index(drop=True)
        changed = events.loc[events.started_at.le(t)].copy()
        changed.loc[changed.finished_at.gt(t), "finished_at"] = pd.NaT
        perturbed = panel.copy()
        future = perturbed["T"].gt(t)
        perturbed.loc[future, "state"] = rng.integers(0, 2, future.sum()).astype(bool)
        perturbed.loc[future, "share_6h"] = rng.random(future.sum())
        after = observed_features(changed, perturbed, adjacency)
        pd.testing.assert_frame_equal(before, after.loc[after["T"].eq(t)].reset_index(drop=True))
        for oblast in ("A", "B"):
            expected = own_features(events, oblast, t)
            assert set(expected) == set(GROUP_A)
            for name in GROUP_A:
                assert before.set_index("oblast").loc[oblast, name] == pytest.approx(expected[name])


def test_fold_rates_and_embargo():
    events, panel = sample()
    observed = observed_features(events, panel, {"A": ("B",), "B": ("A",)})
    params = FoldParams("2026-01-01", ("2026-01-03", "2026-01-05"))
    for k in (0, 1, 24):
        fold = next(fold_data(panel, observed, params, k, GROUP_A + GROUP_B))
        assert fold.train["T"].max() < pd.Timestamp("2026-01-03", tz="UTC") - pd.Timedelta(hours=25)
        assert (fold.train["T"] + pd.Timedelta(hours=k+1)).max() <= fold.valid["T"].min()
        expected = fold.train.groupby("oblast").y_0.mean()
        assert np.allclose(fold.valid.base_rate, fold.valid.oblast.map(expected))
    with pytest.raises(ValueError, match="Only specified"):
        next(fold_data(panel, observed, params, 0, ("oblast",)))


def test_recency_weights():
    frame = pd.DataFrame({"T": pd.to_datetime(["2026-01-01", "2026-01-15"], utc=True)})
    end = pd.Timestamp("2026-01-29", tz="UTC")
    assert recency_weights(frame, end, 14).tolist() == [.25, .5]
    assert recency_weights(frame, end, np.inf).tolist() == [1, 1]


def test_logistic_fits_scaler_on_train_only():
    pytest.importorskip("sklearn", reason="Offline Python 3.14 lacks sklearn; model test runs on Python 3.12")
    frame = pd.DataFrame({"active_now": [0., 0., 1., 1.], "hours_since_end": [8., 4., 0., 0.], "y": [0, 1, 0, 1]})
    columns = ("active_now", "hours_since_end")
    model = PooledLogistic(columns, .1).fit(frame)
    np.testing.assert_allclose(model.scaler.mean_, frame[list(columns)].mean())
    test = frame.copy()
    test["hours_since_end"] = 1000.
    original = model.scaler.mean_.copy()
    p = model.predict_proba(test, 1)
    assert np.all((p >= 0) & (p <= 1))
    np.testing.assert_array_equal(original, model.scaler.mean_)


def test_validation_guard_and_label_loading(tmp_path):
    from airalerts.ladder import read_panel
    path = tmp_path / "panel.csv"
    pd.DataFrame({"oblast": ["A"], "T": ["2026-08-01T00:00:00Z"], "y_0": [True]}).to_csv(path, index=False)
    with pytest.raises(ValueError, match="reserved TEST"):
        read_panel(path)
    pd.DataFrame({"oblast": ["A", "A"], "T": ["2026-07-01T00:00:00Z", "2026-07-01T01:00:00Z"],
                  "y_0": [True, False]}).to_csv(path, index=False)
    assert read_panel(path).y_0.tolist() == [True, False]


def test_candidate_selection_uses_pooled_validation():
    pytest.importorskip("sklearn", reason="Offline sklearn execution runs on Python 3.12")
    from airalerts.ladder import select_grid
    events, panel = sample()
    observed = observed_features(events, panel, {"A": ("B",), "B": ("A",)})
    params = FoldParams("2026-01-01", ("2026-01-03", "2026-01-04", "2026-01-05"))
    folds = list(fold_data(panel, observed, params, 1, GROUP_A))
    chosen, pred, candidates = select_grid(folds, GROUP_A, [.1, 1], np.inf, params, 42)
    losses = {C: sum(r["n"] * r["brier"] for r in candidates if r["C"] == C) / sum(r["n"] for r in candidates if r["C"] == C) for C in [.1, 1]}
    assert chosen == min(losses, key=lambda C: (losses[C], C))
    assert pred.fold_id.nunique() == 2
    assert len(candidates) == 4
