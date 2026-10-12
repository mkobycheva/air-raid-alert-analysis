"""Offline TRAIN-only EDA, with separate compute/render modes."""

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--panel", type=Path, default=Path("data/processed/panel.csv.gz"))
    parser.add_argument("--official", type=Path, default=Path("data/raw/official_data_en.csv"))
    parser.add_argument("--out", type=Path, default=Path("reports/eda"))
    parser.add_argument("--compute-only", action="store_true")
    parser.add_argument("--plots-only", action="store_true")
    args = parser.parse_args()
    if not args.plots_only:
        from airalerts.eda import prepare_eda, decompose
        daily, chosen = prepare_eda(args.panel, args.official, args.out)
        print("TRAIN-selected representatives:\n" + chosen.to_string(index=False))
        print(decompose(daily, chosen, args.out).to_string(index=False))
    if not args.compute_only:
        from airalerts.plot_eda import plot_eda
        plot_eda(args.out)


if __name__ == "__main__":
    main()
