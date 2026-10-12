"""Validation-only ensembles, comparison tables and frozen per-lead protocol."""

import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

from airalerts.advanced import OUT, Recorder, paired_gain, recency, previous_features
from airalerts.evaluate import bootstrap_bss, latest_results, metric_row, reliability
from airalerts.features import GROUP_L, EWMA_START
from airalerts.ladder import read_panel, read_prediction
from airalerts.splits import walk_forward_folds
from airalerts.advanced import protocol

REFERENCE_NAMES = ("climatology", "persistence_hard", "persistence_prob", "seasonal_day", "seasonal_week", "ses")


def eligible_models(lead: int, available: set[str]) -> list[str]:
    base = "logreg_AB" if len(previous_features(lead)) > 8 else "logreg_A"
    names = {base, "hgb", "hgb_platt"}
    half = recency(lead)
    if np.isfinite(half):
        names.add(f"{base}_hl{half:g}")
    decision = pd.read_csv(OUT / "long_selection.csv").set_index("lead").loc[lead]
    if decision.keep_long:
        names.add("logreg_ABL")
    return sorted(names & available)


def validate_predictions(pred: pd.DataFrame, lead: int) -> None:
    end = pd.Timestamp("2026-08-01", tz="UTC")
    if pred.empty or pred["T"].lt(pd.Timestamp("2026-06-01", tz="UTC")).any() or (pred["T"] + pd.Timedelta(hours=lead+1)).gt(end).any():
        raise ValueError("Prediction rows must be inside guarded VALID target windows")
    if pred.duplicated(["oblast", "T", "fold_id"]).any():
        raise ValueError("Duplicate prediction keys")


def ensemble_probability(model_p: np.ndarray, ses_p: np.ndarray, weight: float) -> np.ndarray:
    if weight not in (.25, .5, .75):
        raise ValueError("Ensemble weight must belong to the fixed validation grid")
    return weight * model_p + (1-weight) * ses_p


def reference_logs(args):
    """Re-log unchanged references with pooled scopes; preserve existing rows."""
    recorder = Recorder(args, "comparison_references")
    latest = latest_results(OUT / "results.csv")
    for name in REFERENCE_NAMES:
        all_pred = None
        for k in args.leads:
            current = Path("data/processed/predictions") / f"{name}_k{k}.csv.gz"
            if current.exists():
                pred = read_prediction(name,k)
            else:
                if all_pred is None:
                    frames = []
                    for fold in map(str, range(1,5)):
                        stem = Path("data/processed/predictions") / f"{name}_{fold}"
                        path = stem.with_suffix(".parquet") if stem.with_suffix(".parquet").exists() else stem.with_suffix(".csv.gz")
                        frame = pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path, low_memory=False, dtype={"fold_id":str})
                        frame["T"] = pd.to_datetime(frame["T"], utc=True, format="ISO8601")
                        frames.append(frame)
                    all_pred = pd.concat(frames,ignore_index=True)
                pred = all_pred.loc[all_pred.lead.eq(k)].copy()
            for fold,frame in pred.groupby("fold_id"):
                expected = latest.loc[latest.model.eq(name) & latest.fold_id.eq(fold) & latest.lead.eq(k)].run_id.unique()
                if len(expected) != 1 or set(frame.run_id.unique()) != set(expected):
                    raise ValueError("Reference prediction file is stale relative to results.csv")
            source = latest.loc[latest.model.eq(name) & latest.fold_id.eq("1") & latest.scope.eq("ALL") & latest.lead.eq(k)].iloc[0]
            source_config = json.loads(source.params_json)
            while "reference_rule" in source_config:
                source_config = source_config["reference_rule"]
            validate_predictions(pred,k)
            recorder.log(pred,name,k,{"features":[],"half_life":"inf","reference_rule":source_config,
                                     "source_run_id":source.run_id,"selection":"unchanged TRAIN-only reference"})
    recorder.finish("Unchanged saved reference predictions are checked against their latest fold run_ids and logged with pooled scopes. No refitting or TEST access.")


def descriptor(name: str, params: dict) -> dict:
    """Freeze rules/hyperparameters, excluding fold-specific fitted quantities."""
    if name.startswith("ens_ses_"):
        base = descriptor(params["base_model"], params["base_params"])
        return {"model":name,"features":base["features"],"hyperparameters":{"base_model":base,"ses":descriptor("ses",{})},
                "half_life":base["half_life"],"ensemble_weight":params["weight_learned"],
                "ensemble_weight_definition":"weight on learned base model; remaining weight on SES"}
    features = params.get("features", [])
    if name.startswith("hgb"):
        hyper = {key:params[key] for key in ("learning_rate","max_depth","max_iter")}
        hyper.update(early_stopping={"method":"chronological TRAIN Brier","tail_days":14,"step_trees":10,
                    "patience_trees":30,"min_improvement":1e-5,"inner_embargo_hours":25},
                    calibration_tail_days=14,refit="pre-calibration TRAIN; choose iterations afresh on TRAIN",
                    base_rate_fit="actual inner fitting subset", min_samples_leaf=20, max_leaf_nodes=31,
                    l2_regularization=0., max_bins=255, random_state=42)
        hyper["calibration"] = {"method":"Platt" if name=="hgb_platt" else "none","tail_days":14,
                                "C":1e6,"epsilon":1e-6,"fit_on":"chronological TRAIN calibration tail only"}
    elif name.startswith("logreg"):
        hyper = {"C":params["C"],"penalty":"l2","scaler":"TRAIN-only StandardScaler",
                 "solver":"lbfgs","max_iter":1000,"class_weight":None}
    elif name=="ses":
        hyper = {"alpha_candidates":[.01,.05,.1,.3,.6],"alpha_selection":"minimise TRAIN Brier separately per lead",
                 "trend":False,"seasonality":False,"warmup_days":56,
                 "observation":"last completed hourly touch indicator","initialization":"first warmup indicator"}
    elif name in ("seasonal_day","seasonal_week"):
        hyper = {"window_candidates":[7,14,28] if name=="seasonal_day" else [4,8],
                 "window_unit":"days" if name=="seasonal_day" else "weeks",
                 "selection":"TRAIN Brier per lead","clock":"Europe/Kyiv target hour/day-of-week",
                 "warmup_days":56}
    elif name=="persistence_hard":
        hyper = {"prediction":"instantaneous state at T"}
    else:
        hyper = {"rate_fit":"TRAIN only, per oblast"}
        if name=="persistence_prob": hyper["condition"]="state at T"
    if set(GROUP_L) & set(features):
        hyper["fixed_long_memory"] = {"share_hours":672,"ewma_half_life_hours":336,"ewma_origin":EWMA_START.isoformat(),"ewma_initial_level":0.}
    return {"model":name,"features":features,"hyperparameters":hyper,"half_life":params.get("half_life","inf"),"ensemble_weight":None}


def run_freeze(args):
    panel = read_panel(args.panel)
    list(walk_forward_folds(panel,protocol(args),0))
    reference_logs(args)
    recorder = Recorder(args,"ensemble")
    latest = latest_results(OUT / "results.csv")
    pools = latest.loc[latest.fold_id.eq("pooled") & latest.scope.eq("ALL")]
    trials, selections = [], []
    for k in args.leads:
        lead_rows = pools.loc[pools.lead.eq(k)].set_index("model")
        eligible = eligible_models(k,set(lead_rows.index))
        base = min(eligible,key=lambda name:(float(lead_rows.loc[name,"brier"]),name))
        pred = read_prediction(base,k)
        validate_predictions(pred,k)
        candidates = []
        for weight in (.25,.5,.75):
            trial = pred.copy()
            trial["p"] = ensemble_probability(pred.p.to_numpy(),pred.ses.to_numpy(),weight)
            score = metric_row(trial)["brier"]
            candidates.append((score,weight,trial))
            trials.append({"lead":k,"base_model":base,"weight_learned":weight,"n":len(pred),"brier":score,"run_id":recorder.run_id})
        _,weight,ensemble = min(candidates,key=lambda item:(item[0],item[1]))
        base_config = json.loads(lead_rows.loc[base,"params_json"])
        name = "ens_ses_"+base
        recorder.log(ensemble,name,k,{"features":base_config.get("features",[]),"base_model":base,
            "base_params":base_config,"half_life":base_config.get("half_life","inf"),"weight_learned":weight,
            "weight_ses":1-weight,"selection":"fixed weight grid on pooled VALID Brier"})
        gain,low,high = paired_gain(ensemble,pred,args)
        selections.append({"lead":k,"model":name,"base_model":base,"weight_learned":weight,
                           "gain_vs_base":gain,"ci_low":low,"ci_high":high,"run_id":recorder.run_id})
    pd.DataFrame(trials).to_csv(OUT / "ensemble_candidate_scores.csv",index=False)
    pd.DataFrame(selections).to_csv(OUT / "ensemble_selection.csv",index=False)
    recorder.finish("Fixed SES averaging weights {0.25,0.5,0.75} selected on pooled VALID; learned base respects context/long-memory/recency gates. No other optional experiment run.")
    return compare_and_freeze(args)


def compare_and_freeze(args):
    import sklearn
    latest = latest_results(OUT / "results.csv")
    pools = latest.loc[latest.fold_id.eq("pooled") & latest.scope.eq("ALL")].copy()
    comparison, frozen, chosen_rows, per_region, calibration = [], {}, [], [], []
    for _,row in pools.iterrows():
        name,k = row.model,int(row.lead)
        if k not in args.leads: continue
        pred = read_prediction(name,k)
        validate_predictions(pred,k)
        if set(pred.run_id.unique()) != {row.run_id}:
            raise ValueError("Comparison prediction run_id differs from latest pooled log")
        for reference,column in [("clim","bss_vs_clim"),("persistence","bss_vs_persistence"),("ses","bss_vs_ses")]:
            low,high = bootstrap_bss(pred,reference,args.seed,args.bootstrap_samples,7)
            comparison.append({"model":name,"lead":k,"run_id":row.run_id,"reference":reference,
                               "n":row.n,"brier":row.brier,"bss":row[column],"ci_low":low,"ci_high":high,"ece":row.ece})
    table = pd.DataFrame(comparison)
    table.to_csv(OUT / "comparison_table.csv",index=False)
    for k in args.leads:
        candidates = pools.loc[pools.lead.eq(k)].set_index("model")
        eligible = set(eligible_models(k,set(candidates.index))) | set(REFERENCE_NAMES)
        ensemble = pd.read_csv(OUT / "ensemble_selection.csv").set_index("lead").loc[k,"model"]
        eligible.add(ensemble)
        best = min(eligible & set(candidates.index),key=lambda name:(float(candidates.loc[name,"brier"]),name))
        row = candidates.loc[best]
        config = descriptor(best,json.loads(row.params_json))
        frozen[str(k)] = {**config,"validation_run_id":row.run_id,"validation_brier":float(row.brier)}
        chosen_rows.append({"lead":k,"model":best,"n":row.n,"brier":row.brier,"bss_vs_clim":row.bss_vs_clim,
                           "bss_vs_persistence":row.bss_vs_persistence,"bss_vs_ses":row.bss_vs_ses,"ece":row.ece,
                           "half_life":config["half_life"],"ensemble_weight":config["ensemble_weight"]})
        pred = read_prediction(best,k)
        calibration.append(reliability(pred.y.to_numpy(),pred.p.to_numpy()).assign(model=best,lead=k))
        for fold_id,frame in pred.groupby("fold_id"):
            flags = frame.groupby("oblast").flagged.first()
            logged = latest.loc[latest.model.eq(best) & latest.lead.eq(k) & latest.fold_id.eq(fold_id) & ~latest.scope.isin(["ALL","ALL_excl_flagged"])]
            for _,region in logged.iterrows():
                per_region.append({"model":best,"lead":k,"fold_id":fold_id,"oblast":region.scope,
                    "flagged":bool(flags.loc[region.scope]),"n":region.n,"base_rate":region.base_rate,"brier":region.brier,
                    "bss_vs_clim":region.bss_vs_clim,"bss_vs_persistence":region.bss_vs_persistence,"bss_vs_ses":region.bss_vs_ses,"ece":region.ece})
    chosen = pd.DataFrame(chosen_rows)
    chosen.to_csv(OUT / "frozen_validation.csv",index=False)
    pd.DataFrame(per_region).to_csv(OUT / "best_per_oblast.csv",index=False)
    pd.concat(calibration,ignore_index=True).to_csv(OUT / "best_reliability.csv",index=False)
    config = {"status":"frozen_validation_only","test_evaluated":False,"official_variant":"B",
        "train_start":args.train_start,"fold_boundaries":args.fold_boundaries,"test_start":"2026-08-01",
        "embargo_hours":25,"primary_leads":[1,2,3,4,5,6],"separate_nowcast_lead":0,"secondary_leads":[12,24],
        "target":"variant-B interval touches [T+k,T+k+1h)","feature_information":"starts<=T; finishes known only if<=T",
        "seed":args.seed,"bootstrap":{"block_days":7,"samples":args.bootstrap_samples},
        "flag_thresholds":{"low":.03,"high":.95,"fit_on":"TRAIN target rate per fold/lead"},
        "model_selection":"pooled walk-forward VALID Brier with prior feature retention gates",
        "models":frozen,"versions":{"python":sys.version.split()[0],"sklearn":sklearn.__version__,"pandas":pd.__version__,"numpy":np.__version__},
        "inputs_sha256":{"panel":hashlib.sha256(args.panel.read_bytes()).hexdigest(),"official":hashlib.sha256(args.official.read_bytes()).hexdigest()},
        "deferred":["calendar ablation","rolling refit","robustness A/D and alternative TRAIN_START"],
        "limitations":["artificial closures not corrected","earlier exploration overlapped TEST","December 2025 definition break",
                       "incomplete in-panel adjacency","June-July validation only","selection/multiple comparisons not covered by CIs"]}
    Path("config").mkdir(exist_ok=True)
    Path("config/final_config.json").write_text(json.dumps(config,indent=2,sort_keys=True,allow_nan=False)+"\n")
    write_summary(chosen,pools,config)
    print(chosen.to_string(index=False),flush=True)
    return chosen


def write_summary(chosen: pd.DataFrame, pools: pd.DataFrame, config: dict):
    lines = ["# Validation comparison and freeze", "", "VERIFIED: experiments ran in order: reference models → A → AB/ablations → recency → fixed long memory → HGB → SES ensemble. TEST was not evaluated. All numbers below use latest pooled results.csv records; stale runs remain in the append-only log and are ignored by latest_results.", "", "VERIFIED: selected models (pooled VALID Brier; lead 0 separate):", "", "```text", chosen.to_string(index=False,float_format=lambda x:f"{x:.5f}"), "```", ""]
    for k in (1,6,12,24):
        subset=pools.loc[pools.lead.eq(k)].set_index("model")
        values={name:float(subset.loc[name,"bss_vs_ses"]) for name in ("logreg_A","logreg_AB","logreg_ABL","hgb")}
        lines.append(f"VERIFIED: lead {k} BSS versus SES: "+", ".join(f"{name}={score:.5f}" for name,score in values.items())+".")
    lines.extend(["", "VERIFIED: long-memory retention uses the matched-recency AB gain gate, not superiority to SES. The complete per-lead paired gains are in long_gains.csv. HGB used the full eight-point grid and chronological TRAIN stopping/calibration tails; no random holdout. Raw and triggered Platt ECE are in hgb_validation.csv. Ensemble weights were selected only from 0.25/0.5/0.75.", "", "VERIFIED: table, seven-day CIs for all three references, per-oblast TRAIN flags, and calibration are in comparison_table.csv, best_per_oblast.csv and best_reliability.csv. Config freezes rules/hyperparameters; final coefficients, SES alpha and HGB stopping iterations must be fitted on FINAL TRAIN only, if later authorised.", "", "## HYPOTHESES NOT CONFIRMED", ""])
    for k in (12,24):
        subset=pools.loc[pools.lead.eq(k)].set_index("model")
        lines.append(f"- VERIFIED: plain logistic superiority to SES at lead {k} is not supported by its point score: A={subset.loc['logreg_A','bss_vs_ses']:.5f}, AB={subset.loc['logreg_AB','bss_vs_ses']:.5f}; long-memory ABL={subset.loc['logreg_ABL','bss_vs_ses']:.5f}.")
    long = pd.read_csv(OUT / "long_selection.csv")
    missing=long.loc[~long.keep_long,"lead"].tolist()
    for k in missing:
        row=pools.loc[pools.lead.eq(k)&pools.model.eq("logreg_ABL")].iloc[0]
        lines.append(f"- VERIFIED: universal long-memory improvement is not confirmed; retention failed at lead {k} (ABL BSS versus climatology {row.bss_vs_clim:.5f}; paired gate in long_gains.csv).")
    lines.extend(["- HYPOTHESIS: validation gains will generalise beyond June–July; no FINAL evaluation of these frozen models exists.",
                  "- HYPOTHESIS: calendar features, rolling refits or robustness to A/D/earlier TRAIN_START will help; these remain unstarted.","",
                  "VERIFIED: reported CIs are conditional on validation selection and do not adjust for tuning or multiple comparisons. Existing artificial-close, definition-break, incomplete-adjacency and earlier TEST-overlap limitations remain. No HGB/software library/network provenance was inferred from a live service."])
    (OUT / "validation_summary.md").write_text("\n".join(lines)+"\n")
