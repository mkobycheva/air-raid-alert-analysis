"""Offline reference validation only; no final-test invocation exists here."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np
import pandas as pd

from airalerts.evaluate import bootstrap_bss, log_result, metric_row, reliability
from airalerts.io import load_official, valid_end
from airalerts.models import ReferenceModel
from airalerts.panel import DEFAULT_LEADS, build_panel, save_frame
from airalerts.splits import FoldParams, walk_forward_folds


def run(args: argparse.Namespace) -> pd.DataFrame:
    params = FoldParams(args.train_start, tuple(args.fold_boundaries), args.test_start, args.embargo_hours)
    end = pd.Timestamp(params.boundaries[-1], tz="UTC")
    if end > pd.Timestamp("2026-08-01", tz="UTC") or end > pd.Timestamp(params.test_start, tz="UTC"):
        raise ValueError("Task 5A evaluation/panel must end no later than 2026-08-01")
    # Guard all boundaries before reading the input or constructing a panel.
    empty = pd.DataFrame({"T": pd.Series([], dtype="datetime64[ns, UTC]"), "y_0": pd.Series([], dtype="boolean")})
    list(walk_forward_folds(empty, params, 0))
    official = load_official(args.official)
    if end > valid_end(official):
        raise ValueError("Validation exceeds the independently trimmed source end")
    # Discard every start in TEST and hide finishes beyond validation. No TEST
    # labels or test rows enter any panel, fitted rate, tuning or metric.
    official = official.loc[official.started_at.lt(end)].copy()
    panel = build_panel(official, params.train_start, end, leads=tuple(args.leads), variant=args.variant,
                        day_windows=tuple(args.day_windows), week_windows=tuple(args.week_windows),
                        alphas=tuple(args.alphas))
    panel_path = save_frame(panel, Path("data/processed/panel.parquet"))
    print(f"Panel saved: {panel_path}; {len(panel)} rows; T in [{panel['T'].min()}, {end})")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], text=True).strip())
    config = vars(args).copy()
    config["official"] = str(args.official)
    input_hash = hashlib.sha256(args.official.read_bytes()).hexdigest()
    config["input_sha256"] = input_hash
    source_files = [Path(__file__), *[Path("src/airalerts") / name for name in
                    ("panel.py", "splits.py", "models.py", "evaluate.py", "grid.py", "io.py")]]
    config["source_sha256"] = hashlib.sha256(b"".join(path.read_bytes() for path in source_files)).hexdigest()
    config["dirty_worktree"] = dirty
    config["validation_label_boundary"] = end.isoformat()
    serialized = json.dumps(config, sort_keys=True)
    created = datetime.now(timezone.utc).isoformat()
    run_id = hashlib.sha256((commit + serialized + created).encode()).hexdigest()[:16]
    out = Path("reports/model")
    out.mkdir(parents=True, exist_ok=True)
    results, pooled, calibration, intervals, selected = [], [], [], [], []
    names = ("climatology", "persistence_hard", "persistence_prob", "seasonal_day", "seasonal_week", "ses")
    for fold_id in map(str, range(1, len(params.boundaries))):
        predictions = {name: [] for name in names}
        for k in args.leads:
            _, train_mask, eval_mask = next(fold for fold in walk_forward_folds(panel, params, k) if fold[0] == fold_id)
            train, evaluation = panel.loc[train_mask], panel.loc[eval_mask]
            models = {name: ReferenceModel(name, (k,), tuple(args.day_windows), tuple(args.week_windows), tuple(args.alphas)).fit(train) for name in names}
            clim = models["climatology"].predict_proba(evaluation, k)
            persistence = models["persistence_prob"].predict_proba(evaluation, k)
            ses = models["ses"].predict_proba(evaluation, k)
            rate = train.groupby("oblast")[f"y_{k}"].mean()
            flagged = rate.index[(rate < args.flag_low) | (rate > args.flag_high)].tolist()
            fold_start, fold_end = params.boundaries[int(fold_id) - 1:int(fold_id) + 1]
            for name, model in models.items():
                pred = evaluation[["oblast", "T"]].copy()
                pred["y"] = evaluation[f"y_{k}"].astype(float)
                pred["p"], pred["clim"], pred["persistence"] = model.predict_proba(evaluation, k), clim, persistence
                pred["ses"] = ses
                pred["lead"], pred["fold_id"], pred["run_id"] = k, fold_id, run_id
                pred["flagged"] = pred.oblast.isin(flagged)
                predictions[name].append(pred)
                pooled.append(pred.assign(model=name))
                fitted = {**config, "fitted": model.params.get(k, {}), "flagged_oblasts": flagged,
                          "ci_reference": "climatology"}
                selected.append({"fold_id": fold_id, "lead": k, "model": name,
                                 "fitted_json": json.dumps(model.params.get(k, {}), sort_keys=True),
                                 "flagged_oblasts": ";".join(flagged)})
                scopes = {"ALL": pred, "ALL_excl_flagged": pred.loc[~pred.flagged]}
                scopes.update({oblast: group for oblast, group in pred.groupby("oblast")})
                for scope, group in scopes.items():
                    ci = bootstrap_bss(group, seed=args.seed, samples=args.bootstrap_samples, block_days=args.block_days) if scope.startswith("ALL") else (np.nan, np.nan)
                    result = {"run_id": run_id, "git_commit": commit, "created_at": created, "model": name,
                              "params_json": json.dumps(fitted, sort_keys=True), "seed": args.seed,
                              "train_start": params.train_start, "fold_id": fold_id, "eval_start": fold_start,
                              "eval_end": fold_end, "lead": k, "scope": scope, **metric_row(group, args.ece_bins),
                              "bss_ci_low": ci[0], "bss_ci_high": ci[1],
                              "notes": f"validation only; CI vs climatology; {args.block_days}-day blocks; embargo={args.embargo_hours}h; dirty_worktree=" + str(dirty)}
                    log_result(out / "results.csv", result)
                    results.append(result)
                    if scope.startswith("ALL"):
                        table = reliability(group.y.to_numpy(), group.p.to_numpy(), args.ece_bins)
                        calibration.append(table.assign(model=name, fold_id=fold_id, lead=k, scope=scope, run_id=run_id))
        for name, frames in predictions.items():
            save_frame(pd.concat(frames, ignore_index=True), Path("data/processed/predictions") / f"{name}_{fold_id}.parquet")
        print(f"Fold {fold_id} completed; no TEST rows evaluated")
    pd.DataFrame(selected).to_csv(out / "chosen_params.csv", index=False)
    pd.concat(calibration, ignore_index=True).to_csv(out / "reliability.csv", index=False)
    all_predictions = pd.concat(pooled, ignore_index=True)
    summary = []
    result_frame = pd.DataFrame(results)
    for (name, k), group in all_predictions.groupby(["model", "lead"], sort=True):
        for scope in ("ALL", "ALL_excl_flagged"):
            subset = group if scope == "ALL" else group.loc[~group.flagged]
            row = {"model": name, "lead": k, "scope": scope, **metric_row(subset, args.ece_bins)}
            folds = result_frame.loc[(result_frame.model == name) & (result_frame.lead == k) & (result_frame.scope == scope)]
            row["fold_bss_min"], row["fold_bss_max"] = folds.bss_vs_clim.min(), folds.bss_vs_clim.max()
            for reference in ("clim", "persistence", "ses"):
                low, high = bootstrap_bss(subset, reference, args.seed, args.bootstrap_samples, args.block_days)
                intervals.append({"run_id": run_id, "model": name, "lead": k, "scope": scope,
                                  "reference": reference, "block_days": args.block_days, "low": low, "high": high})
                day_low, day_high = bootstrap_bss(subset, reference, args.seed, args.bootstrap_samples, 1)
                intervals.append({"run_id": run_id, "model": name, "lead": k, "scope": scope,
                                  "reference": reference, "block_days": 1, "low": day_low, "high": day_high})
                if reference == "clim":
                    row["bss_ci_low"], row["bss_ci_high"] = low, high
            summary.append(row)
    summary = pd.DataFrame(summary)
    summary.to_csv(out / "reference_validation.csv", index=False)
    pd.DataFrame(intervals).to_csv(out / "bootstrap.csv", index=False)
    columns = ["model", "lead", "scope", "n", "bss_vs_clim", "bss_vs_persistence", "bss_vs_ses", "fold_bss_min", "fold_bss_max", "bss_ci_low", "bss_ci_high"]
    text = "# Reference validation only\n\nRun: " + run_id + "; git: " + commit + "; dirty worktree: " + str(dirty)
    text += "\n\nParameters: `" + serialized + "`\n\n"
    text += "No TEST rows or target hours were used. Labels beyond the validation boundary are missing; "
    text += "the last fold therefore has fewer eligible rows at longer leads. Leads are evaluated separately, including 0. "
    text += "Pooled BSS is computed from pooled squared errors, not averaged fold scores. Fold spread is min/max BSS vs climatology. "
    text += f"Intervals use paired circular {args.block_days}-day blocks across all oblasts; all three references and 1-day sensitivity are in bootstrap.csv. "
    text += "Flagging is lead/fold-specific and based only on TRAIN. Results.csv is append-only; other summaries describe this run.\n\n"
    text += "```text\n" + summary[columns].to_string(index=False, float_format=lambda x: f"{x:.5f}") + "\n```\n"
    (out / "reference_validation.md").write_text(text)
    print(summary.loc[summary.scope.eq("ALL"), columns].to_string(index=False))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--official", type=Path, default=Path("data/raw/official_data_en.csv"))
    parser.add_argument("--train-start", default="2025-12-01")
    parser.add_argument("--fold-boundaries", nargs="+", default=["2026-06-01", "2026-06-16", "2026-07-01", "2026-07-16", "2026-08-01"])
    parser.add_argument("--test-start", default="2026-08-01")
    parser.add_argument("--variant", choices=["B"], default="B")
    parser.add_argument("--leads", nargs="+", type=int, default=list(DEFAULT_LEADS))
    parser.add_argument("--day-windows", nargs="+", type=int, default=[7, 14, 28])
    parser.add_argument("--week-windows", nargs="+", type=int, default=[4, 8])
    parser.add_argument("--alphas", nargs="+", type=float, default=[.01, .05, .1, .3, .6])
    parser.add_argument("--flag-low", type=float, default=.03)
    parser.add_argument("--flag-high", type=float, default=.95)
    parser.add_argument("--ece-bins", type=int, default=10)
    parser.add_argument("--bootstrap-samples", type=int, default=300)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--embargo-hours", type=int, default=25)
    parser.add_argument("--block-days", type=int, default=7)
    run(parser.parse_args())


if __name__ == "__main__":
    main()
