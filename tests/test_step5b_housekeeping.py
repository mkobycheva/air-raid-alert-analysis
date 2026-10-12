import csv

import pandas as pd
import pytest

from airalerts.evaluate import RESULT_COLUMNS, latest_results, log_result
from airalerts.panel import DEFAULT_LEADS
from airalerts.splits import FoldParams, walk_forward_folds


def test_shared_25h_embargo_for_every_label() -> None:
    times = pd.date_range("2025-12-01", "2026-08-01", freq="h", inclusive="left", tz="UTC")
    rows = pd.DataFrame({"T": times, **{f"y_{k}": False for k in DEFAULT_LEADS}})
    params = FoldParams()
    assert params.embargo_hours == 25
    for lead in DEFAULT_LEADS:
        for fold, train, valid in walk_forward_folds(rows, params, lead):
            start = pd.Timestamp(params.boundaries[int(fold) - 1], tz="UTC")
            assert rows.loc[train, "T"].max() < start - pd.Timedelta(hours=25)
            for k in DEFAULT_LEADS:
                end = rows.loc[train, "T"] + pd.Timedelta(hours=k + 1)
                assert end.le(start).all()
    with pytest.raises(ValueError, match="25"):
        list(walk_forward_folds(rows, FoldParams(embargo_hours=24), 0))


def test_additive_schema_preserves_legacy_rows_and_latest_scopes(tmp_path) -> None:
    path = tmp_path / "results.csv"
    old = {column: "" for column in RESULT_COLUMNS[:-1]}
    old.update(run_id="old", model="ses", fold_id="1", lead="1", scope="ALL", created_at="2026-01-01T00:00:00Z", brier="0.125")
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=RESULT_COLUMNS[:-1])
        writer.writeheader()
        writer.writerow(old)
    new = {**old, "run_id": "new", "created_at": "2026-01-02T00:00:00Z", "bss_vs_ses": "0"}
    log_result(path, new)
    log_result(path, {**new, "scope": "A"})
    with path.open(newline="") as handle:
        data = list(csv.DictReader(handle))
    assert {key: data[0][key] for key in old} == old
    assert data[0]["bss_vs_ses"] == ""
    latest = latest_results(path)
    assert latest.run_id.unique().tolist() == ["new"]
    assert set(latest.scope) == {"ALL", "A"}
