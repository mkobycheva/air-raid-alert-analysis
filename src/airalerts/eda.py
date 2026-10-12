"""TRAIN-only daily descriptive STL; never imported by feature/model code."""

from pathlib import Path

import numpy as np
import pandas as pd

from airalerts.grid import exact_share
from airalerts.io import load_official, official_variant
from airalerts.splits import FoldParams, walk_forward_folds


def strength(component: np.ndarray, remainder: np.ndarray) -> float:
    denominator = float(np.var(component + remainder))
    return max(0., 1 - float(np.var(remainder)) / denominator) if denominator > 1e-12 else np.nan


def prepare_eda(panel_path: Path, official_path: Path, out: Path,
                params: FoldParams = FoldParams()) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Choose representatives on first-fold TRAIN, using hourly y_0 rates.

    NATIONAL is SUM of per-region exact alert-hours, not a national OR state.
    Only complete Europe/Kyiv calendar days contained in TRAIN enter STL/ACF.
    """
    panel = pd.read_csv(panel_path, usecols=["oblast", "T", "y_0"])
    panel["T"] = pd.to_datetime(panel["T"], utc=True, format="ISO8601")
    if panel["T"].ge(pd.Timestamp(params.test_start, tz="UTC")).any():
        raise ValueError("EDA panel contains TEST rows")
    out.mkdir(parents=True, exist_ok=True)
    rates = []
    for fold_id, train, _ in walk_forward_folds(panel, params, 0):
        data = panel.loc[train].groupby("oblast").y_0.agg(["mean", "size"]).reset_index()
        data = data.rename(columns={"mean": "base_rate", "size": "n"})
        data["flagged"] = data.base_rate.lt(.03) | data.base_rate.gt(.95)
        data["fold_id"] = fold_id
        data["train_end_exclusive"] = (pd.Timestamp(params.boundaries[int(fold_id) - 1], tz="UTC") - pd.Timedelta(hours=params.embargo_hours)).isoformat()
        rates.append(data)
    all_rates = pd.concat(rates, ignore_index=True)
    all_rates.to_csv(out / "train_base_rates.csv", index=False)
    overview = pd.DataFrame([{"rows": len(panel), "oblasts": panel.oblast.nunique(), "min_T": str(panel["T"].min()),
                              "max_T": str(panel["T"].max()), "embargo_hours": params.embargo_hours}])
    overview.to_csv(out / "panel_overview.csv", index=False)
    first = all_rates.loc[all_rates.fold_id.eq("1")].set_index("oblast")
    groups = {
        "east": ["Dnipropetrovska oblast", "Donetska oblast", "Kharkivska oblast", "Zaporizka oblast", "Sumska oblast"],
        "center": ["Cherkaska oblast", "Kyivska oblast", "Kyiv City", "Kirovohradska oblast", "Poltavska oblast", "Vinnytska oblast", "Zhytomyrska oblast"],
        "west": ["Lvivska oblast", "Volynska oblast", "Zakarpatska oblast", "Rivnenska oblast", "Ternopilska oblast", "Chernivetska oblast", "Ivano-Frankivska oblast", "Khmelnytska oblast"],
    }
    choices = []
    median = float(first.base_rate.median())
    for group, candidates in groups.items():
        available = first.loc[first.index.intersection(candidates)].reset_index()
        if group == "east":
            available = available.sort_values(["base_rate", "oblast"], ascending=[False, True])
        elif group == "west":
            available = available.sort_values(["base_rate", "oblast"])
        else:
            available["distance"] = (available.base_rate - median).abs()
            available = available.sort_values(["distance", "oblast"])
        row = available.iloc[0]
        choices.append({"group": group, "oblast": row.oblast, "base_rate": row.base_rate, "flagged": row.flagged})
    chosen = pd.DataFrame(choices)
    chosen.to_csv(out / "representatives.csv", index=False)
    train_start = pd.Timestamp(params.train_start, tz="UTC")
    train_end = pd.Timestamp(params.boundaries[0], tz="UTC") - pd.Timedelta(hours=params.embargo_hours)
    events = official_variant(load_official(official_path), "B")
    events = events.loc[events.oblast.isin(first.index) & events.started_at.lt(train_end)].copy()
    events["finished_at"] = events.finished_at.clip(upper=train_end)
    a = train_start.tz_convert("Europe/Kyiv").ceil("D")
    b = train_end.tz_convert("Europe/Kyiv").floor("D")
    boundaries = pd.date_range(a, b, freq="D")
    daily = []
    for low, high in zip(boundaries[:-1], boundaries[1:]):
        shares = exact_share(events, low, high).reindex(first.index, fill_value=0)
        hours = shares * (high - low).total_seconds() / 3600
        row = {"day": low.date().isoformat(), "day_hours": (high - low).total_seconds() / 3600,
               "NATIONAL": hours.sum()}
        row.update({oblast: hours[oblast] for oblast in chosen.oblast})
        daily.append(row)
    daily = pd.DataFrame(daily)
    daily.to_csv(out / "train_daily_alert_hours.csv", index=False)
    return daily, chosen


def decompose(daily: pd.DataFrame, chosen: pd.DataFrame, out: Path, period: int = 7,
              seasonal: int = 13) -> pd.DataFrame:
    from statsmodels.tsa.seasonal import STL
    from statsmodels.tsa.stattools import acf

    rows, components = [], []
    for name in ["NATIONAL", *chosen.oblast.tolist()]:
        observed = daily[name].to_numpy(dtype=float)
        result = STL(observed, period=period, seasonal=seasonal, robust=True).fit()
        rows.append({"series": name, "n_days": len(observed), "period_days": period,
                     "F_T": strength(result.trend, result.resid), "F_S": strength(result.seasonal, result.resid)})
        components.append(pd.DataFrame({"day": daily.day, "series": name, "observed": observed,
                                        "trend": result.trend, "seasonal": result.seasonal, "remainder": result.resid}))
    table = pd.DataFrame(rows)
    table.to_csv(out / "stl_strength.csv", index=False)
    pd.concat(components, ignore_index=True).to_csv(out / "stl_components.csv", index=False)
    correlations = acf(daily.NATIONAL.to_numpy(), nlags=28, fft=False)
    pd.DataFrame({"lag_days": np.arange(len(correlations)), "acf": correlations}).to_csv(out / "national_acf.csv", index=False)
    national = table.loc[table.series.eq("NATIONAL")].iloc[0]
    stronger = "trend" if national.F_T >= national.F_S else "weekly seasonal"
    sentences = [
        f"Descriptive, two-sided STL on {int(national.n_days)} complete TRAIN days gives NATIONAL F_T={national.F_T:.4f} and F_S={national.F_S:.4f}.",
        f"The {stronger} component has the larger NATIONAL variance-reduction strength under this decomposition; this is not forecast skill.",
        "The east/center/west representatives were chosen from first-fold TRAIN rates: highest east, center nearest the overall median, and lowest west; their individual strengths are in stl_strength.csv.",
        "STL uses observations on both sides of each date, so its components never enter model features; the supplied December 2025 definition break also limits causal interpretation.",
        "The ACF is for daily national exposure: its lag is in days and is not the hourly forecast lead k.",
    ]
    (out / "stl_description.md").write_text("\n\n".join(sentences) + "\n")
    return table
