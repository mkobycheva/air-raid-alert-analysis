# Repository review — 2026-10-12

VERIFIED: The candidates below were approved and removed after the initial review. No staging, commits, model runs or network checks. Sizes and git statuses in the inventory describe the pre-cleanup snapshot. This is not a secrets audit.

## Approved removals (completed)

| File / group | Status | Bytes | Proposal and reason |
|---|---|---:|---|
| `eda.ipynb` | tracked | 148,193 | REMOVED: historical cells already embedded in notebooks/00_eda.ipynb. |
| `codex-session-01a12689-cac3-7c03-bdd2-f254e422b7d2.md` | untracked | 1,462,264 | REMOVED: conversation export, not a reproducibility input; contents not inspected. |
| `data/geo/ne_10m_admin_1_states_provinces.geojson` | ignored | 40,726,851 | REMOVED: preliminary boundary download not used by the current builder. |
| `reports/model/step5b_core.md` | tracked | 6,095 | REMOVED: historical progress note; canonical decisions/results remain. |
| `reports/model/steps3_6.md` | tracked | 3,898 | REMOVED: historical progress note; canonical stage reports remain. |
| `reports/model/steps3_6_summary.csv` | tracked | 1,298 | REMOVED: derived progress summary; detailed stage tables remain. |
| `.DS_Store` (1 files) | ignored | 6,148 | REMOVED: disposable OS/runtime cache; regenerates automatically. |
| `__pycache__/` (8 files) | ignored | 153,180 | REMOVED: disposable OS/runtime cache; regenerates automatically. |
| `.pytest_cache/` (4 files) | ignored | 2,661 | REMOVED: disposable OS/runtime cache; regenerates automatically. |

## Keep and inconsistencies

VERIFIED: The HTML is tracked, while viewer/build source and several FINAL source/report files are untracked. Keep and deliberately commit the required implementation and evidence; a fresh clone currently cannot reproduce all local functionality. The conversation export was removed.

VERIFIED: results.csv is append-only evidence, not a disposable duplicate. Preserve it and FINAL metrics/bootstrap/per-oblast tables. Do not truncate logs or rewrite git history as cleanup. Selection tables are read by ladder/freeze/report code; do not remove them just because they are generated.

VERIFIED: reports/census_message_templates.csv is a unique local historical input consumed by comparison. Raw/API snapshots and FINAL predictions/checkpoints are ignored but required or irreplaceable; preserve them outside git. The root geoBoundaries files are the current viewer inputs; their location follows the user’s choice. The unused Natural Earth file is separate.

VERIFIED: README/AGENTS now distinguish completed FINAL from historical validation reports, variant B from the earlier all-level target, and Python 3.14 core testing from the frozen Python 3.12.6 environment. Unpinned requirements remain a reproducibility limitation; no dependency changes were made.

VERIFIED: The frozen config’s validation-only status fields intentionally remain unchanged. The FINAL checkpoint/report record completion. Historical report tables and model artefacts were not recomputed.

VERIFIED: Metadata supplies the geometry source URL but not its licence field. CC BY 4.0 attribution follows the previously specified geoBoundaries source; independent licence verification is outstanding. Channel silence and volunteer-channel provenance are prior user-supplied facts, not fresh network verification.

## Generated outputs — keep by default; optional removal only with regeneration inputs

VERIFIED: Comparison outputs can be regenerated with `PYTHONPATH=src python3 scripts/run_comparison.py`; EDA outputs with `PYTHONPATH=src python3 scripts/run_eda.py`. Model outputs document the frozen experiment: do not rerun training/freeze to replace them after TEST. Existing stage tables and saved predictions are prerequisites for reporting-only regeneration.

| File | Status | Bytes | Recommendation |
|---|---|---:|---|
| `reports/compare/Kharkivska_oblast.png` | tracked | 113,721 | KEEP by default; optional REMOVE of derived output if original inputs are preserved |
| `reports/compare/Kyiv_City.png` | tracked | 84,906 | KEEP by default; optional REMOVE of derived output if original inputs are preserved |
| `reports/compare/Lvivska_oblast.png` | tracked | 75,081 | KEEP by default; optional REMOVE of derived output if original inputs are preserved |
| `reports/compare/Odeska_oblast.png` | tracked | 88,001 | KEEP by default; optional REMOVE of derived output if original inputs are preserved |
| `reports/compare/Volynska_oblast.png` | tracked | 79,865 | KEEP by default; optional REMOVE of derived output if original inputs are preserved |
| `reports/compare/api_alert_overlap.csv` | tracked | 526 | KEEP by default; optional REMOVE of derived output if original inputs are preserved |
| `reports/compare/api_counts.csv` | tracked | 1,063 | KEEP by default; optional REMOVE of derived output if original inputs are preserved |
| `reports/compare/api_fact5_regression.csv` | tracked | 185 | KEEP by default; optional REMOVE of derived output if original inputs are preserved |
| `reports/compare/api_open_counts.csv` | tracked | 614 | KEEP by default; optional REMOVE of derived output if original inputs are preserved |
| `reports/compare/api_red_time_coverage.csv` | tracked | 2,871 | KEEP by default; optional REMOVE of derived output if original inputs are preserved |
| `reports/compare/api_threat_shares.csv` | tracked | 90 | KEEP by default; optional REMOVE of derived output if original inputs are preserved |
| `reports/compare/api_volunteer.csv` | tracked | 29,920 | KEEP by default; optional REMOVE of derived output if original inputs are preserved |
| `reports/compare/census_groups.csv` | tracked | 47 | KEEP by default; optional REMOVE of derived output if original inputs are preserved |
| `reports/compare/census_siren_shares.csv` | tracked | 53 | KEEP by default; optional REMOVE of derived output if original inputs are preserved |
| `reports/compare/excluded_regions.csv` | tracked | 105 | KEEP by default; optional REMOVE of derived output if original inputs are preserved |
| `reports/compare/external_reference.csv` | tracked | 4,191 | KEEP by default; optional REMOVE of derived output if original inputs are preserved |
| `reports/compare/fact3_regression.csv` | tracked | 1,670 | KEEP by default; optional REMOVE of derived output if original inputs are preserved |
| `reports/compare/hromada_drivers.csv` | tracked | 9,884 | KEEP by default; optional REMOVE of derived output if original inputs are preserved |
| `reports/compare/indirect_bridge.csv` | tracked | 5,419 | KEEP by default; optional REMOVE of derived output if original inputs are preserved |
| `reports/compare/inventory.csv` | tracked | 580 | KEEP by default; optional REMOVE of derived output if original inputs are preserved |
| `reports/compare/legacy_census_groups.csv` | tracked | 509 | KEEP by default; optional REMOVE of derived output if original inputs are preserved |
| `reports/compare/legacy_census_siren_shares.csv` | tracked | 188 | KEEP by default; optional REMOVE of derived output if original inputs are preserved |
| `reports/compare/long_counts.csv` | tracked | 482 | KEEP by default; optional REMOVE of derived output if original inputs are preserved |
| `reports/compare/long_top_locations.csv` | tracked | 1,379 | KEEP by default; optional REMOVE of derived output if original inputs are preserved |
| `reports/compare/longest_20.csv` | tracked | 3,408 | KEEP by default; optional REMOVE of derived output if original inputs are preserved |
| `reports/compare/monthly_exact_difference.png` | tracked | 183,464 | KEEP by default; optional REMOVE of derived output if original inputs are preserved |
| `reports/compare/monthly_exact_shares.csv` | tracked | 206,079 | KEEP by default; optional REMOVE of derived output if original inputs are preserved |
| `reports/compare/official_volunteer.csv` | tracked | 188,028 | KEEP by default; optional REMOVE of derived output if original inputs are preserved |
| `reports/compare/source_comparison.md` | tracked | 24,563 | KEEP by default; optional REMOVE of derived output if original inputs are preserved |
| `reports/compare/variants.csv` | tracked | 6,911 | KEEP by default; optional REMOVE of derived output if original inputs are preserved |
| `reports/eda/national_acf.csv` | tracked | 674 | KEEP by default; optional REMOVE of derived output if original inputs are preserved |
| `reports/eda/national_acf.png` | tracked | 32,246 | KEEP by default; optional REMOVE of derived output if original inputs are preserved |
| `reports/eda/panel_overview.csv` | tracked | 104 | KEEP by default; optional REMOVE of derived output if original inputs are preserved |
| `reports/eda/representatives.csv` | tracked | 186 | KEEP by default; optional REMOVE of derived output if original inputs are preserved |
| `reports/eda/stl_Dnipropetrovska_oblast.png` | tracked | 229,882 | KEEP by default; optional REMOVE of derived output if original inputs are preserved |
| `reports/eda/stl_Kirovohradska_oblast.png` | tracked | 246,175 | KEEP by default; optional REMOVE of derived output if original inputs are preserved |
| `reports/eda/stl_NATIONAL.png` | tracked | 222,491 | KEEP by default; optional REMOVE of derived output if original inputs are preserved |
| `reports/eda/stl_Zakarpatska_oblast.png` | tracked | 155,463 | KEEP by default; optional REMOVE of derived output if original inputs are preserved |
| `reports/eda/stl_components.csv` | tracked | 73,750 | KEEP by default; optional REMOVE of derived output if original inputs are preserved |
| `reports/eda/stl_description.md` | tracked | 871 | KEEP by default; optional REMOVE of derived output if original inputs are preserved |
| `reports/eda/stl_strength.csv` | tracked | 259 | KEEP by default; optional REMOVE of derived output if original inputs are preserved |
| `reports/eda/train_base_rates.csv` | tracked | 7,377 | KEEP by default; optional REMOVE of derived output if original inputs are preserved |
| `reports/eda/train_daily_alert_hours.csv` | tracked | 13,484 | KEEP by default; optional REMOVE of derived output if original inputs are preserved |
| `reports/model/AB_bootstrap.csv` | tracked | 34,180 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/AB_calibration.png` | tracked | 409,949 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/AB_candidate_scores.csv` | tracked | 40,739 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/AB_reliability.csv` | tracked | 301,852 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/AB_selected.csv` | tracked | 1,618 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/AB_validation.csv` | tracked | 4,349,026 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/AB_validation.md` | tracked | 6,130 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/A_bootstrap.csv` | tracked | 7,851 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/A_calibration.png` | tracked | 268,176 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/A_candidate_scores.csv` | tracked | 9,207 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/A_reliability.csv` | tracked | 69,340 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/A_selected.csv` | tracked | 363 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/A_validation.csv` | tracked | 1,027,206 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/A_validation.md` | tracked | 1,892 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/ab_selection.csv` | tracked | 1,020 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/best_calibration.png` | tracked | 273,691 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/best_per_oblast.csv` | tracked | 140,170 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/best_reliability.csv` | tracked | 6,601 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/bootstrap.csv` | tracked | 56,734 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/bss_vs_lead.png` | tracked | 156,491 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/chosen_params.csv` | tracked | 26,015 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/comparison_references_bootstrap.csv` | tracked | 45,708 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/comparison_references_reliability.csv` | tracked | 383,958 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/comparison_references_validation.csv` | tracked | 12,359,087 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/comparison_references_validation.md` | tracked | 7,071 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/comparison_table.csv` | tracked | 68,708 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/ensemble_bootstrap.csv` | tracked | 8,790 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/ensemble_candidate_scores.csv` | tracked | 1,668 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/ensemble_reliability.csv` | tracked | 77,424 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/ensemble_selection.csv` | tracked | 1,115 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/ensemble_validation.csv` | tracked | 2,203,272 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/ensemble_validation.md` | tracked | 1,960 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/final_test.md` | untracked | 35,379 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/final_test_bootstrap.csv` | untracked | 47,053 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/final_test_metrics.csv` | untracked | 596,016 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/final_test_per_oblast.csv` | untracked | 36,902 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/frozen_validation.csv` | tracked | 1,250 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/hgb_bootstrap.csv` | tracked | 7,257 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/hgb_calibration.png` | tracked | 266,804 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/hgb_candidate_scores.csv` | tracked | 17,308 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/hgb_reliability.csv` | tracked | 64,338 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/hgb_selected.csv` | tracked | 2,735 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/hgb_stopping_history.csv` | tracked | 49,881 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/hgb_train_tails.csv` | tracked | 8,592 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/hgb_validation.csv` | tracked | 1,629,606 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/hgb_validation.md` | tracked | 1,833 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/long_bootstrap.csv` | tracked | 8,008 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/long_candidate_scores.csv` | tracked | 7,999 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/long_gains.csv` | tracked | 3,433 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/long_reliability.csv` | tracked | 70,930 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/long_selection.csv` | tracked | 1,241 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/long_validation.csv` | tracked | 1,385,601 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/long_validation.md` | tracked | 1,896 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/pooled_inventory.csv` | tracked | 3,720 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/recency_bootstrap.csv` | tracked | 33,651 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/recency_calibration.png` | tracked | 274,208 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/recency_candidate_scores.csv` | tracked | 10,188 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/recency_reliability.csv` | tracked | 298,119 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/recency_selected.csv` | tracked | 1,598 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/recency_selection.csv` | tracked | 1,276 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/recency_validation.csv` | tracked | 4,401,316 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/recency_validation.md` | tracked | 6,117 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/reference_validation.csv` | tracked | 23,496 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/reference_validation.md` | tracked | 17,399 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/reliability.csv` | tracked | 375,426 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/results.csv` | tracked | 71,540,409 | KEEP: frozen experiment evidence / reporting input |
| `reports/model/step5b_core.md` | tracked | 6,095 | REMOVED; see cleanup record above |
| `reports/model/steps3_6.md` | tracked | 3,898 | REMOVED; see cleanup record above |
| `reports/model/steps3_6_summary.csv` | tracked | 1,298 | REMOVED; see cleanup record above |
| `reports/model/validation_summary.md` | tracked | 4,375 | KEEP: frozen experiment evidence / reporting input |

## Required implementation and documents

VERIFIED: Collectors remain provenance/reproduction utilities with synthetic tests; lack of use by the viewer is not evidence that they should be deleted. No source-module removal is proposed beyond the duplicate root notebook.

| File | Status | Bytes | Recommendation |
|---|---|---:|---|
| `.gitignore` | tracked | 398 | KEEP |
| `AGENTS.md` | tracked | 3,176 | KEEP |
| `README.md` | tracked | 5,477 | KEEP |
| `app/template.html` | untracked | 22,672 | KEEP |
| `config/final_config.json` | tracked | 21,728 | KEEP |
| `docs/DECISIONS.md` | tracked | 45,813 | KEEP |
| `docs/index.html` | tracked | 638,196 | KEEP |
| `notebooks/00_eda.ipynb` | tracked | 161,064 | KEEP |
| `notebooks/01_logreg.ipynb` | tracked | 7,040 | KEEP |
| `notebooks/02_logreg_context.ipynb` | tracked | 13,000 | KEEP |
| `notebooks/03_recency.ipynb` | tracked | 12,261 | KEEP |
| `notebooks/04_hgb.ipynb` | tracked | 22,605 | KEEP |
| `notebooks/05_comparison.ipynb` | tracked | 195,493 | KEEP |
| `requirements.txt` | tracked | 150 | KEEP |
| `scripts/build_app.py` | untracked | 2,976 | KEEP |
| `scripts/report_advanced_models.py` | tracked | 9,628 | KEEP |
| `scripts/report_model_ladder.py` | tracked | 7,617 | KEEP |
| `scripts/run_advanced_models.py` | tracked | 1,260 | KEEP |
| `scripts/run_comparison.py` | tracked | 1,230 | KEEP |
| `scripts/run_eda.py` | tracked | 1,062 | KEEP |
| `scripts/run_final.py` | untracked | 434 | KEEP |
| `scripts/run_model_ladder.py` | tracked | 1,232 | KEEP |
| `scripts/run_reference_models.py` | tracked | 11,242 | KEEP |
| `src/airalerts/__init__.py` | tracked | 63 | KEEP |
| `src/airalerts/advanced.py` | tracked | 7,446 | KEEP |
| `src/airalerts/appdata.py` | untracked | 13,074 | KEEP |
| `src/airalerts/collect/__init__.py` | tracked | 70 | KEEP |
| `src/airalerts/collect/alerts_in_ua.py` | tracked | 10,258 | KEEP |
| `src/airalerts/collect/census_message_templates.py` | tracked | 11,098 | KEEP |
| `src/airalerts/collect/topup_official.py` | tracked | 19,169 | KEEP |
| `src/airalerts/compare.py` | tracked | 35,626 | KEEP |
| `src/airalerts/eda.py` | tracked | 6,970 | KEEP |
| `src/airalerts/evaluate.py` | tracked | 6,228 | KEEP |
| `src/airalerts/features.py` | tracked | 10,300 | KEEP |
| `src/airalerts/final.py` | untracked | 21,323 | KEEP |
| `src/airalerts/freeze.py` | tracked | 17,104 | KEEP |
| `src/airalerts/grid.py` | tracked | 5,361 | KEEP |
| `src/airalerts/hgb.py` | tracked | 10,695 | KEEP |
| `src/airalerts/io.py` | tracked | 4,759 | KEEP |
| `src/airalerts/ladder.py` | tracked | 14,481 | KEEP |
| `src/airalerts/models.py` | tracked | 2,709 | KEEP |
| `src/airalerts/neighbors.py` | tracked | 3,735 | KEEP |
| `src/airalerts/panel.py` | tracked | 7,897 | KEEP |
| `src/airalerts/plot_comparison.py` | tracked | 2,253 | KEEP |
| `src/airalerts/plot_eda.py` | tracked | 1,696 | KEEP |
| `src/airalerts/pooled.py` | tracked | 4,052 | KEEP |
| `src/airalerts/splits.py` | tracked | 2,194 | KEEP |
| `tests/test_alerts_in_ua.py` | tracked | 3,873 | KEEP |
| `tests/test_app.py` | untracked | 6,307 | KEEP |
| `tests/test_census_message_templates.py` | tracked | 9,900 | KEEP |
| `tests/test_compare.py` | tracked | 5,727 | KEEP |
| `tests/test_features.py` | tracked | 4,677 | KEEP |
| `tests/test_final.py` | untracked | 4,111 | KEEP |
| `tests/test_freeze.py` | tracked | 1,474 | KEEP |
| `tests/test_grid.py` | tracked | 3,744 | KEEP |
| `tests/test_hgb.py` | tracked | 1,852 | KEEP |
| `tests/test_long_memory.py` | tracked | 2,224 | KEEP |
| `tests/test_pooled.py` | tracked | 5,550 | KEEP |
| `tests/test_reference_models.py` | tracked | 5,374 | KEEP |
| `tests/test_step5b_housekeeping.py` | tracked | 2,006 | KEEP |
| `tests/test_topup.py` | tracked | 12,951 | KEEP |

VERIFIED: The progress reports were removed with user approval; canonical stage reports remain. Cleanup does not shrink existing git history. Virtual-environment caches were excluded; project caches may regenerate.
