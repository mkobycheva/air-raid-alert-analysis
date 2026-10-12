# Тривожник — air-raid alert forecasting

A retrospective, self-contained viewer of saved forecasts for 24 Ukrainian regions. Open [docs/index.html](docs/index.html) directly, or publish the `docs/` directory with GitHub Pages. The page uses historical data, not live alerts.

## Current state

FINAL evaluation is complete. The frozen configuration is from commit `296573221359a2ce12d9c45e729500980807a71c`. The TEST window is **[2026-08-01 00:00, 2026-09-05 05:00) UTC**; valid forecast-time ranges differ by lead because targets beyond the end are withheld. Lead 0 is a nowcast, 1–6 are primary forecasts, and 12/24 are secondary.

Read [FINAL results](reports/model/final_test.md), [validation and selection](reports/model/validation_summary.md), [source comparison](reports/compare/source_comparison.md), and [decisions and limitations](docs/DECISIONS.md). Do not refit, re-predict or select settings using TEST. `final_config.json` retains its original validation-freeze status fields; FINAL completion is recorded separately in the checkpoint and FINAL report.

## Setup

For core utilities, tests and the viewer, Python 3.14 was used on macOS:

```sh
python3.14 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
PYTHONPATH=src python3 -m pytest
```

The frozen model run used Python 3.12.6, NumPy 1.26.4, pandas 3.0.3 and scikit-learn 1.6.1. The unpinned requirements are not an exact environment lock. Some upstream-parser and machine-learning tests can skip when their optional runtime is unavailable; a green core test run alone does not reproduce FINAL.

## Inputs and provenance

Clone the MIT-licensed [upstream dataset](https://github.com/Vadimkin/ukrainian-air-raid-sirens-dataset) outside this repository, then copy its snapshots:

```sh
git clone https://github.com/Vadimkin/ukrainian-air-raid-sirens-dataset.git ../ukrainian-air-raid-sirens-dataset
mkdir -p data/raw
cp ../ukrainian-air-raid-sirens-dataset/datasets/official_data_en.csv data/raw/
cp ../ukrainian-air-raid-sirens-dataset/datasets/volunteer_data_en.csv data/raw/
```

Upstream files can change: these checksums identify the local snapshots, not every future download.

| File | SHA-256 |
|---|---|
| `data/raw/official_data_en.csv` | `b396f87696243069eec0219880e87dcd642b20beb0a7bae0d0e1f61e1ed20ec4` |
| `data/raw/volunteer_data_en.csv` | `e441ecaa9813c9088e41aa6f137f9917679c9721701c817a97aae3bed470e1d5` |
| `alerts_in_ua/alerts_month.csv` | `e21532d64265454995096b09cd451940f64f8b7b34fa84c609aada416f6073a7` |

Raw data, API snapshots and processed predictions are ignored and must be preserved separately. The alerts.in.ua snapshot was fetched on 2026-10-11; its rolling history cannot reproduce that historical snapshot later. The official channel has been silent since 2026-09-07 according to previously supplied provenance, not a new network check.

The primary target is official **variant B**, the union of oblast+raion intervals; hromada rows are excluded. Sources are compared separately, never merged. Luhanska, Crimea and Sevastopol are not modelled. See DECISIONS for censoring, parser artifacts, definition changes, incomplete neighbours, and limited validation coverage.

## Rebuild the viewer

```sh
PYTHONPATH=src python3 scripts/build_app.py
```

Inputs: ignored `data/processed/predictions/final_test.csv.gz`, FINAL checkpoint, saved `reports/model/final_test_metrics.csv` and `final_test_bootstrap.csv`, frozen config, and the user-supplied root files `geoBoundaries-UKR-ADM1.geojson` and `metadata-geoboundaries-ukr-adm1-geojson.json`. Use `--help` for alternate geometry/metadata paths. The build does not download boundaries or run model code.

The resulting `docs/index.html` contains the data and geometry, works offline, and makes no network requests. It uses a fixed continuous probability colour scale. Prediction mode hides outcomes; actual mode shows the target-hour outcome and dashed large-error outlines. Geometry attribution is included in the footer. The supplied metadata does not independently establish the licence; see DECISIONS.

## Regenerate descriptive reports

With the original snapshots available:

```sh
PYTHONPATH=src python3 scripts/run_comparison.py
PYTHONPATH=src python3 scripts/run_comparison.py --plots-only
PYTHONPATH=src python3 scripts/run_eda.py
```

Comparison outputs go to `reports/compare/`; missing API inputs are skipped. EDA CLI outputs go to `reports/eda/`. The combined `notebooks/00_eda.ipynb` contains historical exploration first, then TRAIN-only descriptive STL/ACF. Earlier exploration overlapped TEST and is not independent validation evidence. STL is two-sided and never a feature.

Model-training and freeze scripts remain as an implementation record, not instructions to restart selection after TEST. `results.csv` is append-only; readers select the latest run per model/fold/lead. Preserve the frozen run and its supporting selection tables. FINAL predictions were made once; subsequent recovery evaluated saved predictions only.

## Repository review

[Cleanup record and file inventory](docs/REPO_REVIEW.md) separate disposable caches and duplicate artifacts from required source, snapshots and evidence. The approved duplicate files, progress summaries and caches have been removed. Some viewer/FINAL source files remain untracked locally although the HTML has been committed: include the required source and reports deliberately before expecting a fresh clone to rebuild. The conversation export has been removed.
