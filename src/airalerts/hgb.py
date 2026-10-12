"""HGB with explicit chronological stopping/calibration tails inside TRAIN."""

from itertools import product
import json

import numpy as np
import pandas as pd

from airalerts.advanced import Recorder, OUT, protocol, recency, selected_features
from airalerts.evaluate import brier, metric_row
from airalerts.ladder import prepare, references
from airalerts.pooled import fold_data, recency_weights

ECE_TRIGGER = .03
TAIL_DAYS = 14
STOP_STEP = 10
STOP_PATIENCE = 30
STOP_TOL = 1e-5


def chronological_tails(train: pd.DataFrame, train_end: pd.Timestamp, lead: int,
                        embargo_hours: int = 25) -> dict[str, pd.DataFrame]:
    if embargo_hours < 25 or embargo_hours < lead + 1:
        raise ValueError("Inner embargo must cover all label windows")
    cal_start = train_end - pd.Timedelta(days=TAIL_DAYS)
    stop_start = cal_start - pd.Timedelta(days=TAIL_DAYS)
    gap = pd.Timedelta(hours=embargo_hours)
    groups = {
        "core": train.loc[train["T"].lt(stop_start-gap)].copy(),
        "stop": train.loc[train["T"].ge(stop_start) & train["T"].lt(cal_start-gap)].copy(),
        "fit": train.loc[train["T"].lt(cal_start-gap)].copy(),
        "cal": train.loc[train["T"].ge(cal_start) & train["T"].lt(train_end)].copy(),
    }
    if any(frame.empty for frame in groups.values()):
        raise ValueError("TRAIN too short for two chronological 14-day tails")
    if (groups["core"]["T"] + pd.Timedelta(hours=lead+1)).max() > groups["stop"]["T"].min():
        raise ValueError("Core labels overlap stopping tail")
    if (groups["fit"]["T"] + pd.Timedelta(hours=lead+1)).max() > groups["cal"]["T"].min():
        raise ValueError("Fitting labels overlap calibration tail")
    return groups


def rates_from_fit(train: pd.DataFrame, *frames: pd.DataFrame) -> list[pd.DataFrame]:
    rates = train.groupby("oblast").y_0.mean()
    result = []
    for frame in (train, *frames):
        copy = frame.copy()
        copy["base_rate"] = copy.oblast.map(rates)
        if copy.base_rate.isna().any():
            raise ValueError("Inner fitting geography is incomplete")
        result.append(copy)
    return result


def select_iterations(core: pd.DataFrame, stop: pd.DataFrame, columns: tuple[str, ...],
                      learning_rate: float, max_depth: int, half_life: float,
                      train_end: pd.Timestamp, seed: int, caps: tuple[int, ...] = (100, 300)):
    from sklearn.ensemble import HistGradientBoostingClassifier
    model = HistGradientBoostingClassifier(learning_rate=learning_rate, max_depth=max_depth,
             max_iter=STOP_STEP, early_stopping=False, warm_start=True, random_state=seed)
    core, stop = rates_from_fit(core, stop)
    x, y = core[list(columns)].to_numpy(dtype=float), core.y.to_numpy(dtype=float)
    stop_x = stop[list(columns)].to_numpy(dtype=float)
    weights = recency_weights(core, train_end, half_life)
    stop_weights = recency_weights(stop, train_end, half_life)
    history = []
    best, best_n = np.inf, 0
    maximum = max(caps)
    points = sorted(set(range(STOP_STEP, maximum+1, STOP_STEP)) | set(caps))
    for n in points:
        model.set_params(max_iter=n)
        model.fit(x, y, sample_weight=weights)
        p = model.predict_proba(stop_x)[:, 1]
        score = float(np.average((stop.y.to_numpy()-p)**2, weights=stop_weights))
        history.append({"iteration": n, "stop_brier": score})
        if score < best - STOP_TOL:
            best, best_n = score, n
        if n - best_n >= STOP_PATIENCE:
            break
    chosen = {}
    for cap in caps:
        available = [row for row in history if row["iteration"] <= cap]
        selected = min(available, key=lambda row: (row["stop_brier"], row["iteration"]))
        chosen[cap] = selected["iteration"]
    return chosen, history


def refit(train: pd.DataFrame, cal: pd.DataFrame, valid: pd.DataFrame, columns: tuple[str, ...],
          learning_rate: float, max_depth: int, iterations: int, half_life: float,
          train_end: pd.Timestamp, seed: int):
    from sklearn.ensemble import HistGradientBoostingClassifier
    train, cal, valid = rates_from_fit(train, cal, valid)
    model = HistGradientBoostingClassifier(learning_rate=learning_rate, max_depth=max_depth,
            max_iter=iterations, early_stopping=False, random_state=seed)
    model.fit(train[list(columns)].to_numpy(dtype=float), train.y.to_numpy(dtype=float),
              sample_weight=recency_weights(train, train_end, half_life))
    return model.predict_proba(valid[list(columns)].to_numpy(dtype=float))[:, 1], model.predict_proba(cal[list(columns)].to_numpy(dtype=float))[:, 1]


class Platt:
    """Coefficients fit chronological TRAIN calibration probabilities only."""
    def __init__(self):
        from sklearn.linear_model import LogisticRegression
        self.model = LogisticRegression(C=1e6, solver="lbfgs", max_iter=1000, random_state=42)

    @staticmethod
    def log_odds(p: np.ndarray) -> np.ndarray:
        p = np.clip(p, 1e-6, 1-1e-6)
        return np.log(p / (1-p)).reshape(-1, 1)

    def fit(self, p: np.ndarray, y: np.ndarray, weights: np.ndarray):
        if len(np.unique(y)) < 2:
            raise ValueError("Platt TRAIN tail needs both classes")
        self.model.fit(self.log_odds(p), y, sample_weight=weights)
        return self

    def predict(self, p: np.ndarray) -> np.ndarray:
        return self.model.predict_proba(self.log_odds(p))[:, 1]


def run_hgb(args):
    args.long_memory = True
    panel, observed = prepare(args)
    params = protocol(args)
    recorder = Recorder(args, "hgb")
    selected_rows, trials, histories, tail_info = [], [], [], []
    grid = list(product((.05, .1), (3, 5), (100, 300)))
    for k in args.leads:
        columns, half_life = selected_features(k), recency(k)
        predictions = {point: [] for point in grid}
        cal_predictions = {point: [] for point in grid}
        fitted = {point: {} for point in grid}
        folds = list(fold_data(panel, observed, params, k, columns))
        for fold in folds:
            end = pd.Timestamp(params.boundaries[int(fold.fold_id)-1], tz="UTC") - pd.Timedelta(hours=params.embargo_hours)
            tails = chronological_tails(fold.train, end, k, params.embargo_hours)
            tail_info.append({"lead": k, "fold_id": fold.fold_id,
                **{name+"_start": str(frame["T"].min()) for name,frame in tails.items()},
                **{name+"_end": str(frame["T"].max()) for name,frame in tails.items()},
                **{name+"_n": len(frame) for name,frame in tails.items()}})
            for lr, depth in product((.05, .1), (3, 5)):
                chosen, history = select_iterations(tails["core"], tails["stop"], columns, lr, depth, half_life, end, args.seed)
                histories.extend({**row,"lead":k,"fold_id":fold.fold_id,"learning_rate":lr,"max_depth":depth} for row in history)
                cached = {}
                for cap in (100,300):
                    n = chosen[cap]
                    if n not in cached:
                        cached[n] = refit(tails["fit"], tails["cal"], fold.valid, columns, lr, depth, n, half_life, end, args.seed)
                    val_p, cal_p = cached[n]
                    point = (lr,depth,cap)
                    pred = references(fold)
                    pred["p"] = val_p
                    predictions[point].append(pred)
                    cal_predictions[point].append({"p":cal_p,"y":tails["cal"].y.to_numpy(dtype=float),
                        "weights":recency_weights(tails["cal"],end,half_life),"fold_id":fold.fold_id})
                    fitted[point][fold.fold_id] = n
                    trials.append({"lead":k,"fold_id":fold.fold_id,"learning_rate":lr,"max_depth":depth,"max_iter":cap,
                        "chosen_iterations":n,"n":len(pred),"brier":brier(pred.y.to_numpy(),pred.p.to_numpy()),"run_id":recorder.run_id})
            print(f"HGB lead={k} fold={fold.fold_id}: all 8 grid candidates evaluated",flush=True)
        pooled = {point:pd.concat(frames,ignore_index=True) for point,frames in predictions.items()}
        winner = min(grid,key=lambda point:(metric_row(pooled[point])["brier"],point))
        pred = pooled[winner]
        lr,depth,cap = winner
        config = {"features":list(columns),"half_life":"inf" if np.isinf(half_life) else half_life,
                  "learning_rate":lr,"max_depth":depth,"max_iter":cap,"fold_iterations":fitted[winner],
                  "early_stopping":"chronological TRAIN Brier, 10-tree checks, patience 30 trees, tolerance 1e-5",
                  "stopping_tail_days":14,"calibration_tail_days":14,"inner_embargo_hours":25,
                  "refit":"pre-calibration TRAIN after iteration selection", "base_rate_fit":"actual core/refit subset",
                  "calibration":"none", "ECE_trigger":ECE_TRIGGER}
        recorder.log(pred,"hgb",k,config)
        selected_rows.append({"lead":k,"model":"hgb","learning_rate":lr,"max_depth":depth,"max_iter":cap,
                              "half_life":config["half_life"],"features":json.dumps(list(columns)),"ece":metric_row(pred)["ece"],"run_id":recorder.run_id})
        if metric_row(pred)["ece"] > ECE_TRIGGER:
            calibrated = []
            coefficients = {}
            for cal_data in cal_predictions[winner]:
                platt = Platt().fit(cal_data["p"],cal_data["y"],cal_data["weights"])
                subset = pred.loc[pred.fold_id.eq(cal_data["fold_id"])].copy()
                subset["p"] = platt.predict(subset.p.to_numpy())
                calibrated.append(subset)
                coefficients[cal_data["fold_id"]] = {"slope":float(platt.model.coef_[0,0]),"intercept":float(platt.model.intercept_[0])}
            calibration_config = {**config,"calibration":"Platt chronological TRAIN tail","calibration_C":1e6,"calibration_epsilon":1e-6,"fold_calibration_coefficients":coefficients}
            calibrated = pd.concat(calibrated,ignore_index=True)
            recorder.log(calibrated,"hgb_platt",k,calibration_config)
            selected_rows.append({**selected_rows[-1],"model":"hgb_platt","ece":metric_row(calibrated)["ece"]})
    pd.DataFrame(selected_rows).to_csv(OUT / "hgb_selected.csv",index=False)
    pd.DataFrame(trials).to_csv(OUT / "hgb_candidate_scores.csv",index=False)
    pd.DataFrame(histories).to_csv(OUT / "hgb_stopping_history.csv",index=False)
    pd.DataFrame(tail_info).to_csv(OUT / "hgb_train_tails.csv",index=False)
    return recorder.finish("Full 8-point HGB grid at all nine leads. Explicit chronological stopping/calibration TRAIN tails with 25-hour inner gaps; no random split. Raw VALID ECE >0.03 triggers TRAIN-tail Platt, logging both versions.")
