"""One-lead pooled fold matrices; no identity or calendar predictors."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from airalerts.features import GROUP_A, GROUP_B, GROUP_L
from airalerts.splits import FoldParams, walk_forward_folds


@dataclass
class FoldData:
    fold_id: str
    lead: int
    train: pd.DataFrame
    valid: pd.DataFrame
    features: tuple[str, ...]
    flagged: tuple[str, ...]


def fold_data(panel: pd.DataFrame, observed: pd.DataFrame, params: FoldParams,
              lead: int, columns: tuple[str, ...]):
    """Fit base_rate on TRAIN y_0; flags on TRAIN y_k, independently per fold."""
    if not set(columns) <= set(GROUP_A + GROUP_B + GROUP_L):
        raise ValueError("Only specified Group A/B predictors are permitted")
    if panel["T"].ge(pd.Timestamp("2026-08-01", tz="UTC")).any():
        raise ValueError("Reserved TEST rows are forbidden")
    if observed.duplicated(["oblast", "T"]).any():
        raise ValueError("Observed features must have unique oblast,T keys")
    aligned = panel[["oblast", "T"]].merge(observed, on=["oblast", "T"], how="left", validate="one_to_one")
    if aligned[list(GROUP_A)].isna().any().any():
        raise ValueError("Missing observed feature values")
    for fold_id, train_mask, valid_mask in walk_forward_folds(panel, params, lead):
        baseline_columns = list(dict.fromkeys(["oblast", "T", "state", "y_0", f"y_{lead}", *[c for c in panel if c.startswith("ses_")]]))
        train = panel.loc[train_mask, baseline_columns].copy()
        valid = panel.loc[valid_mask, baseline_columns].copy()
        rates = train.groupby("oblast").y_0.mean()
        target_rates = train.groupby("oblast")[f"y_{lead}"].mean()
        flagged = tuple(target_rates.index[(target_rates < .03) | (target_rates > .95)])
        for target, mask in ((train, train_mask), (valid, valid_mask)):
            for name in GROUP_A + GROUP_B + tuple(c for c in GROUP_L if c in aligned):
                target[name] = target.oblast.map(rates) if name == "base_rate" else aligned.loc[mask, name].to_numpy()
            target["y"] = target[f"y_{lead}"].astype(float)
            if target[list(columns)].isna().any().any():
                raise ValueError("Missing fold predictors")
        yield FoldData(fold_id, lead, train, valid, columns, flagged)


def recency_weights(train: pd.DataFrame, train_end: pd.Timestamp,
                    half_life: float) -> np.ndarray:
    """Age from exclusive end of TRAIN; inf means ordinary unweighted fit."""
    if half_life <= 0 or train["T"].ge(train_end).any():
        raise ValueError("Weights require positive half-life and strictly past TRAIN")
    age = (train_end - train["T"]).dt.total_seconds().to_numpy() / 86400
    return np.ones(len(train)) if np.isinf(half_life) else .5 ** (age / half_life)


class PooledLogistic:
    """L2 logistic probability with TRAIN-only (optionally weighted) scaling."""

    def __init__(self, columns: tuple[str, ...], C: float, seed: int = 42):
        from sklearn.linear_model import LogisticRegression
        from sklearn.preprocessing import StandardScaler
        self.columns, self.C = columns, C
        self.scaler = StandardScaler()
        self.model = LogisticRegression(C=C, penalty="l2", solver="lbfgs", max_iter=1000, random_state=seed)

    def fit(self, train: pd.DataFrame, weights: np.ndarray | None = None) -> "PooledLogistic":
        import warnings
        from sklearn.exceptions import ConvergenceWarning
        x = train[list(self.columns)].to_numpy(dtype=float)
        self.scaler.fit(x, sample_weight=weights)
        with warnings.catch_warnings():
            warnings.simplefilter("error", ConvergenceWarning)
            self.model.fit(self.scaler.transform(x), train.y.to_numpy(dtype=float), sample_weight=weights)
        return self

    def predict_proba(self, rows: pd.DataFrame, lead: int | None = None) -> np.ndarray:
        return self.model.predict_proba(self.scaler.transform(rows[list(self.columns)].to_numpy(dtype=float)))[:, 1]
