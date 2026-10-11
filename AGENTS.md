# Project: per-oblast air-raid alert forecasting (Ukraine)

Goal: for each oblast, forecast P(alert touches hour h) at forecast time T, evaluated on the latest period. No data leakage.

## Forecast setup
- PRIMARY: each lead 1..6 h ahead as a separate target. Lead 0 is reported separately, never pooled.
- SECONDARY (contrast): leads 12 and 24 h.
- EXTRA metric, only if time allows: event window "any alert in [T, T+W)".
- Do not choose a horizon by test score. Do NOT implement train/val/test splits yet; only prepare data.

## Data decisions (changes go to docs/DECISIONS.md)
- `official` (Telegram air_alert_ua, structured, levels oblast/raion/hromada) is PRIMARY. `volunteer` (eTryvoga, keyword-parsed, oblast level) is a robustness check. Never average or merge them.
- official_data_en.csv has an exact duplicated block: `drop_duplicates()` right after reading (expected 299,275 -> 185,430 rows).
- All timestamps are UTC (= Telegram publication time, not siren time). Convert to Europe/Kyiv only for daily reporting.
- Target: alert(oblast, hour) = 1 iff ANY interval of ANY level in the oblast touches [h, h+1h).
- Exclude Luhanska oblast and Crimea.
- Intervals are written only when closed, so each file is right-censored: trim the last 48 h of every source.
- volunteer `naive` = imputed end (+30 min). official: duration == 3600 s is a heuristic imputation flag (~0.1% of rows).
- Hourly "touch" inflates up to ~3.3x observed; ~1x for saturated oblasts. Compare SOURCES by exact minutes; use the hourly grid only for modelling.
- Do not model alert counts or durations (parser artifacts).

## Leakage rules
- A feature for forecast time T may use only events with started_at <= T. finished_at counts as known only if <= T; otherwise the alert is "ongoing".
- Time-based splits only. Fit anything (scalers, encoders) on the training window only.

## Code rules
- Task 1 needs no network or secrets. Later collect tasks may use the network, but never read, print or write tokens; credentials come from env vars only.
- Never modify data/raw. Inspect files before assuming column names.
- Type hints, small pure functions, pytest tests, no absolute paths.
- Keep the repo minimal: create a file only when the current task needs it.
- Final report after each task: files changed, commands run, test output, what you assumed or could not verify. Do not claim results you did not run.
