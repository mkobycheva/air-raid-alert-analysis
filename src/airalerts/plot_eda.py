"""Offline rendering of computed EDA tables; standard-library CSV input."""

import csv
from datetime import datetime
from pathlib import Path

import numpy as np


def plot_eda(out: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    with (out / "stl_components.csv").open() as handle:
        rows = list(csv.DictReader(handle))
    for name in sorted({row["series"] for row in rows}):
        selected = [row for row in rows if row["series"] == name]
        dates = [datetime.fromisoformat(row["day"]) for row in selected]
        fig, axes = plt.subplots(4, 1, sharex=True, figsize=(11, 8))
        for ax, field in zip(axes, ("observed", "trend", "seasonal", "remainder")):
            ax.plot(dates, [float(row[field]) for row in selected], linewidth=1)
            ax.set_ylabel(field)
        axes[0].set_title(name + " — TRAIN only; descriptive, two-sided STL")
        fig.autofmt_xdate()
        fig.tight_layout()
        fig.savefig(out / ("stl_" + name.replace(" ", "_") + ".png"), dpi=150)
        plt.close(fig)
    with (out / "national_acf.csv").open() as handle:
        rows = list(csv.DictReader(handle))
    fig, ax = plt.subplots(figsize=(10, 4))
    lags = np.array([int(row["lag_days"]) for row in rows])
    values = np.array([float(row["acf"]) for row in rows])
    ax.vlines(lags, 0, values)
    ax.scatter(lags, values, s=15)
    ax.axhline(0, color="black", linewidth=.7)
    ax.set(title="NATIONAL TRAIN daily alert-hours ACF — lag is not forecast lead k",
           xlabel="Lag (days)", ylabel="Autocorrelation")
    fig.tight_layout()
    fig.savefig(out / "national_acf.png", dpi=150)
    plt.close(fig)
