"""Validation-only pooled logistic ladder through recency weighting."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np
import pandas as pd

from airalerts.evaluate import bootstrap_bss, log_result, metric_row, reliability
from airalerts.features import GROUP_A, GROUP_B, observed_features
from airalerts.io import load_official
from airalerts.models import ReferenceModel
from airalerts.panel import save_frame
from airalerts.pooled import PooledLogistic, fold_data, recency_weights
from airalerts.splits import FoldParams

SETS = {
    "logreg_A": GROUP_A,
    "logreg_AB": GROUP_A + GROUP_B,
    "logreg_AB_neighbors": GROUP_A + ("neighbor_share_now", "neighbor_share_6h"),
    "logreg_AB_national": GROUP_A + ("national_active_count",),
    "logreg_AB_base": GROUP_A + ("base_rate",),
}


def read_panel(path: Path) -> pd.DataFrame:
    panel = pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path, low_memory=False)
    panel["T"] = pd.to_datetime(panel["T"], utc=True, format="ISO8601")
    if panel["T"].ge(pd.Timestamp("2026-08-01", tz="UTC")).any():
        raise ValueError("Panel contains reserved TEST rows")
    for column in [c for c in panel if c.startswith("y_")]:
        panel[column] = panel[column].map({True: True, False: False, "True": True, "False": False}).astype("boolean")
    return panel.reset_index(drop=True)


def prepare(args) -> tuple[pd.DataFrame, pd.DataFrame]:
    panel = read_panel(args.panel)
    if args.fold_boundaries[-1] > "2026-08-01":
        raise ValueError("Validation must end no later than August 1")
    include_long_memory = getattr(args, "long_memory", False)
    cache = Path("data/processed/ladder_features_long.csv.gz" if include_long_memory else "data/processed/ladder_features.csv.gz")
    meta = cache.with_suffix(".metadata.json")
    fingerprint = hashlib.sha256(args.panel.read_bytes() + args.official.read_bytes() +
                                 b"".join(Path("src/airalerts", n).read_bytes() for n in
                                          ["features.py", "neighbors.py", "grid.py", "panel.py", "io.py"])).hexdigest()
    if cache.exists() and meta.exists() and json.loads(meta.read_text()).get("fingerprint") == fingerprint:
        observed = pd.read_csv(cache, parse_dates=["T"])
    else:
        events = load_official(args.official)
        events = events.loc[events.started_at.lt(pd.Timestamp("2026-08-01", tz="UTC"))].copy()
        observed = observed_features(events, panel, include_long_memory=include_long_memory)
        cache.parent.mkdir(parents=True, exist_ok=True)
        observed.to_csv(cache, index=False, compression={"method": "gzip", "mtime": 0})
        meta.write_text(json.dumps({"fingerprint": fingerprint, "group_A": GROUP_A, "group_B": GROUP_B}) + "\n")
    return panel, observed


def references(fold) -> pd.DataFrame:
    result = fold.valid[["oblast", "T", "y"]].copy()
    for column, name in [("clim", "climatology"), ("persistence", "persistence_prob"), ("ses", "ses")]:
        model = ReferenceModel(name, (fold.lead,), (), (), (.01, .05, .1, .3, .6)).fit(fold.train)
        result[column] = model.predict_proba(fold.valid, fold.lead)
    result["flagged"] = result.oblast.isin(fold.flagged)
    result["fold_id"] = fold.fold_id
    result["lead"] = fold.lead
    return result


def prediction_path(model: str, lead: int) -> Path:
    return Path("data/processed/predictions") / f"{model}_k{lead}.csv.gz"


def read_prediction(model: str, lead: int) -> pd.DataFrame:
    return pd.read_csv(prediction_path(model, lead), parse_dates=["T"], dtype={"fold_id": str})


def select_grid(folds, columns, Cs, half_life, params, seed):
    """Choose one C per lead across pooled VALID, never per-fold minima."""
    candidates, predictions = [], {}
    for C in Cs:
        frames = []
        for fold in folds:
            end = pd.Timestamp(params.boundaries[int(fold.fold_id)-1], tz="UTC") - pd.Timedelta(hours=params.embargo_hours)
            weights = None if np.isinf(half_life) else recency_weights(fold.train, end, half_life)
            model = PooledLogistic(columns, C, seed).fit(fold.train, weights)
            frame = references(fold)
            frame["p"] = model.predict_proba(fold.valid, fold.lead)
            frames.append(frame)
            candidates.append({"C": C, "half_life": "inf" if np.isinf(half_life) else half_life,
                               "fold_id": fold.fold_id, "n": len(frame), "brier": metric_row(frame)["brier"]})
        predictions[C] = pd.concat(frames, ignore_index=True)
    # Smaller C wins a tie. Predictions are from four independent TRAIN fits.
    chosen = min(Cs, key=lambda C: (float(np.mean((predictions[C].y-predictions[C].p)**2)), C))
    return chosen, predictions[chosen], candidates


def log_predictions(pred, model, lead, selected, args, run_id, commit, created):
    out = Path("reports/model")
    rows, calibration, cis = [], [], []
    grouped = list(pred.groupby("fold_id", sort=True)) + [("pooled", pred)]
    for fold_id, frame in grouped:
        scopes = {"ALL": frame, "ALL_excl_flagged": frame.loc[~frame.flagged]}
        scopes.update(dict(tuple(frame.groupby("oblast", sort=True))))
        if fold_id == "pooled":
            start, end = args.fold_boundaries[0], args.fold_boundaries[-1]
        else:
            start, end = args.fold_boundaries[int(fold_id)-1:int(fold_id)+1]
        for scope, subset in scopes.items():
            ci = bootstrap_bss(subset, seed=args.seed, samples=args.bootstrap_samples) if scope.startswith("ALL") else (np.nan, np.nan)
            values = metric_row(subset)
            record = {"run_id": run_id, "git_commit": commit, "created_at": created,
                      "model": model, "params_json": json.dumps(selected, sort_keys=True), "seed": args.seed,
                      "train_start": args.train_start, "fold_id": fold_id, "eval_start": start, "eval_end": end,
                      "lead": lead, "scope": scope, **values, "bss_ci_low": ci[0], "bss_ci_high": ci[1],
                      "notes": "validation; selected on these folds; 7-day CI vs clim; no class resampling; no TEST"}
            log_result(out / "results.csv", record)
            rows.append(record)
            if scope.startswith("ALL"):
                calibration.append(reliability(subset.y.to_numpy(), subset.p.to_numpy()).assign(model=model,lead=lead,fold_id=fold_id,scope=scope))
                if fold_id == "pooled":
                    for reference in ("clim", "persistence", "ses"):
                        for block_days in (7, 1):
                            low, high = bootstrap_bss(subset, reference, args.seed, args.bootstrap_samples, block_days)
                            cis.append({"model": model,"lead": lead,"scope": scope,"reference": reference,"block_days": block_days,"low": low,"high": high})
    pred["run_id"] = run_id
    # Per-model/fold prediction files; one lead is held at a time.
    for fold_id, frame in pred.groupby("fold_id"):
        save_frame(frame, Path("data/processed/predictions") / f"{model}_{fold_id}_k{lead}.parquet")
    pred.to_csv(prediction_path(model, lead), index=False, compression={"method": "gzip", "mtime": 0})
    return rows, calibration, cis


def run(args) -> pd.DataFrame:
    panel, observed = prepare(args)
    params = FoldParams(args.train_start, tuple(args.fold_boundaries), "2026-08-01", args.embargo_hours)
    out = Path("reports/model")
    out.mkdir(parents=True, exist_ok=True)
    if args.stage == "prepare":
        inventory = []
        for k in args.leads:
            for fold in fold_data(panel, observed, params, k, GROUP_A + GROUP_B):
                inventory.append({"fold_id": fold.fold_id,"lead": k,"train_n": len(fold.train),"valid_n": len(fold.valid),
                                  "max_train_T": str(fold.train["T"].max()), "flagged": ";".join(fold.flagged)})
        result = pd.DataFrame(inventory)
        result.to_csv(out / "pooled_inventory.csv", index=False)
        print(result.to_string(index=False), flush=True)
        return result
    created = datetime.now(timezone.utc).isoformat()
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    fingerprint = hashlib.sha256(args.panel.read_bytes() + Path("src/airalerts/features.py").read_bytes() + Path(__file__).read_bytes()).hexdigest()
    run_id = hashlib.sha256((created + json.dumps(vars(args), default=str, sort_keys=True)).encode()).hexdigest()[:16]
    all_rows, calibration, intervals, candidates, selections, gains = [], [], [], [], [], []
    for k in args.leads:
        if args.stage == "A":
            names = ["logreg_A"]
        elif args.stage == "AB":
            names = ["logreg_AB", "logreg_AB_neighbors", "logreg_AB_national", "logreg_AB_base"]
        else:
            decisions = pd.read_csv(out / "ab_selection.csv")
            choice = decisions.loc[decisions.lead.eq(k)].iloc[0]
            base = "logreg_AB" if choice.keep_context else "logreg_A"
            previous = pd.read_csv(out / ("AB_selected.csv" if base == "logreg_AB" else "A_selected.csv"))
            C = float(previous.loc[(previous.model == base) & (previous.lead == k), "C"].iloc[0])
            names = [base + "_hl" + ("inf" if np.isinf(h) else f"{h:g}") for h in args.half_lives]
        lead_choices = []
        for name in names:
            columns = SETS[name] if args.stage != "recency" else SETS[base]
            half_life = np.inf if args.stage != "recency" else args.half_lives[names.index(name)]
            folds = list(fold_data(panel, observed, params, k, columns))
            chosen, pred, trials = select_grid(folds, columns, args.C if args.stage != "recency" else [C], half_life, params, args.seed)
            selected = {"C": chosen, "features": list(columns), "half_life": "inf" if np.isinf(half_life) else half_life,
                        "embargo_hours": args.embargo_hours, "fold_boundaries": args.fold_boundaries,
                        "selection": "pooled validation Brier; fixed C in recency stage", "input_code_sha256": fingerprint,
                        "dirty_worktree": bool(subprocess.check_output(["git", "status", "--porcelain"], text=True).strip())}
            entries, tables, ci = log_predictions(pred, name, k, selected, args, run_id, commit, created)
            all_rows.extend(entries);calibration.extend(tables);intervals.extend(ci)
            candidates.extend({**row,"model": name,"lead": k,"run_id": run_id} for row in trials)
            selections.append({"model": name,"lead": k,"C": chosen,"half_life": selected["half_life"],"run_id": run_id})
            lead_choices.append({"model": name, "brier": metric_row(pred)["brier"], "C": chosen, "half_life": selected["half_life"]})
            print(f"{args.stage} lead={k} model={name} C={chosen} BSS_clim={metric_row(pred)['bss_vs_clim']:.5f}", flush=True)
            del folds
            if args.stage == "AB" and name == "logreg_AB":
                baseline = read_prediction("logreg_A", k)
                paired = pred.merge(baseline[["oblast","T","fold_id","p"]].rename(columns={"p":"baseline"}), on=["oblast","T","fold_id"], validate="one_to_one")
                if len(paired) != len(pred): raise ValueError("A/AB validation keys differ")
                low, high = bootstrap_bss(paired,"baseline",args.seed,args.bootstrap_samples)
                gain = 1 - np.mean((paired.y-paired.p)**2) / np.mean((paired.y-paired.baseline)**2)
                gains.append({"lead": k,"relative_brier_gain_vs_A": gain,"ci_low": low,"ci_high": high,
                              "keep_context": bool(low > 0),"decision": "improvement" if low > 0 else "no evidence of improvement", "run_id": run_id})
        if args.stage == "recency":
            best = min(lead_choices, key=lambda r: (r["brier"], r["model"]))
            chosen_pred = read_prediction(best["model"], k)
            baseline = read_prediction(base, k)
            paired = chosen_pred.merge(baseline[["oblast", "T", "fold_id", "p"]].rename(columns={"p": "baseline"}),
                                       on=["oblast", "T", "fold_id"], validate="one_to_one")
            if len(paired) != len(chosen_pred):
                raise ValueError("Recency/base validation keys differ")
            low, high = bootstrap_bss(paired, "baseline", args.seed, args.bootstrap_samples)
            gain = 1 - np.mean((paired.y-paired.p)**2) / np.mean((paired.y-paired.baseline)**2)
            gains.append({"lead": k, **best, "base_model": base, "relative_brier_gain_vs_base": gain,
                          "ci_low": low, "ci_high": high, "run_id": run_id})
    results = pd.DataFrame(all_rows)
    results.to_csv(out / f"{args.stage}_validation.csv", index=False)
    pd.DataFrame(candidates).to_csv(out / f"{args.stage}_candidate_scores.csv", index=False)
    pd.DataFrame(selections).to_csv(out / f"{args.stage}_selected.csv", index=False)
    pd.concat(calibration, ignore_index=True).to_csv(out / f"{args.stage}_reliability.csv", index=False)
    pd.DataFrame(intervals).to_csv(out / f"{args.stage}_bootstrap.csv", index=False)
    if gains:
        pd.DataFrame(gains).to_csv(out / ("ab_selection.csv" if args.stage == "AB" else "recency_selection.csv"), index=False)
    summary = results.loc[results.fold_id.eq("pooled") & results.scope.eq("ALL"), ["model","lead","brier","bss_vs_clim","bss_vs_persistence","bss_vs_ses","bss_ci_low","bss_ci_high","ece"]]
    text = f"# Step {args.stage}: validation only\n\nVERIFIED: run {run_id}; 25-hour embargo, independent fold fits, pooled TRAIN, no class resampling, no calendar/identity/STL features, no TEST.\n\n"
    text += "C is chosen across the four VALID folds for each lead, not separately on each fold. Recency fixes the previous selected C and selects half-life on VALID. These validation-selected metrics are descriptive selection scores, not unbiased final performance. CI uses paired circular seven-day UTC blocks; one-day sensitivity and all three references are in the bootstrap table. Per-region and excluded-flagged metrics are logged.\n\n```text\n" + summary.to_string(index=False,float_format=lambda x:f"{x:.5f}") + "\n```\n"
    if gains: text += "\n```text\n" + pd.DataFrame(gains).to_string(index=False) + "\n```\n"
    (out / f"{args.stage}_validation.md").write_text(text)
    print(summary.to_string(index=False),flush=True)
    return results
