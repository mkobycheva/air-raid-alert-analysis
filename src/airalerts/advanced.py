"""Validation-only long-memory, HGB and ensemble experiments; never FINAL."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np
import pandas as pd

from airalerts.evaluate import bootstrap_bss, metric_row
from airalerts.features import GROUP_A, GROUP_B, GROUP_L, EWMA_START
from airalerts.ladder import prepare, select_grid, read_prediction, log_predictions, references
from airalerts.pooled import fold_data
from airalerts.splits import FoldParams

OUT = Path("reports/model")
LONG_FEATURES = GROUP_A + GROUP_B + GROUP_L


def protocol(args) -> FoldParams:
    return FoldParams(args.train_start, tuple(args.fold_boundaries), "2026-08-01", args.embargo_hours)


def recency(lead: int) -> float:
    """Carry recency only where its paired gain lower bound is positive."""
    row = pd.read_csv(OUT / "recency_selection.csv").set_index("lead").loc[lead]
    return float(row.half_life) if row.ci_low > 0 else np.inf


def previous_features(lead: int) -> tuple[str, ...]:
    row = pd.read_csv(OUT / "ab_selection.csv").set_index("lead").loc[lead]
    return GROUP_A + GROUP_B if row.keep_context else GROUP_A


def selected_features(lead: int) -> tuple[str, ...]:
    row = pd.read_csv(OUT / "long_selection.csv").set_index("lead").loc[lead]
    return LONG_FEATURES if row.keep_long else previous_features(lead)


def paired_gain(pred: pd.DataFrame, base: pd.DataFrame, args) -> tuple[float, float, float]:
    keys = ["oblast", "T", "fold_id"]
    paired = pred.merge(base[keys + ["p", "y"]].rename(columns={"p": "baseline", "y": "base_y"}), on=keys, validate="one_to_one")
    if len(paired) != len(pred) or not np.array_equal(paired.y, paired.base_y):
        raise ValueError("Paired validation rows/labels differ")
    denominator = float(np.mean((paired.y - paired.baseline) ** 2))
    gain = 1 - float(np.mean((paired.y - paired.p) ** 2)) / denominator if denominator else np.nan
    low, high = bootstrap_bss(paired, "baseline", args.seed, args.bootstrap_samples, 7)
    return gain, low, high


class Recorder:
    def __init__(self, args, stage: str):
        self.args, self.stage = args, stage
        OUT.mkdir(parents=True, exist_ok=True)
        self.created = datetime.now(timezone.utc).isoformat()
        self.commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        self.run_id = hashlib.sha256((self.created + stage).encode()).hexdigest()[:16]
        self.rows, self.calibration, self.intervals = [], [], []
        files = ["features.py", "pooled.py", "advanced.py", "hgb.py", "freeze.py", "ladder.py", "splits.py", "evaluate.py", "models.py", "neighbors.py", "grid.py", "panel.py", "io.py"]
        self.fingerprint = hashlib.sha256(args.panel.read_bytes() + args.official.read_bytes() +
                                          b"".join(Path("src/airalerts", n).read_bytes() for n in files if Path("src/airalerts", n).exists())).hexdigest()

    def log(self, pred: pd.DataFrame, name: str, lead: int, selected: dict):
        config = {**selected, "embargo_hours": self.args.embargo_hours, "fold_boundaries": self.args.fold_boundaries,
                  "stage": self.stage, "source_input_sha256": self.fingerprint,
                  "dirty_worktree": bool(subprocess.check_output(["git", "status", "--porcelain"], text=True).strip())}
        rows, calibration, intervals = log_predictions(pred, name, lead, config, self.args, self.run_id, self.commit, self.created)
        self.rows.extend(rows); self.calibration.extend(calibration); self.intervals.extend(intervals)
        pooled = metric_row(pred)
        print(f"{self.stage}: lead={lead}, model={name}, BSS_clim={pooled['bss_vs_clim']:.5f}, ECE={pooled['ece']:.5f}", flush=True)

    def finish(self, note: str = "") -> pd.DataFrame:
        results = pd.DataFrame(self.rows)
        results.to_csv(OUT / f"{self.stage}_validation.csv", index=False)
        pd.concat(self.calibration, ignore_index=True).to_csv(OUT / f"{self.stage}_reliability.csv", index=False)
        pd.DataFrame(self.intervals).to_csv(OUT / f"{self.stage}_bootstrap.csv", index=False)
        pooled = results.loc[results.fold_id.eq("pooled") & results.scope.eq("ALL")]
        columns = ["model", "lead", "n", "brier", "bss_vs_clim", "bss_vs_persistence", "bss_vs_ses", "bss_ci_low", "bss_ci_high", "ece"]
        (OUT / f"{self.stage}_validation.md").write_text(f"# {self.stage}: validation only\n\nVERIFIED: run {self.run_id}. {note}\n\n"
            "Four independent fold fits, 25-hour embargo; no TEST. VALID selects candidates, so scores/CIs are descriptive selection results and do not adjust for selection/multiple comparisons. Seven-day paired blocks are primary; one-day sensitivity is saved.\n\n```text\n" + pooled[columns].to_string(index=False, float_format=lambda x:f"{x:.5f}") + "\n```\n")
        return results


def run_long(args):
    args.long_memory = True
    panel, observed = prepare(args)
    params = protocol(args)
    recorder = Recorder(args, "long")
    choices, comparisons, trials = [], [], []
    for k in args.leads:
        half_life = recency(k)
        folds = list(fold_data(panel, observed, params, k, LONG_FEATURES))
        C, pred, candidates = select_grid(folds, LONG_FEATURES, [.01, .1, 1., 10.], half_life, params, args.seed)
        config = {"features": list(LONG_FEATURES), "C": C, "half_life": "inf" if np.isinf(half_life) else half_life,
                  "share_window_hours": 672, "ewma_half_life_hours": 336, "ewma_start": EWMA_START.isoformat(),
                  "ewma_initial_level": 0., "ewma_signal": "completed hourly touch indicator", "selection": "C by pooled VALID Brier"}
        recorder.log(pred, "logreg_ABL", k, config)
        matched_name = "logreg_AB" if np.isinf(half_life) else f"logreg_AB_hl{half_life:g}"
        matched = read_prediction(matched_name, k)
        gain, low, high = paired_gain(pred, matched, args)
        choices.append({"lead": k, "C": C, "half_life": config["half_life"], "keep_long": bool(low > 0),
                        "AB_source": matched_name, "gain_vs_AB": gain, "ci_low": low, "ci_high": high,
                        "decision": "improvement" if low > 0 else "no evidence of improvement", "run_id": recorder.run_id})
        for label, base in [("logreg_AB", matched), ("logreg_AB_unweighted", read_prediction("logreg_AB", k)), ("ses", pred.assign(p=pred.ses))]:
            gain, low, high = paired_gain(pred, base, args)
            comparisons.append({"lead": k, "reference": label, "reference_source": matched_name if label == "logreg_AB" else label,
                                "gain": gain, "ci_low": low, "ci_high": high,
                                "decision": "improvement" if low > 0 else "no evidence of improvement" if low <= 0 <= high else "worse", "run_id": recorder.run_id})
        trials.extend({**row, "lead": k, "run_id": recorder.run_id} for row in candidates)
    pd.DataFrame(choices).to_csv(OUT / "long_selection.csv", index=False)
    pd.DataFrame(comparisons).to_csv(OUT / "long_gains.csv", index=False)
    pd.DataFrame(trials).to_csv(OUT / "long_candidate_scores.csv", index=False)
    return recorder.finish("Fixed 672-hour exact share and 336-hour EWMA half-life; no window/half-life tuning. ABL retention requires positive gain CI against AB with matched recency. SES is comparison only. Unweighted AB comparison is also saved.")
