# Project: per-oblast air-raid alert forecasting (Ukraine)

## Current scope
- The frozen model and single FINAL evaluation are complete. Preserve config, predictions, logs and metrics. Do not refit, re-predict, retune or choose horizons from TEST without a new explicit instruction.
- Lead 0 is separate; primary leads 1..6; secondary 12/24. Each target is whether an alert touches [T+k, T+k+1h).
- Use existing code. Keep the repository minimal. Document changes in docs/DECISIONS.md.

## Data decisions
- PRIMARY is official variant B: OR over oblast and raion rows, excluding hromada. A and D are sensitivities, not the frozen target.
- Deduplicate official immediately after reading (299,275 → 185,430 rows in the original snapshot).
- Volunteer is an independent robustness source; previously supplied provenance identifies UkraineAlarmSignal. Do not merge or average sources. The CSV alone does not establish channel provenance.
- UTC timestamps are publication times, not necessarily siren times. Use Europe/Kyiv for local reporting.
- Exclude Luhanska, Crimea and Sevastopol; neighbouring modelled oblasts consequently have incomplete geographical context.
- Trim each source at max(started_at) minus 48h; API end is min(max(started_at), fetched_at) minus 48h. Open alerts are excluded from interval maths. Never modify data/raw.
- Volunteer naive ends are imputed; official duration == 3600s is a heuristic artificial-close flag (~0.1%). Do not infer physical alert counts/durations from parser rows.
- Frozen features include union-state starts and elapsed-in-alert; these are state summaries, not raw parser-row counts/durations.
- Compare sources using exact union minutes first; hourly touch inflates shares up to ~3.3x observed, ~1x for saturated oblasts.

## Leakage and evaluation
- At T use started_at <= T; finished_at is known only if <= T, otherwise ongoing. Fit scalers, base rates, parameters and weights on each fold's TRAIN only.
- Four independent June–July 2026 walk-forward folds, TRAIN_START 2025-12-01, common 25h embargo. TEST is [2026-08-01, 2026-09-05 05:00) UTC with lead-specific withheld tails.
- Primary uncertainty uses paired seven-day blocks; day-block results are sensitivity evidence. Results are append-only; use latest_results to exclude stale runs.
- STL/ACF are descriptive only. Earlier exploratory runs overlapped TEST; do not present them as independent validation.
- Retain the frozen HGB chronological stopping/calibration protocol, including its shorter fitting window. Architecture comparisons are not perfectly controlled.

## Code and reporting
- No secrets in code, files, output or tests; collectors accept credentials only from environment variables. No network unless the current task permits it.
- Type hints, small pure functions, synthetic offline tests, no absolute paths. Inspect inputs before assuming schema.
- The viewer reads saved TEST numbers only. It has no model/backend or browser network requests; current UI uses a continuous fixed scale.
- Final reports list changed files, commands, test output, assumptions and unverified items. Mark evidence VERIFIED or HYPOTHESIS; never claim unrun results.
