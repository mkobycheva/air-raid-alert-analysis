"""Offline descriptive source comparison. Run with PYTHONPATH=src."""

import argparse
from pathlib import Path



def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--api-file", type=Path, default=Path("alerts_in_ua/alerts_month.csv"))
    parser.add_argument("--census-dir", type=Path, default=Path("reports"))
    parser.add_argument("--out", type=Path, default=Path("reports/compare"))
    parser.add_argument("--start", default="2022-03-15")
    parser.add_argument("--end", help="Optional UTC comparison cap")
    parser.add_argument("--no-plots", action="store_true")
    parser.add_argument("--plots-only", action="store_true", help="Render existing comparison CSVs")
    args = parser.parse_args()
    if args.plots_only:
        from airalerts.plot_comparison import plot_reports
        plot_reports(args.out)
    else:
        from airalerts.compare import run_comparison, utc
        run_comparison(args.raw_dir, args.api_file, args.census_dir, args.out, utc(args.start),
                       utc(args.end) if args.end else None, not args.no_plots)


if __name__ == "__main__":
    main()
