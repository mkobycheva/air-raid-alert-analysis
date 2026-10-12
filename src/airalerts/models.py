"""Simple references; every fitted rate/candidate uses the supplied TRAIN only."""

import numpy as np
import pandas as pd


class ReferenceModel:
    def __init__(self, name: str, leads: tuple[int, ...], day_windows: tuple[int, ...],
                 week_windows: tuple[int, ...], alphas: tuple[float, ...]):
        self.name, self.leads = name, leads
        self.day_windows, self.week_windows, self.alphas = day_windows, week_windows, alphas
        self.params: dict[int, dict] = {}
        self.rates: dict[int, pd.Series] = {}
        self.global_rates: dict[int, float] = {}
        self.base_rates: dict[int, pd.Series] = {}

    def fit(self, train: pd.DataFrame) -> "ReferenceModel":
        if train.empty:
            raise ValueError("Cannot fit an empty TRAIN window")
        for k in self.leads:
            y = train[f"y_{k}"].astype(float)
            self.global_rates[k] = float(y.mean())
            self.base_rates[k] = train.groupby("oblast")[f"y_{k}"].mean()
            if self.name == "persistence_prob":
                self.rates[k] = train.groupby(["oblast", "state"])[f"y_{k}"].mean()
            else:
                self.rates[k] = train.groupby("oblast")[f"y_{k}"].mean()
            if self.name in {"seasonal_day", "seasonal_week", "ses"}:
                prefix = {"seasonal_day": "day", "seasonal_week": "week", "ses": "ses"}[self.name]
                candidates = {"day": self.day_windows, "week": self.week_windows, "ses": self.alphas}[prefix]
                columns = [f"ses_{value:g}" if prefix == "ses" else f"{prefix}_{value}_k{k}" for value in candidates]
                loss = [float(np.mean((train[column].to_numpy() - y.to_numpy()) ** 2)) for column in columns]
                position = int(np.argmin(loss))
                self.params[k] = {"column": columns[position], "chosen": candidates[position], "train_brier": loss[position]}
        return self

    def predict_proba(self, rows: pd.DataFrame, lead: int) -> np.ndarray:
        if self.name == "persistence_hard":
            return rows.state.to_numpy(dtype=float)
        if self.name in {"seasonal_day", "seasonal_week", "ses"}:
            return np.clip(rows[self.params[lead]["column"]].to_numpy(dtype=float), 0, 1)
        if self.name == "persistence_prob":
            keys = pd.MultiIndex.from_frame(rows[["oblast", "state"]])
            values = self.rates[lead].reindex(keys).to_numpy(dtype=float)
            fallback = rows.oblast.map(self.base_rates[lead]).fillna(self.global_rates[lead]).to_numpy(dtype=float)
            return np.where(np.isnan(values), fallback, values)
        return rows.oblast.map(self.rates[lead]).fillna(self.global_rates[lead]).to_numpy(dtype=float)
