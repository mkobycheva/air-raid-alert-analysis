import json

import numpy as np
import pandas as pd
import pytest

from airalerts.evaluate import RESULT_COLUMNS, bootstrap_bss, ece, log_result, reliability
from airalerts.models import ReferenceModel
from airalerts.panel import build_panel
from airalerts.splits import FoldParams, walk_forward_folds


def events() -> pd.DataFrame:
    frame = pd.DataFrame([
        ("A", "raion", "2026-01-01 14:40", "2026-01-01 15:10"),
        ("A", "oblast", "2026-01-01 15:00", "2026-01-01 18:00"),
        ("A", "raion", "2026-01-02 06:00", "2026-01-02 07:00"),
        ("B", "hromada", "2026-01-01 01:00", "2026-01-03 23:00"),
        ("B", "raion", "2026-01-02 05:00", "2026-01-02 08:00"),
    ], columns=["oblast", "level", "started_at", "finished_at"])
    for column in ("started_at", "finished_at"):
        frame[column] = pd.to_datetime(frame[column], utc=True)
    return frame


def panel(frame: pd.DataFrame) -> pd.DataFrame:
    return build_panel(frame, "2026-01-01", "2026-01-04", leads=(0, 1, 2, 3, 6, 24),
                       day_windows=(1,), week_windows=(1,), alphas=(.1,), oblasts=["A", "B"])


def test_future_perturbation() -> None:
    original = events()
    reference = panel(original)
    features = [column for column in reference if not column.startswith("y_")]
    rng = np.random.default_rng(42)
    times = rng.choice(reference["T"].unique(), size=8, replace=False)
    for T in times:
        changed = original.loc[original.started_at.le(T)].copy()
        changed.loc[changed.finished_at.gt(T), "finished_at"] = pd.NaT
        actual = panel(changed)
        pd.testing.assert_frame_equal(reference.loc[reference["T"].eq(T), features].reset_index(drop=True),
                                      actual.loc[actual["T"].eq(T), features].reset_index(drop=True))


def test_lead_definition_variant_and_asof_exact_share() -> None:
    frame = events().iloc[[0, 3]]
    result = panel(frame)
    row = result.loc[result.oblast.eq("A") & result["T"].eq(pd.Timestamp("2026-01-01 12:00", tz="UTC"))].iloc[0]
    assert not row.y_1 and row.y_2 and row.y_3
    assert not result.loc[result.oblast.eq("B"), "state"].any()
    row = result.loc[result.oblast.eq("A") & result["T"].eq(pd.Timestamp("2026-01-01 15:00", tz="UTC"))].iloc[0]
    assert row.state
    assert row.share_6h == pytest.approx(20 / 360)
    assert row.touch_prev_1
    assert result.loc[result["T"].eq(pd.Timestamp("2026-01-03 23:00", tz="UTC")), "y_24"].isna().all()
    overlapping = panel(events())
    row = overlapping.loc[overlapping.oblast.eq("A") & overlapping["T"].eq(pd.Timestamp("2026-01-01 16:00", tz="UTC"))].iloc[0]
    assert row.state
    assert row.hours_since_end == pytest.approx(50 / 60)  # last known close, even while another row is ongoing
    only_hromada = build_panel(events().iloc[[3]], "2026-01-01", "2026-01-02", leads=(0,),
                               day_windows=(1,), week_windows=(1,), alphas=(.1,))
    assert only_hromada.oblast.unique().tolist() == ["B"]
    assert not only_hromada.state.any() and not only_hromada.y_0.any()


def test_fold_embargo_and_test_guard() -> None:
    index = pd.date_range("2025-12-01", "2026-08-01", freq="h", inclusive="left", tz="UTC")
    rows = pd.DataFrame({"T": index})
    params = FoldParams()
    for k in (0, 1, 6, 12, 24):
        rows[f"y_{k}"] = False
        for fold, train, evaluate in walk_forward_folds(rows, params, k):
            boundary = pd.Timestamp(params.boundaries[int(fold) - 1], tz="UTC")
            assert (rows.loc[train, "T"] + pd.Timedelta(hours=k + 1)).max() <= boundary
            assert (rows.loc[evaluate, "T"] + pd.Timedelta(hours=k + 1)).max() <= pd.Timestamp(params.test_start, tz="UTC")
    with pytest.raises(ValueError, match="TEST"):
        list(walk_forward_folds(rows, FoldParams(boundaries=("2026-07-16", "2026-08-02")), 0))
    with pytest.raises(ValueError, match="TEST"):
        list(walk_forward_folds(rows, FoldParams(boundaries=("2026-07-16", "2026-08-02"), test_start="2026-08-10"), 0))


def test_results_schema_and_append(tmp_path) -> None:
    path = tmp_path / "results.csv"
    row = {column: "" for column in RESULT_COLUMNS}
    row.update(model="climatology", params_json=json.dumps({}), n=2, lead=1, scope="ALL")
    log_result(path, row)
    log_result(path, row)
    assert pd.read_csv(path).columns.tolist() == RESULT_COLUMNS
    assert len(pd.read_csv(path)) == 2
    with pytest.raises(ValueError, match="schema"):
        log_result(path, {"model": "climatology"})


def test_fit_only_train_and_calibration_bootstrap() -> None:
    train = pd.DataFrame({"oblast": ["A"] * 4, "state": [False, False, True, True],
                          "y_1": [0, 0, 1, 1], "ses_0.1": [.1, .1, .9, .9], "ses_0.6": [.5] * 4})
    clf = ReferenceModel("persistence_prob", (1,), (7,), (4,), (.1, .6)).fit(train)
    np.testing.assert_array_equal(clf.predict_proba(train, 1), [0, 0, 1, 1])
    ses = ReferenceModel("ses", (1,), (7,), (4,), (.1, .6)).fit(train)
    assert ses.params[1]["chosen"] == .1
    assert ece(np.array([0., 1.]), np.array([0., 1.])) == 0
    assert reliability(np.array([0., 1.]), np.array([0., 1.])).n.sum() == 2
    rows = pd.DataFrame({"T": pd.date_range("2026-06-01", periods=48, freq="h", tz="UTC"),
                         "y": [0., 1.] * 24, "p": [0., 1.] * 24, "clim": .5})
    assert bootstrap_bss(rows, samples=20) == (1., 1.)
