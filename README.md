# Air-raid alert analysis

## Setup

Use Python 3.14 on macOS:

```sh
python3.14 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

Obtain the raw CSVs from the MIT-licensed
[Vadimkin/ukrainian-air-raid-sirens-dataset](https://github.com/Vadimkin/ukrainian-air-raid-sirens-dataset).
Clone it outside this repository and copy the two files into `data/raw/`:

```sh
git clone https://github.com/Vadimkin/ukrainian-air-raid-sirens-dataset.git ../ukrainian-air-raid-sirens-dataset
mkdir -p data/raw
cp ../ukrainian-air-raid-sirens-dataset/datasets/official_data_en.csv data/raw/
cp ../ukrainian-air-raid-sirens-dataset/datasets/volunteer_data_en.csv data/raw/
```

Upstream files can change. The checksums below identify this project's current
input snapshots; a later clone may not reproduce these exact bytes.

## Regenerate reports

With the local input snapshots available, run:

```sh
PYTHONPATH=src python3 scripts/run_comparison.py
```

This writes CSV tables, PNG figures and `source_comparison.md` to
`reports/compare/`. To regenerate only figures from existing tables:

```sh
PYTHONPATH=src python3 scripts/run_comparison.py --plots-only
```

The API input is `alerts_in_ua/alerts_month.csv`; if it is unavailable, API
comparisons are skipped. Raw data and API snapshots are gitignored and must be
preserved separately. See [docs/DECISIONS.md](docs/DECISIONS.md) for provenance
and definitions.

## Snapshot provenance and SHA-256

Per project provenance, the official Telegram channel `air_alert_ua` has been
silent since 2026-09-07. The alerts.in.ua snapshot was fetched on 2026-10-11.
Its rolling history means that this historical snapshot cannot be re-downloaded
later; preserve the original file. These are provenance notes, not analysis
results or a new live-channel check.

| File | SHA-256 |
|---|---|
| `data/raw/official_data_en.csv` | `b396f87696243069eec0219880e87dcd642b20beb0a7bae0d0e1f61e1ed20ec4` |
| `data/raw/volunteer_data_en.csv` | `e441ecaa9813c9088e41aa6f137f9917679c9721701c817a97aae3bed470e1d5` |
| `alerts_in_ua/alerts_month.csv` | `e21532d64265454995096b09cd451940f64f8b7b34fa84c609aada416f6073a7` |
