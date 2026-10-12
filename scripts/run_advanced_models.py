"""Offline validation steps 6b–8; FINAL is not implemented."""
import argparse
from pathlib import Path
from airalerts.panel import DEFAULT_LEADS


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stage', choices=['long', 'hgb', 'freeze'], required=True)
    p.add_argument('--panel', type=Path, default=Path('data/processed/panel.csv.gz'))
    p.add_argument('--official', type=Path, default=Path('data/raw/official_data_en.csv'))
    p.add_argument('--train-start', default='2025-12-01')
    p.add_argument('--fold-boundaries', nargs='+', default=['2026-06-01','2026-06-16','2026-07-01','2026-07-16','2026-08-01'])
    p.add_argument('--embargo-hours', type=int, default=25)
    p.add_argument('--leads', nargs='+', type=int, default=list(DEFAULT_LEADS))
    p.add_argument('--seed', type=int, default=42)
    p.add_argument('--bootstrap-samples', type=int, default=300)
    args = p.parse_args()
    if args.stage == 'long':
        from airalerts.advanced import run_long
        run_long(args)
    elif args.stage == 'hgb':
        from airalerts.hgb import run_hgb
        run_hgb(args)
    else:
        from airalerts.freeze import run_freeze
        run_freeze(args)


if __name__ == '__main__': main()
