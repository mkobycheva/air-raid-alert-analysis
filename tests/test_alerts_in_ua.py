from datetime import datetime, timezone

import pandas as pd
import pytest

from airalerts.collect.alerts_in_ua import NORMALISED_COLUMNS, normalise, resolve_oblast
from airalerts.grid import exact_share, time_grid
from airalerts.io import load_alerts_in_ua, valid_end

FETCHED = datetime(2026, 10, 11, tzinfo=timezone.utc)


def alert(alert_id: int = 1, **changes) -> dict:
    return {"id": alert_id, "location_oblast_uid": 27, "location_type": "raion",
            "location_oblast": "Львівська область", "alert_type": "air_raid",
            "started_at": "2026-10-01T14:00:00Z", "finished_at": "2026-10-01T15:00:00Z", **changes}


def test_open_missing_level_and_mixed_precision() -> None:
    frame = normalise({27: {"alerts": [alert(finished_at=None), alert(2, started_at="2026-10-01T14:00:00.123Z")]}}, FETCHED)
    assert frame.is_open.tolist() == [True, False]
    assert pd.isna(frame.finished_at.iloc[0])
    assert frame.alert_level.isna().all()
    assert str(frame.fetched_at.dt.tz) == "UTC"


def test_duplicate_id_across_queries_and_bare_list() -> None:
    frame = normalise({27: [alert()], 8: {"alerts": [alert()]}}, FETCHED)
    assert len(frame) == 1
    assert frame.queried_uid.iloc[0] == 8


def test_latest_duplicate_observation_and_null_threat_type() -> None:
    frame = normalise({27: [alert(finished_at=None)],
                       8: [alert(threats=[{"threat_type": None}, {"threat_type": "uav"}])]}, FETCHED)
    assert len(frame) == 1
    assert not frame.is_open.iloc[0]
    assert frame.threat_types.iloc[0] == "uav"


@pytest.mark.parametrize("payloads", [{}, {27: []}, {27: {"alerts": []}}, {27: {"alerts": None}}, {27: None}])
def test_empty_payload_has_schema(payloads: dict) -> None:
    frame = normalise(payloads, FETCHED)
    assert frame.empty
    assert frame.columns.tolist() == NORMALISED_COLUMNS


def test_missing_id_or_invalid_start_rejected() -> None:
    with pytest.raises(ValueError, match="missing id"):
        normalise({27: [alert(None)]}, FETCHED)
    with pytest.raises(ValueError):
        normalise({27: [alert(started_at=None)]}, FETCHED)


def test_loader_filters_and_open_math(tmp_path) -> None:
    records = [alert(alert_level="red"), alert(2, finished_at=None, alert_level="red"),
               alert(3, alert_level="yellow"), alert(4, alert_type="artillery_shelling", alert_level="red")]
    path = tmp_path / "api.csv"
    normalise({27: records}, FETCHED).to_csv(path, index=False)
    frame = load_alerts_in_ua(path)
    assert len(frame) == 3
    assert frame.oblast.unique().tolist() == ["Lvivska oblast"]
    assert frame.level.unique().tolist() == ["raion"]
    assert frame.is_open.sum() == 1
    assert len(load_alerts_in_ua(path, variant="red")) == 2
    assert len(load_alerts_in_ua(path, air_raid_only=False)) == 4
    assert exact_share(frame, "Lvivska oblast", "2026-10-01 14:00", "2026-10-01 16:00") == .5
    assert time_grid(frame, "2026-10-01 14:00", "2026-10-01 16:00")["Lvivska oblast"].tolist() == [True, False]


def test_real_schema_uid_fallback_and_fetched_cutoff(tmp_path) -> None:
    path = tmp_path / "api.csv"
    normalise({8: [alert(location_oblast_uid=41, location_oblast="Волинська область")]}, FETCHED).to_csv(path, index=False)
    frame = load_alerts_in_ua(path)
    assert frame.oblast.iloc[0] == "Volynska oblast"
    assert frame.oblast_resolution.iloc[0] == "location_oblast_name_fallback"
    frame["fetched_at"] = pd.Timestamp("2026-09-30", tz="UTC")
    assert valid_end(frame) == pd.Timestamp("2026-09-28", tz="UTC")


def test_uid_fallback_does_not_mislabel_a_district() -> None:
    assert resolve_oblast(14, queried_uid=8, title=None) == ("Volynska oblast", "queried_uid_fallback")
    with pytest.raises(ValueError, match="disagrees"):
        resolve_oblast(41, queried_uid=27, title="Волинська область")
