"""Render offline CSV reports with matplotlib; no data collection imports."""

import csv
from datetime import datetime
from pathlib import Path

import numpy as np


def plot_reports(out: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    with (out / "monthly_exact_shares.csv").open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("No monthly comparison rows to plot")
    oblasts = sorted({row["oblast"] for row in rows})
    months = sorted({row["month"] for row in rows})
    heat = np.full((len(oblasts), len(months)), np.nan)
    for row in rows:
        heat[oblasts.index(row["oblast"]), months.index(row["month"])] = float(row["B_minus_volunteer"])
    fig, ax = plt.subplots(figsize=(max(12, len(months) * .28), 8))
    bound = max(.01, float(np.nanmax(np.abs(heat))))
    image = ax.imshow(heat, aspect="auto", cmap="RdBu_r", vmin=-bound, vmax=bound)
    ax.set_yticks(range(len(oblasts)), oblasts)
    ticks = list(range(0, len(months), 3))
    ax.set_xticks(ticks, [months[index] for index in ticks], rotation=60, ha="right")
    ax.set_title("Official B − volunteer: monthly exact coverage share (descriptive)")
    fig.colorbar(image, ax=ax, label="Share difference")
    fig.tight_layout()
    fig.savefig(out / "monthly_exact_difference.png", dpi=160)
    plt.close(fig)
    for oblast in ["Lvivska oblast", "Volynska oblast", "Kharkivska oblast", "Odeska oblast", "Kyiv City"]:
        selected = sorted((row for row in rows if row["oblast"] == oblast), key=lambda row: row["month"])
        if not selected:
            continue
        fig, ax = plt.subplots(figsize=(11, 4))
        for column in ("official_A", "official_B", "volunteer", "volunteer_no_naive"):
            ax.plot([datetime.fromisoformat(row["month"] + "-01") for row in selected],
                    [float(row[column]) for row in selected], label=column)
        ax.set(title=f"{oblast}: monthly exact coverage (descriptive)", ylabel="Exact share", ylim=(0, 1))
        ax.legend(ncol=2)
        fig.autofmt_xdate()
        fig.tight_layout()
        fig.savefig(out / (oblast.replace(" ", "_") + ".png"), dpi=160)
        plt.close(fig)
