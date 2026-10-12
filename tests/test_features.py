import numpy as np
import pandas as pd
import pytest

from airalerts.eda import strength
from airalerts.features import AsOfFeatures, GROUP_A, GROUP_B, own_features
from airalerts.neighbors import NEIGHBORS, validate_neighbors
from airalerts.panel import build_panel


def events(rows: list[tuple]) -> pd.DataFrame:
    frame = pd.DataFrame(rows, columns=["oblast", "level", "started_at", "finished_at"])
    for column in ("started_at", "finished_at"):
        frame[column] = pd.to_datetime(frame[column], utc=True, format="mixed")
    return frame


@pytest.mark.parametrize("end", ["2026-01-03 14:00", None])
def test_ongoing_end_is_unknown(end) -> None:
    frame = events([("A", "raion", "2026-01-03 10:00", end)])
    result = own_features(frame, "A", "2026-01-03 12:00")
    assert result["active_now"] == 1
    assert result["hours_since_end"] == 0
    assert result["elapsed_in_alert"] == 2
    assert result["share_1h"] == 1
    assert result["share_6h"] == pytest.approx(2 / 6)
    assert result["starts_24h"] == 1


def test_closed_never_and_capped() -> None:
    frame = events([("A", "oblast", "2026-01-03 08:00", "2026-01-03 09:00")])
    result = own_features(frame, "A", "2026-01-03 12:00")
    assert result["hours_since_end"] == 3
    assert result["elapsed_in_alert"] == 0
    assert own_features(frame, "B", "2026-01-03 12:00")["hours_since_end"] == 168
    old = own_features(frame, "A", "2026-01-20 12:00")
    assert old["hours_since_end"] == 168
    assert own_features(frame.iloc[:0], "A", "2026-01-03 12:00")["hours_since_end"] == 168


def test_union_starts_adjacent_and_variant_b() -> None:
    frame = events([
        ("A", "raion", "2026-01-03 08:00", "2026-01-03 10:00"),
        ("A", "oblast", "2026-01-03 09:00", "2026-01-03 10:00"),
        ("A", "raion", "2026-01-03 10:00", "2026-01-03 14:00"),
        ("A", "hromada", "2026-01-01", "2026-01-05"),
    ])
    result = own_features(frame, "A", "2026-01-03 12:00")
    assert result["elapsed_in_alert"] == 4
    assert result["starts_24h"] == 1
    assert result["share_6h"] == pytest.approx(4 / 6)
    at_start = own_features(frame.iloc[[0]], "A", "2026-01-03 08:00")
    assert at_start["active_now"] == 1 and at_start["elapsed_in_alert"] == 0
    assert at_start["share_1h"] == 0 and at_start["starts_24h"] == 1


def test_future_event_perturbation() -> None:
    frame = events([
        ("A", "raion", "2026-01-03 08:00", "2026-01-03 14:00"),
        ("A", "raion", "2026-01-03 16:00", "2026-01-03 20:00"),
    ])
    t = pd.Timestamp("2026-01-03 12:00", tz="UTC")
    changed = frame.loc[frame.started_at.le(t)].copy()
    changed.loc[changed.finished_at.gt(t), "finished_at"] = pd.NaT
    assert own_features(frame, "A", t) == own_features(changed, "A", t)


def test_future_panel_flips_and_train_only_rates() -> None:
    frame = events([
        ("A", "raion", "2026-01-01 08:00", "2026-01-03 14:00"),
        ("B", "raion", "2026-01-02 10:00", "2026-01-03 13:00"),
    ])
    panel = build_panel(frame, "2026-01-01", "2026-01-05", leads=(0,),
                        day_windows=(), week_windows=(), alphas=(), oblasts=["A", "B"])
    train = panel.loc[panel["T"].lt(pd.Timestamp("2026-01-01 23:00", tz="UTC"))]
    builder = AsOfFeatures({"A": ("B",), "B": ("A",)}).fit(train, "2026-01-03")
    rng = np.random.default_rng(42)
    for t in rng.choice(panel.loc[panel["T"].ge(pd.Timestamp("2026-01-03", tz="UTC")), "T"].unique(), 5, replace=False):
        requested = panel.loc[panel["T"].eq(t), ["oblast", "T"]]
        before = builder.transform(frame, panel, requested)
        changed = panel.copy()
        future = changed["T"].gt(t)
        for column in ("state", "share_6h", "y_0"):
            values = rng.integers(0, 2, future.sum())
            changed.loc[future, column] = values.astype(bool) if column in ("state", "y_0") else values.astype(float)
        after = builder.transform(frame, changed, requested)
        pd.testing.assert_frame_equal(before, after)
        assert list(before.columns) == ["oblast", "T", *GROUP_A, *GROUP_B]
        assert before.set_index("oblast").base_rate.to_dict() == train.groupby("oblast").y_0.mean().to_dict()
    with pytest.raises(ValueError, match="outside embargoed TRAIN"):
        builder.fit(panel, "2026-01-03")


def test_neighbors() -> None:
    validate_neighbors(list(NEIGHBORS))
    assert len(NEIGHBORS) == 24
    with pytest.raises(ValueError):
        validate_neighbors(["A", "B"], {"A": ("B",), "B": ("B",)})


def test_stl_strength() -> None:
    assert strength(np.arange(5.), np.zeros(5)) == 1
    assert strength(np.zeros(5), np.arange(5.)) == 0
    assert np.isnan(strength(np.zeros(5), np.zeros(5)))
