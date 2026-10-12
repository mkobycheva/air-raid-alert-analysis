"""Offline steps 3–6 only; no HGB or final-test mode."""

import argparse
from pathlib import Path
from airalerts.panel import DEFAULT_LEADS
from airalerts.ladder import run


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=['prepare', 'A', 'AB', 'recency'], required=True)
    parser.add_argument('--panel',type=Path,default=Path('data/processed/panel.csv.gz'))
    parser.add_argument('--official',type=Path,default=Path('data/raw/official_data_en.csv'))
    parser.add_argument('--train-start',default='2025-12-01')
    parser.add_argument('--fold-boundaries',nargs='+',default=['2026-06-01','2026-06-16','2026-07-01','2026-07-16','2026-08-01'])
    parser.add_argument('--embargo-hours',type=int,default=25)
    parser.add_argument('--leads',nargs='+',type=int,default=list(DEFAULT_LEADS))
    parser.add_argument('--C',nargs='+',type=float,default=[.01,.1,1.,10.])
    parser.add_argument('--half-lives',nargs='+',type=float,default=[14.,30.,60.,float('inf')])
    parser.add_argument('--seed',type=int,default=42)
    parser.add_argument('--bootstrap-samples',type=int,default=300)
    run(parser.parse_args())


if __name__ == '__main__':
    main()
