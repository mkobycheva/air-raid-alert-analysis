"""Probability metrics, paired UTC-day bootstrap, and one append-only logger."""

import csv
import os
from pathlib import Path
import tempfile

import numpy as np
import pandas as pd

RESULT_COLUMNS = ["run_id", "git_commit", "created_at", "model", "params_json", "seed", "train_start", "fold_id",
                  "eval_start", "eval_end", "lead", "scope", "n", "base_rate", "brier", "bss_vs_clim",
                  "bss_vs_persistence", "bss_ci_low", "bss_ci_high", "ece", "notes", "bss_vs_ses"]


def brier(y: np.ndarray, p: np.ndarray) -> float:
    return float(np.mean((y - p) ** 2)) if len(y) else np.nan


def bss(score: float, reference: float) -> float:
    return 1 - score / reference if reference > 0 else np.nan


def reliability(y: np.ndarray, p: np.ndarray, bins: int = 10) -> pd.DataFrame:
    if not np.isfinite(p).all() or ((p < 0) | (p > 1)).any():
        raise ValueError("Probabilities must be finite and in [0,1]")
    bucket = np.minimum((p * bins).astype(int), bins - 1)
    rows = []
    for i in range(bins):
        mask = bucket == i
        rows.append({"bin": i, "lower": i / bins, "upper": (i + 1) / bins, "n": int(mask.sum()),
                     "mean_probability": float(p[mask].mean()) if mask.any() else np.nan,
                     "observed_rate": float(y[mask].mean()) if mask.any() else np.nan})
    return pd.DataFrame(rows)


def ece(y: np.ndarray, p: np.ndarray, bins: int = 10) -> float:
    table = reliability(y, p, bins)
    return float((table.n * (table.mean_probability - table.observed_rate).abs()).sum() / len(y)) if len(y) else np.nan


def bootstrap_bss(rows: pd.DataFrame, reference: str = "clim", seed: int = 42,
                  samples: int = 300, block_days: int = 7) -> tuple[float, float]:
    """Paired circular moving blocks of UTC days, shared across all regions."""
    if samples < 1 or block_days < 1:
        raise ValueError("Bootstrap samples/block_days must be positive")
    if rows.empty:
        return np.nan, np.nan
    errors = pd.DataFrame({"day": rows["T"].dt.floor("D"),
                           "model": (rows.y - rows.p) ** 2,
                           "reference": (rows.y - rows[reference]) ** 2}).groupby("day").sum()
    rng = np.random.default_rng(seed)
    starts = rng.integers(0, len(errors), size=(samples, int(np.ceil(len(errors) / block_days))))
    selected = ((starts[..., None] + np.arange(block_days)) % len(errors)).reshape(samples, -1)[:, :len(errors)]
    numerator = errors.model.to_numpy()[selected].sum(axis=1)
    denominator = errors.reference.to_numpy()[selected].sum(axis=1)
    values = 1 - np.divide(numerator, denominator, out=np.full(samples, np.nan), where=denominator > 0)
    finite = values[np.isfinite(values)]
    return tuple(np.quantile(finite, [.025, .975])) if len(finite) else (np.nan, np.nan)


def metric_row(rows: pd.DataFrame, bins: int = 10) -> dict:
    y, p = rows.y.to_numpy(dtype=float), rows.p.to_numpy(dtype=float)
    score = brier(y, p)
    return {"n": len(rows), "base_rate": float(y.mean()) if len(y) else np.nan, "brier": score,
            "bss_vs_clim": bss(score, brier(y, rows.clim.to_numpy())),
            "bss_vs_persistence": bss(score, brier(y, rows.persistence.to_numpy())),
            "bss_vs_ses": bss(score, brier(y, rows.ses.to_numpy())) if "ses" in rows else np.nan,
            "ece": ece(y, p, bins)}


def latest_results(path: Path) -> pd.DataFrame:
    """Latest execution per model/fold/lead, retaining all its scope rows.

    Append position breaks creation-time ties. Duplicate scope rows within an
    execution retain their last occurrence. Old SES fields remain missing.
    """
    frame = pd.read_csv(path, dtype={"run_id": str, "fold_id": str})
    if "bss_vs_ses" not in frame:
        frame["bss_vs_ses"] = np.nan
    frame["_order"] = np.arange(len(frame))
    frame["_created"] = pd.to_datetime(frame.created_at, utc=True, format="ISO8601", errors="coerce")
    frame["_created"] = frame["_created"].fillna(pd.Timestamp("1970-01-01", tz="UTC"))
    keys = ["model", "fold_id", "lead"]
    ordered = frame.sort_values(["_created", "_order"])
    newest = ordered.drop_duplicates(keys, keep="last")[keys + ["run_id"]]
    selected = ordered.merge(newest, on=keys + ["run_id"], how="inner")
    return selected.drop_duplicates(keys + ["scope"], keep="last").drop(columns=["_order", "_created"]).reset_index(drop=True)


def _upgrade_schema(path: Path) -> None:
    """One-time additive header upgrade; preserve every old field verbatim.

    This adds an empty SES cell to old records without changing metric values,
    order or record count. Subsequent writes append only. No records are dropped.
    """
    with path.open(newline="") as handle:
        old = next(csv.reader(handle))
    if old == RESULT_COLUMNS:
        return
    if old != RESULT_COLUMNS[:-1]:
        raise ValueError("Existing results.csv schema differs")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", newline="", dir=path.parent, delete=False) as output:
            temporary = Path(output.name)
            writer = csv.writer(output)
            writer.writerow(RESULT_COLUMNS)
            with path.open(newline="") as source:
                reader = csv.reader(source)
                next(reader)
                for row in reader:
                    if len(row) != len(old):
                        raise ValueError("Malformed legacy log row")
                    writer.writerow(row + [""])
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def log_result(path: Path, result: dict) -> None:
    """The only results.csv writer; refuse schema drift before appending."""
    if set(result) != set(RESULT_COLUMNS):
        raise ValueError("Result does not match the results.csv schema")
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists() and path.stat().st_size > 0
    if exists:
        _upgrade_schema(path)
    with path.open("a", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=RESULT_COLUMNS)
        if not exists:
            writer.writeheader()
        writer.writerow(result)
