# Data decisions

## Current status and reading this log

VERIFIED: FINAL is complete, run `final-20261012T142247472660`, frozen commit `296573221359a2ce12d9c45e729500980807a71c`; see [FINAL report](../reports/model/final_test.md). No new modelling was run during repository organisation. The frozen config's original validation-only status is intentionally preserved; it is not the completion record.

VERIFIED: Entries below are chronological snapshots. Earlier all-level targets were superseded by variant B; max(finished_at) trimming by max(started_at)-48h; panel defaults by the specified A/B/L features; day-block primary intervals by seven-day blocks. Earlier “TEST not evaluated” and “stop before HGB” statements describe their historical stages. The seven-bin viewer palette was subsequently replaced, at user request, by a fixed continuous darker blue scale and the title “Тривожник”.

VERIFIED: The combined notebook preserves historical exploration before TRAIN-only STL. The duplicate root eda.ipynb was removed after review; its historical cells remain in the combined notebook. Earlier exploration overlapped TEST; it is not independent validation. HGB retains its frozen chronological tails even without calibration, so its fitting freshness differs from logistic regression.

VERIFIED: Neighbours were confirmed by the user. Luhanska and Crimea are absent from the panel: Donetska, Kharkivska and Khersonska have fewer panel neighbours than geographically. Calendar ablation, rolling refit and robustness experiments remain deferred.

VERIFIED: Repository review and approved cleanup are in [REPO_REVIEW.md](REPO_REVIEW.md). The approved candidates have now been removed. Source, generated evidence and irreplaceable snapshots are distinguished there. Historical numeric tables have not been changed.


## 2026-10-10 — Raw data provenance and storage

- VERIFIED (user-supplied provenance): The supplied CSVs are from [Vadimkin/ukrainian-air-raid-sirens-dataset](https://github.com/Vadimkin/ukrainian-air-raid-sirens-dataset). The upstream repository identifies its license as MIT. Local files were not compared byte-for-byte against a specific upstream commit; their snapshot revisions are unverified.
- VERIFIED: Both raw CSVs were moved with plain `mv` from the repository root to `data/raw`; neither was staged or committed.
- VERIFIED: `data/raw/official_data_en.csv` is 31,025,633 bytes: 299,275 raw rows, 185,430 after exact deduplication.
- VERIFIED: `data/raw/volunteer_data_en.csv` is 8,892,014 bytes: 115,793 raw rows and 115,793 exact unique rows; the loader retains all rows.
- VERIFIED: Raw CSVs are not committed. Analysis reads them without modifying their contents. No new interval-length or coverage-threshold exclusion rule was adopted.
- VERIFIED: The regression end is floored to the hour after choosing the earlier of the independently trimmed source ends. General grid behavior for partial hours remains available.
- VERIFIED (historical): The standalone audit script used `data/raw` and has since been removed. Current reports are regenerated with `PYTHONPATH=src python3 scripts/run_comparison.py`.
- HYPOTHESIS: Long official intervals could reflect persistent local alerts, missing closures, or parser behavior. Coverage differences alone do not establish the cause, so this audit does not drop them.

## Task 1b audit — historical results

VERIFIED (historical): These results were produced by a removed script. They retain the original windows and max(finished_at) tail convention used at that time; they are not current comparison outputs.

VERIFIED: All timestamps below are UTC.

VERIFIED: Interval audit window is [2026-02-01 00:00:00+00:00, 2026-09-05 05:39:33+00:00).

VERIFIED: Regression window is [2026-02-01 00:00:00+00:00, 2026-09-05 05:00:00+00:00).

VERIFIED: Source ends use max(finished_at) before exclusions; each source is trimmed independently.

VERIFIED: Long-interval counts and rankings include intervals touching the audit window; durations are full, unclipped durations. Missing count-table rows mean zero. Luhanska statistics use the full loaded sources.

### VERIFIED: Local raw files

```text
   source    bytes  raw_rows  exact_unique_rows  loaded_rows  git_tracked
 official 31025633    299275             185430       185430        False
volunteer  8892014    115793             115793       115793        False
```

### VERIFIED: Official >24 h by oblast × level (443 total)

```text
           oblast_name  oblast  raion  hromada
   Chernihivska oblast       0      6        0
Dnipropetrovska oblast       0     16       52
       Donetska oblast       0    264       25
     Kharkivska oblast       0      9        1
  Kirovohradska oblast       0      3        0
        Kyivska oblast       0      4        0
         Sumska oblast       0      6        0
      Zaporizka oblast       0     55        2
```

### VERIFIED: Ten longest official intervals touching the window

```text
                oblast             raion                                          hromada   level                started_at               finished_at   duration_days
       Donetska oblast  Pokrovskyi raion                   Pokrovska terytorialna hromada hromada 2026-07-26 14:38:44+00:00 2026-08-29 04:17:56+00:00 33.568888888889
Dnipropetrovska oblast Nikopolskyi raion         Chervonohryhorivska terytorialna hromada hromada 2026-03-23 21:53:07+00:00 2026-04-19 05:12:29+00:00 26.305115740741
Dnipropetrovska oblast Nikopolskyi raion         Chervonohryhorivska terytorialna hromada hromada 2026-03-03 20:50:20+00:00 2026-03-23 17:54:21+00:00 19.877789351852
Dnipropetrovska oblast Nikopolskyi raion         Chervonohryhorivska terytorialna hromada hromada 2026-02-21 09:46:42+00:00 2026-03-02 17:20:09+00:00  9.314895833333
Dnipropetrovska oblast Nikopolskyi raion         Chervonohryhorivska terytorialna hromada hromada 2026-02-05 20:08:27+00:00 2026-02-14 07:37:42+00:00  8.478645833333
Dnipropetrovska oblast Nikopolskyi raion m. Marhanets ta Marhanetska terytorialna hromada hromada 2026-05-12 08:48:04+00:00 2026-05-20 05:28:02+00:00  7.861087962963
Dnipropetrovska oblast Nikopolskyi raion         Chervonohryhorivska terytorialna hromada hromada 2026-02-14 12:15:08+00:00 2026-02-21 09:39:05+00:00  6.891631944444
Dnipropetrovska oblast Nikopolskyi raion         Chervonohryhorivska terytorialna hromada hromada 2026-01-30 12:48:19+00:00 2026-02-05 16:04:11+00:00  6.136018518519
Dnipropetrovska oblast Nikopolskyi raion m. Marhanets ta Marhanetska terytorialna hromada hromada 2026-08-28 05:42:26+00:00 2026-09-03 05:24:58+00:00  5.987870370370
Dnipropetrovska oblast Nikopolskyi raion m. Marhanets ta Marhanetska terytorialna hromada hromada 2026-07-24 06:05:48+00:00 2026-07-30 05:26:36+00:00  5.972777777778
```

### VERIFIED: Official exact shares, original window (fractions; Luhanska excluded)

```text
                 oblast  all_intervals  intervals_le24h
       Cherkaska oblast 0.126145567363   0.126145567363
    Chernihivska oblast 0.682931329305   0.660758710712
    Chernivetska oblast 0.018017346783   0.018017346783
 Dnipropetrovska oblast 0.999047357691   0.951534871189
        Donetska oblast 0.962487688525   0.747793381636
Ivano-Frankivska oblast 0.012124324371   0.012124324371
      Kharkivska oblast 0.881911962427   0.861750608435
      Khersonska oblast 0.292898275861   0.292898275861
     Khmelnytska oblast 0.027626573421   0.027626573421
   Kirovohradska oblast 0.184165380589   0.164068524517
              Kyiv City 0.065996894572   0.065996894572
         Kyivska oblast 0.198109723862   0.177942910295
         Lvivska oblast 0.011546251726   0.011546251726
     Mykolaivska oblast 0.249864888901   0.249864888901
          Odeska oblast 0.208163531185   0.208163531185
       Poltavska oblast 0.351336549451   0.351336549451
       Rivnenska oblast 0.035335172140   0.035335172140
          Sumska oblast 0.843024159208   0.821110121072
     Ternopilska oblast 0.015778332264   0.015778332264
       Vinnytska oblast 0.051090435023   0.051090435023
        Volynska oblast 0.016340079709   0.016340079709
     Zakarpatska oblast 0.008956432752   0.008956432752
       Zaporizka oblast 0.832308672808   0.781266624607
     Zhytomyrska oblast 0.085218184688   0.085218184688
```

VERIFIED: The ≤24 h column is a sensitivity comparison only; source intervals are not removed or rewritten.

### VERIFIED: Luhanska, full source

```text
   source  rows            min_started_at            max_started_at      max_duration_s  max_duration_days  gt24h
 official     1 2022-03-24 11:28:27+00:00 2022-03-24 11:28:27+00:00 316413.000000000000     3.662187500000      1
volunteer     3 2022-02-28 06:09:16+00:00 2022-04-04 16:46:15+00:00   1800.000000000000     0.020833333333      0
```

### VERIFIED: Regression comparison (fractions)

```text
   source                 oblast  hourly_before  hourly_floored   exact_before  exact_floored  hourly_changed  exact_changed
 official         Lvivska oblast 0.024084778420  0.024089419927 0.011546251726 0.011547718464            True           True
 official Dnipropetrovska oblast 0.999807321773  0.999807284641 0.999047357691 0.999047236676            True           True
 official              Kyiv City 0.135838150289  0.135671613028 0.065996894572 0.065878246718            True           True
volunteer         Lvivska oblast 0.166088631985  0.166120639815 0.066449343467 0.066457784630            True           True
volunteer Dnipropetrovska oblast 0.610982658960  0.611100404702 0.183127847242 0.183151110255            True           True
volunteer              Kyiv City 0.136416184971  0.136249759106 0.048061334364 0.047940408128            True           True
```

### VERIFIED: Descriptive extremes, floored window (Luhanska excluded)

VERIFIED: official >95%: Dnipropetrovska oblast=99.904723667587%, Donetska oblast=96.248292327787%

VERIFIED: official <3%: Chernivetska oblast=1.801963555384%, Ivano-Frankivska oblast=1.212586454252%, Khmelnytska oblast=2.762157127256%, Lvivska oblast=1.154771846427%, Ternopilska oblast=1.578033660949%, Volynska oblast=1.634215541423%, Zakarpatska oblast=0.895757050170%

VERIFIED: volunteer >95%: none

VERIFIED: volunteer <3%: Ivano-Frankivska oblast=0.836020641956%, Rivnenska oblast=2.044115757693%, Vinnytska oblast=2.480744523672%

VERIFIED: No coverage-threshold exclusions were applied.

VERIFIED: Official-only oblast names: [].

VERIFIED: Volunteer-only oblast names: [].

VERIFIED: Luhanska oblast present in both sources: True. Full name sets contain no Crimea entry.

## 2026-10-10 — Task 2 official top-up implementation; collection not run

- VERIFIED: Added `diagnose` and `collect` modes that call the upstream parser without copying its parsing logic. The upstream active-alert pickle is copied into memory; its last-id sidecar is read separately. The local checkpoint holds active alerts and the last id, never Telegram credentials or a client.
- VERIFIED: No messages or intervals were collected. Collected date range and last fetched id are unavailable. Original id 338380 and 33 unclosed alerts remain supplied context, not newly measured results.
- VERIFIED: `UPSTREAM_DIR`, `TG_API_ID`, `TG_API_HASH`, and `TG_SESSION` are missing. Live diagnostics, collection, upstream parser tests and real post-collection metrics could not run. Telegram network access was not tested; missing configuration does not establish channel silence or a format change.
- VERIFIED: Offline verification: 27 passed, 5 upstream tests skipped. Tests cover ordering, idempotency, deduplication, interrupted saves, FloodWait retries, read-only diagnosis and both hard stops. CSV commits before state; crash replay deduplicates. A checkpoint without its CSV is refused. Collectors must run sequentially.
- VERIFIED: Collection applies no 48 h trim. Descriptive level-share comparison uses deduplicated history starts in the two calendar months ending at max(finished_at); differences above 10 percentage points are flagged without changing exclusions. The state output is gitignored.
- HYPOTHESIS: A changed message format or location vocabulary could explain majority rejection, if observed; there is no live evidence yet. After a configured run, record actual dates, last id, metrics and any evidenced format change here.

## Target definition: official, oblast+raion rows only (variant B). Evidence: template census of channel air_alert_ua. 2026-03-01..09-08: raion/oblast activations are ~100% 'Повітряна тривога'; hromada activations are 52% sirens and 48% threats (artillery, UAV, KAB, ballistic, missile). 2024-Q1: 1,168/1,169 hromada activations are artillery threats. Zaporizhzhia-city threat posts start 2026-06-22..25 (definition break inside variant A). Known limitations: 406 raion-level 'end of KAB threat' posts (~1% of raion deactivations) can close an active siren early; city-level sirens of Kharkiv/Zaporizhzhia (hromada rows) are excluded. Variants A and D are sensitivities.

## 2026-10-11 — Task 3 comparison conventions

- The current tail rule supersedes the earlier max(finished_at) audit convention: valid_end = max(started_at) − 48 h, or min(max(started_at), max(fetched_at)) − 48 h for API snapshots. Compute before all level/region/naive filters; clip at pair endpoints. Earlier Task 1b tables above are historical, not regenerated.
- Primary official definition B retains oblast and raion rows; A, C and D remain separate descriptive definition checks. Open API alerts and zero-duration intervals are excluded from interval coverage. Adjoining half-open intervals remain separate episodes; exact union time is unaffected.
- The API loader shares the collector UID resolver and preserves raw metadata. Local snapshots put raion IDs in location_oblast_uid, so the loader uses the supplied oblast name or corroborated queried_uid, with a recorded resolution method. Unknown regions without a usable fallback raise. Partial API coverage is reported and absent oblasts are never filled as zero.
- The user-supplied volunteer channel is UkraineAlarmSignal. Earlier eTryvoga provenance in AGENTS.md/docs conflicts with that supplied fact; the CSV itself cannot identify its channel. No network validation is attempted.
- All source comparisons are descriptive and separate. API yellow-as-threat remains a hypothesis; both API-ALL and API-RED are reported without relabelling yellow rows. No targets, splits, features, models or forecast evaluation are created.

## Task 3 verification on local files

- The supplied official row-count and exact-share regressions match (185,430 deduplicated rows; see reports/compare/fact3_regression.csv). The reference regression uses its stated untrimmed 2026-02-01..2026-09-07 window; comparison tables use the new trimmed endpoint 2026-09-05 05:28:22 UTC.
- During this task, an already-running local API fetch replaced the initial 188-row file. The final snapshot has 16,532 rows, 25 oblasts (24 after excluding Luhanska), 70 open alerts, and raion/city/hromada/oblast rows. Lvivska+Volynska still match the earlier 188 raion rows (155 yellow, 33 red). Three starts exceed the stored pre-request fetched_at; the requested fetched_at cap is used conservatively. All threat_types in this snapshot are empty.
- Clear collector fixes: preserve an empty CSV schema; parse mixed ISO8601 precisions; handle null threat_type values; refuse missing ids or invalid starts; retain the latest queried duplicate-id observation; record fetched_at at completion; honor numeric Retry-After on 429. Bearer auth and the 31-second spacing are retained, not validated against a live endpoint. The collector was not run. The loader records fallback resolution for the API's mislabelled location_oblast_uid values.
- The API comparison archive boundary is assumed to be fetched_at minus 30 days; old starts of long-lived alerts do not expand month_ago archive coverage backwards. Official/volunteer windows and API windows in the INDIRECT table do not overlap. No color semantics are inferred.
- Only the undated 2024-Q1 census exists locally: 13,127 total messages, 1,168 artillery activations out of 1,169 hromada activations. Date-ranged 2026 census aggregation is skipped; the 2026 counts/break and live channel silence remain supplied context rather than newly verified evidence.
- Python 3.14 runs the calculations and tests. PNGs were rendered offline using cached Python 3.13 matplotlib dependencies because matplotlib is absent from the 3.14 environment. No dependencies were downloaded, no secrets were used, and raw source files were not modified by this work.

## Task 5A — parameterised reference validation protocol

- Current task authorises panels, targets and validation folds, superseding the earlier preparation-only restriction. Defaults are configurable parameters, not conclusions selected by test scores. Official definition defaults to B (oblast+raion). Supplied project context: air_alert_ua has been silent since 2026-09-07; no top-up is possible. No channel/network check is performed here.
- Forecast T is a whole UTC hour. Only events started_at <= T contribute observations; finishes count as known only when <= T. Otherwise the alert is ongoing. The last completed observation hour is [T−1h,T). As-of past shares use exact interval-union time, not inflated hourly touch rates. No event counts or event durations are features; nationwide state counts oblasts, not events.
- y_k is variant-B interval touch of [T+k,T+k+1h). Default leads: PRIMARY 1..6 separately; 0 separately, never pooled with PRIMARY; SECONDARY 12 and 24. Panel labels whose target hour ends after the available validation boundary are missing, not fetched from TEST. Input rows with genuinely unknown ends conservatively have unsettled labels withheld.
- TRAIN_START defaults to 2025-12-01. Default walk-forward T windows: [2026-06-01,06-16), [06-16,07-01), [07-01,07-16), [07-16,08-01). For lead k, TRAIN T is [TRAIN_START,fold_start), additionally requiring T+k+1h <= fold_start. Evaluation T can target the next internal validation fold, but never beyond the final validation boundary. Guard rejects evaluation after the earlier of configured test_start and this stage’s default 2026-08-01 boundary unless final_test=True; this runner provides no such flag and independently caps the panel/evaluation at 2026-08-01.
- Planned TEST = [2026-08-01, independently trimmed source end). It is not used in Task 5A. Planned final protocol: choose everything on validation folds, refit before 2026-08-01 using the selected hyperparameters and embargo, then evaluate TEST once. No final refit or test evaluation is run here.
- Limitation: approximately 0.1% of official rows have heuristic artificial ends with duration == 3600 s, created when a restart occurs more than 3 h later. Such an alert could still look ongoing at T in the live stream. The history does not expose when the synthetic closure was inferred; this is not corrected.
- Disclosure: earlier exploratory horizon/profile runs used a window overlapping planned TEST. Those design decisions are therefore re-checked on walk-forward folds; the later TEST cannot be described as wholly untouched by prior exploration.
- Feature defaults: prior-hour touch lags 1..6; exact shares over 6h/24h/7d/28d; hours since the last known closed interval capped at 72 (72 if none; a different ongoing interval does not erase the last known close); national oblast state count; Europe/Kyiv hour/weekday sin/cos. Fixed historical context warms up the largest rolling candidate (default 56 days). Climatology/persistence rates, seasonal candidate and SES alpha fit TRAIN only, separately by lead. Seasonal candidates default to 7/14/28 elapsed days and 4/8 elapsed weeks, matching Kyiv hour/day-of-week; SES candidates .01/.05/.1/.3/.6 use the last completed hourly bit and no trend/season. Initial SES level is its first warmup observation. During validation, profiles and SES update causally with already observed hours; rates/window/alpha are not refitted on evaluation labels. N/M/alpha are selected by TRAIN Brier, not validation outcomes.
- Reporting defaults: 10 ECE bins, seed 42, 300 paired UTC-day bootstrap samples; flags TRAIN positive rates <3% or >95%, by lead/fold. Pooled BSS uses pooled squared errors. results.csv CI columns refer to climatology; bootstrap.csv also records persistence-reference CIs. Undefined reference Brier or empty scopes produce missing values. Logs append via one writer; summary/calibration/parameter files describe the latest run. Source/input fingerprints and dirty-worktree status supplement git_commit provenance.
- Offline pyarrow installation was attempted with --no-index and unavailable. Parquet dependency is listed; this environment saves panel and predictions as deterministic csv.gz in gitignored data/processed instead. No raw files are modified and no secrets/network are used.

## Task 5B — steps 0–2; stop for neighbor review

- VERIFIED: The common configurable embargo is now 25 hours for all leads, superseding 5A's lead-specific 1..25-hour target-end rule. Each independent fold fits on T in [TRAIN_START, valid_start−25h), also checking target-hour end <= valid_start. With the exclusive cutoff and hourly timestamps, the latest TRAIN T is 26 hours before VALID. TEST remains reserved; no TEST forecasts, labels, selection or evaluation were used. Leads remain separate, including 0. No resampling.
- VERIFIED: SES already existed: ETS(A,N,N), alpha selected separately per lead/fold by TRAIN Brier over .01/.05/.1/.3/.6. The validation rerun adds SES-reference BSS. Paired circular moving 7-day UTC blocks are the primary bootstrap (seed 42, 300 samples); 1-day blocks are a sensitivity. The one-time additive results.csv schema migration appends an empty bss_vs_ses cell to legacy records; all 28,080 legacy records retain their original 21 field values and order (verified by SHA-256). New records append. latest_results selects the latest run_id per (model,fold_id,lead) by created_at, breaking ties by append position, retaining its scopes and ignoring stale runs without deleting them.
- VERIFIED: Reference run 3157b3124f2a6925 uses 25-hour embargo and seven-day CIs; actual metrics, per-fold spread, flags and reference/sensitivity CIs are in reports/model/reference_validation.csv, results.csv and bootstrap.csv. For ALL at lead 1, BSS vs climatology is 0.06002 for persistence_prob and 0.05739 for SES; at lead 6 it is 0.01079 and 0.04850. These are validation descriptions, not a final-model choice.
- VERIFIED: No notebooks/00_eda.ipynb existed; it is created, leaving the existing root eda.ipynb intact. STL uses 180 complete Europe/Kyiv days in first-fold TRAIN, daily exact union hours per region; NATIONAL sums 24 regions including Kyiv City rather than ORing nationally. Robust weekly STL uses period=7 days, seasonal=13. First-fold TRAIN chooses highest eastern rate (Dnipropetrovska, 0.95418), central nearest overall median (Kirovohradska, 0.26341), lowest western rate (Zakarpatska, 0.02694). NATIONAL F_T=0.14525, F_S=0.00000. Zero component-plus-remainder variance gives an undefined strength. All decomposition/ACF output is descriptive and two-sided; no components enter features. ACF daily lag is not forecast lead k.
- VERIFIED: Group A/B features reuse variant B, episodes and exact_share. Unknown/future ends are masked before interval calculations. Hours since end is zero while active, otherwise capped at 168; never_alerted distinguishes no observed alert from an old ended alert. elapsed_in_alert measures the current continuous oblast-union episode. starts_24h counts oblast union transitions in (T−24h,T], not parser row starts; overlapping and abutting rows form one continuous activation. This requested state-age/start feature set supersedes 5A's blanket no-count/no-duration feature restriction for this task. No calendar fields are added. base_rate is TRAIN hourly y_0 mean, frozen per fold; context uses causal panel state/share_6h at T, and neighbors have equal weights.
- VERIFIED: The explicit neighbor dict in src/airalerts/neighbors.py matches all 24 panel names, is symmetric and has no self-links. Kyiv City links to enclosing Kyivska; Luhanska/Crimea are excluded. No correlation-derived edges. Synthetic tests perturb strictly future panel rows and events, mask future finishes, and verify identical features; they cover ongoing alerts, state age, caps, overlapping/abutting intervals and hromada exclusion. Step 2 produced no model-validation scores. Steps 3 onward await human neighbor review.
- HYPOTHESIS / NEEDS HUMAN REVIEW: The hand-written adjacency represents shared administrative borders correctly. Symmetry and exact names are checked; geographic correctness is not independently verified here.
- VERIFIED: Offline computation used installed Python 3.12 statsmodels; rendering used cached Python 3.13 matplotlib. Tests/core checks ran on Python 3.14. No dependency downloads, credential access or raw modifications. Statsmodels/matplotlib execution on Python 3.14 is unverified in this environment because those packages are absent there.
- Supplied limitations carried forward (not newly established here): ~0.1% of official rows are artificially closed (duration==3600 s); closure inference time is unavailable and uncorrected. Earlier exploratory runs overlapped TEST. December 2025 introduces a raion definition break: oblast alert means any raion. The neighbor dict is hand-written. Validation covers only June–July.

## Deferred / optional (not done)

- Ensemble was originally deferred; subsequently authorised and completed in Step 8 below.
- Calendar ablation: add hour/weekday features to the best model; only on explicit request.
- Rolling refit versus fixed fit: validation fixed before June 1 versus refit every 15 days. If rolling improves outside the block-bootstrap CI, final uses past-only 15-day refits; only on explicit request.
- Robustness: apply frozen settings without retuning to targets A/D and TRAIN_START=2025-07-01, validation only; only on explicit request.

## Task 5B continuation — confirmed geography and exact feature contract

- VERIFIED (user confirmation): the hand-written neighbor dictionary is accepted. Luhanska and Crimea are intentionally outside the panel, so Donetska, Kharkivska and Khersonska have fewer in-panel neighbors than geographic neighbors. Context averages use only the listed in-panel neighbors; no excluded-region value is imputed.
- VERIFIED: Revised Group A is exactly active_now, hours_since_end (cap 168), elapsed_in_alert, share_1h, share_6h, share_24h, share_168h, starts_24h. Group B is exactly base_rate, neighbor_share_now, neighbor_share_6h, national_active_count. The earlier extra never_alerted flag was removed to match the revised eight-plus-four list. Its earlier justification was the original flag request; it is no longer a predictor. Old panel lags/calendar/28-day shares/cap-72 fields are not logistic inputs.
- VERIFIED: Vectorized features reuse variant B, interval episodes and panel prefix coverage; synthetic tests compare them with the original as-of calculation and perturb future intervals/panel rows. One-lead fold matrices pool all 24 regions, without identity encoding. base_rate fits TRAIN y_0 only; flags use TRAIN y_k. All leads use the common 25-hour embargo and independent fold fits. No TEST target hour is used.
- VERIFIED: Historical root eda.ipynb cells are preserved first in notebooks/00_eda.ipynb, followed by the TRAIN-only STL section. Historical exploration is explicitly marked as such, was not executed again and is not validation/model-selection evidence. Root eda.ipynb was retained at that stage; it was later removed as a reviewed duplicate.
- Decision: choose one C per lead by pooled VALID Brier across the four independent folds, rather than picking each fold's local minimum. Candidate grid is {0.01,0.1,1,10}; no class resampling. StandardScaler and logistic coefficients fit current TRAIN only. Reported validation-selected scores are selection descriptions, not unbiased final performance.
- Decision: context is retained per lead only if its paired seven-day-block relative Brier gain over A has lower 95% bound >0. Otherwise record no evidence of improvement and use A for recency. Ablations add neighbor-only, national-only or base-rate-only context to A. Recency fixes the selected base model/C and chooses half-life {14,30,60,inf} on pooled VALID, with age from exclusive TRAIN end; both scaler and logistic loss use the weights. No HGB/final/optional task is run.

## Task 5B — steps 4–6 results (validation-selected, no FINAL)

- VERIFIED: Step 4 logreg_A pooled BSS versus climatology: lead 0 separately 0.43616; leads 1/6 0.09006/0.03069; leads 12/24 0.01712/0.00974. One C per lead selected on pooled VALID Brier, scaler and logistic coefficients fitted on each independent TRAIN. Per-oblast metrics, TRAIN flags, ECE and three reference BSS values append to results.csv.
- VERIFIED: Step 5 full logreg_AB BSS versus climatology at 1/6 is 0.09940/0.03981. Paired seven-day-block gain over A has positive lower bound at leads 1–6. At 0,12,24: no evidence of improvement; these leads exclude all Group B features in recency. Neighbor-only/national-only/base-rate-only ablations are in AB_validation.csv and notebook 02. Context does not enter as an identity one-hot.
- VERIFIED: Step 6 selected half-lives: 0→60d, 1→14d, 2→14d, 3→30d, 4→30d, 5→30d, 6→14d, 12→60d, 24→inf. Fix the step 4/5 chosen C and base model per lead, then choose half-life by pooled VALID Brier. Weight both scaler and logistic loss; weights are not normalized, so effective penalty strength can also change. base_rate remains unweighted TRAIN y_0 mean. This is a stated implementation choice, not an extra tuning grid.
- VERIFIED: Selected recency BSS versus climatology at 1/6 is 0.10409/0.04349. Recency gain CIs are positive for 1–6, cross zero at 0/12, and equal zero for unchanged 24; no improvement claim at 0/12/24. SES still has lower Brier at leads 5,6,12,24. The validation-selected numbers and CIs do not account for hyperparameter-selection or multiple-comparison uncertainty; they are not unbiased final-test estimates.
- VERIFIED: Full Python 3.14 suite: 84 passed, 14 skipped. Forecasting suite on installed Python 3.12 sklearn: 21 passed, including two model tests skipped in 3.14. Twelve remaining skips are pre-existing unavailable upstream parser tests. All specified nine leads and the full grids ran; no runtime shrinkage. No network/secrets/raw modifications. HGB, optional tasks, final configuration and TEST evaluation were not run. The former reports/model/steps3_6.md progress note was later removed; canonical A/AB/recency reports and notebooks 01–03 remain.

## Steps 6b–8 protocol (validation only; FINAL not authorised)

- Fixed long-memory features: share_672h is exact union exposure during [T−672h,T); ewma_14d is the EWMA of completed hourly touch indicators, half-life 336 hours, fixed zero initialization at 2022-03-15 UTC. These parameters are not fitted or searched. Starts after T contribute nothing; unknown/future ends mean ongoing. Existing A/B columns remain unchanged; Group L is optional and separate.
- User clarification: retention of long memory requires improvement over AB, while SES is comparison only. Compare AB with the same step-6 recency weighting to isolate the new features; also report unweighted logreg_AB. Carry recency forward only when its prior paired gain lower bound is positive; otherwise inf. C uses the same {0.01,0.1,1,10} grid on pooled VALID. If the matched-AB gain CI includes zero, record no evidence of improvement and preserve the previous A/B feature choice.
- HGB full grid: learning_rate {0.05,0.1}, max_depth {3,5}, max_iter cap {100,300}, fixed seed 42. All eight candidates per lead are evaluated; shared fitting trajectories may reuse identical prefixes. No random validation split. Fixed chronological TRAIN calibration tail 14 days; preceding 14 days provide early stopping, with 25-hour gaps to prevent label overlap. Select iterations by tail Brier every 10 trees (minimum 10), patience 30 trees, minimum improvement 1e-5. Refit those iterations on pre-calibration TRAIN; calibration tail stays untouched by model fitting. Refit base_rate on the actual fitting subset, not inner holdout labels. Half-life ages are measured from the fold's nominal TRAIN end.
- Calibration trigger fixed before HGB scores: pooled raw VALID ECE >0.03 means clearly miscalibrated. In that case fit Platt on the chronological calibration TRAIN tail (clipped log-odds, epsilon 1e-6, logistic C=1e6, no resampling), log raw and calibrated versions, and compare them on VALID. Calibration parameters never fit VALID/TEST.
- Ensemble newly authorised: best eligible learned model per lead plus SES, weights for the learned model {0.25,0.5,0.75}, selected by pooled VALID Brier. Frozen selection compares eligible learned models, ensembles and references by VALID Brier. Lead 0 stays separate. Freeze model, ordered features, hyperparameters, half-life and ensemble weight per lead; fitted coefficients/alpha/iteration counts are learned only on the future FINAL TRAIN using the frozen rules. No FINAL run here.
- Calendar ablation, rolling refit, and frozen robustness on A/D or TRAIN_START remain deferred and unstarted. Existing limitations remain: artificial ends, prior exploratory TEST overlap, December 2025 definition break, incomplete in-panel adjacency, and June–July-only validation. Selection CIs do not adjust for tuning/multiple comparisons.

## Step 6b — fixed long memory results

- VERIFIED: logreg_ABL was evaluated at all nine leads with the unchanged C grid and previously supported recency settings. The fixed 672h exact share / 336h EWMA parameters were not searched. Core future-perturbation tests now cover both long features; vectorized and direct calculations agree.
- VERIFIED: Pooled ABL BSS versus climatology at leads 1/6/12/24 is 0.10632/0.04532/0.03505/0.02795. Matched-recency AB gain CIs retain Group L at 1,2,3,6,12,24. At 0,4,5: no evidence of improvement; the earlier A/B feature choice is preserved. Both matched-recency and unweighted AB gains are in long_gains.csv.
- VERIFIED: Against SES, ABL's gain CI is positive at 0,1,2, crosses zero at 3,4,5,6,12, and is negative at 24. SES comparison does not veto Group L, per user clarification; superiority to SES at long leads is not established. CIs are conditional on validation selection.

## Step 7 — HGB results

- VERIFIED: Full 8-point grid × 4 independent folds × 9 leads = 288 candidate-fold evaluations; no grid or lead reduction. Stopping trajectories reuse identical prefixes while evaluating both 100/300 caps. Ordered core/stopping/refit/calibration boundaries and actual chosen iterations are saved in hgb_train_tails.csv and hgb_stopping_history.csv.
- VERIFIED: Pooled HGB BSS versus climatology at 1/6/12/24 is 0.10293/0.03005/0.03372/0.03241. Corresponding BSS versus SES is 0.04831/−0.01939/−0.01156/−0.00791. These scores do not establish universal HGB superiority. Actual fitting excludes the chronological calibration tail; base_rate is fitted only on the relevant fitting subset.
- VERIFIED: Pooled raw ECE ranges 0.01155..0.02646 across leads, below the predeclared >0.03 trigger. No real-data Platt/isotonic model was fitted. Platt TRAIN-tail fitting and chronological embargoes pass synthetic tests. Full Python 3.14 suite: 88 passed, 15 skipped; three sklearn tests use the offline Python 3.12 environment, while twelve pre-existing skips lack UPSTREAM_DIR. No failures, network, credentials or TEST evaluation.

## Step 8 — ensemble comparison and freeze

- VERIFIED: Ensemble weights {0.25,0.5,0.75} were evaluated at each of nine leads, using the best eligible learned model and SES. Weight means the learned-model share. Lead 0 retains raw HGB; its SES ensemble was worse. Frozen leads 1,2,3 use SES+ABL with learned weight 0.75; 4,5 use SES+AB_hl30 at 0.50; 6 uses SES+ABL at 0.50; 12 uses SES+ABL at 0.25; 24 uses SES+HGB at 0.50.
- VERIFIED: Frozen pooled BSS versus climatology at 1/6/12/24 is 0.11049/0.05411/0.04730/0.04479; versus SES it is 0.05633/0.00590/0.00265/0.00498. Seven-day gain CIs versus SES include zero at 6 and 24: no evidence of improvement there, despite selection by the specified lowest VALID Brier rule. Ensemble gains over the learned base include zero at 1,2,3; these remain validation-selected choices rather than established improvements. No lead is selected or dropped by these scores.
- VERIFIED: Comparison covers 24 model names and 486 model/lead/reference rows; per-oblast best-model reporting has 864 fold/lead/region rows with TRAIN flags. Unchanged reference predictions were verified against their latest run_ids and appended with pooled scopes. Existing log records remain unchanged; latest_results ignores stale runs. All three references have paired seven-day CIs. Notebooks 04/05 have executed table cells; calibration and BSS figures were rendered offline.
- VERIFIED: config/final_config.json freezes per-lead model, ordered features, hyperparameters, half-life and ensemble weight. It freezes TRAIN fitting rules, not validation-fold coefficients or iteration counts. Platt was not triggered; FINAL must use the frozen calibration method, not a new TEST-triggered decision. No FINAL fit/evaluation or remaining optional task ran.
- VERIFIED: Python 3.14 tests: 88 passed, 15 skipped; forecasting tests on installed Python 3.12 sklearn: 26 passed. Model execution on Python 3.14 remains unverified because sklearn is absent there. Plots used cached Python 3.13 matplotlib. No downloads or credential access. Existing artificial-close, prior exploration, definition-break, partial adjacency and short-validation limitations remain; CIs are conditional on validation selection.

## FINAL TEST — completed from saved predictions

- VERIFIED: Frozen config commit 296573221359a2ce12d9c45e729500980807a71c; src/config/scripts were clean at the original preflight. Input fingerprints matched. FINAL refit used TRAIN T in [2025-12-01,2026-07-30 23:00 UTC), the 25-hour embargo, and the frozen per-lead feature/C/recency/ensemble settings. HGB retained its frozen inner chronological tails/refit subset; SES alpha and HGB iterations were fitted on TRAIN only.
- VERIFIED: All nine leads were predicted once. TEST UTC [2026-08-01 00:00,2026-09-05 05:00), using the independently trimmed source endpoint floored to the hour and withholding target windows extending beyond it. 181,152 prediction rows were saved before evaluation. No test-score-driven settings changes, refits or repeated predictions occurred.
- VERIFIED: Initial evaluation stopped on a pandas chunked CSV-parser IndexError while reading selected columns of results.csv with mixed numeric/text fold ids. Recovery disables chunked inference and specifies identifier dtypes; a synthetic 65,538-row regression test passes. The explicit --evaluate-saved path validates checkpoints/config/target bounds and evaluates saved predictions only.
- VERIFIED: Prediction SHA-256 remains 8e74808e6c75ee00a9a153ab6bd61ac7ce1c664d8d6ef5205b437a3c2bef60d3; frozen config bytes are unchanged. The entire pre-existing 70,946,427-byte results.csv prefix is unchanged; 234 FINAL rows append with fold_id=test, notes=final and the frozen commit. Reporting includes 216 per-oblast rows, FINAL TRAIN flags, excluded-flagged metrics, and seven-day paired CIs versus all three references.
- VERIFIED: TEST BSS versus climatology at leads 1/6/12/24 is 0.23205/0.13574/0.11175/0.08561; versus SES it is 0.04891/0.02343/0.01224/0.00584. SES gain CIs include zero at 5,6,12,24: no evidence of improvement there. Lead 0 remains separate. TEST raw Brier is worse than validation at 12 (0.09405 vs 0.09306) and 24 (0.09718 vs 0.09278); the report lists all calibration/skill deteriorations explicitly. Different periods/reference errors make this descriptive, not a paired period comparison.
- VERIFIED: Full Python 3.14 tests: 92 passed, 15 skipped; FINAL-specific tests on frozen Python 3.12: 4 passed. Saved evaluation ran offline on Python 3.12 with no raw modifications or credential access. Remaining optional experiments stay unstarted; no post-TEST tuning. See reports/model/final_test.md and its metrics/bootstrap/per-oblast CSVs.

## Task 6 — retrospective offline TEST viewer

- VERIFIED: The single-page app only displays saved FINAL predictions and pooled TEST summaries. Inputs are final_test.csv.gz (181,152 rows, 24 regions, leads 0..6/12/24), final_test_metrics.csv, final_test_bootstrap.csv, frozen config, and FINAL checkpoint provenance. Frozen commit: 296573221359a2ce12d9c45e729500980807a71c. No model is fitted, called or tuned, and no validation/TRAIN data is embedded.
- VERIFIED: The TEST window is [2026-08-01 00:00,2026-09-05 05:00) UTC. Forecast T ranges differ by lead because target hours extending beyond the trimmed endpoint are withheld. No gaps/cells are filled or extrapolated. Forecast mode displays the saved probability for [T+k,T+k+1h); fact mode displays saved y, with dashed outlines for original unrounded |p−y|>=0.5. Switching mode preserves T/k. There is no state-at-T column, so none is inferred or displayed.
- VERIFIED: The used boundary file is the user-supplied root geoBoundaries-UKR-ADM1.geojson, 3,919,902 bytes, 27 Polygon/MultiPolygon features, CRS84 lon/lat. Exact source URL from the supplied metadata: https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/UKR/ADM1/geoBoundaries-UKR-ADM1.geojson . SHA-256: b2f9f4ad2e9be5888523219c0bb46a24332ead16b46305409098048fd361a2d6. ISO identifiers uniquely match all 24 modelled regions; UA-30 (Kyiv City) and UA-32 (Kyivska) are distinct. Source and metadata remain unchanged in the root, per user preference; both are ignored. A preliminary Natural Earth download exists under ignored data/geo but is not used. No further download is performed by the builder.
- Licence attribution follows the task-specified geoBoundaries gbOpen licence: CC BY 4.0, geoBoundaries / William & Mary geoLab. The supplied metadata contains the pinned download URL but no licence field; independent licence-page verification was not performed because network use was restricted. The source, attribution and hash are included as footer text, with no external links/resources.
- VERIFIED: Projection is equirectangular (longitude scaled by cos(49 degrees), negative latitude), fitted to the Ukraine extent. Closed rings are simplified with Ramer–Douglas–Peucker at fixed 0.8 SVG-unit tolerance, rounded to 0.1 unit, preserving holes via even-odd fill. Path data totals 62,028 bytes. Geometry is for display, not precise boundary measurement. Kyiv City has its real polygon plus an offset circle/leader; Luhanska, Crimea and Sevastopol stay neutral/hatched with no forecast values.
- VERIFIED: Compact layout is lead/T/oblast: little-endian uint16 per-mille probabilities, little-bit-order outcomes and exact raw-probability error flags. Build-time probability round-trip error is <=0.0005 (floating-point comparison tolerance only), outcomes match exactly. Summary values/CIs are copied from saved TEST files, not recalculated. The final HTML is 636,763 bytes; embedded JSON 548,583 bytes. Repeated production builds are byte-identical.
- VERIFIED: Vanilla JS decodes once; SVG geometry is never recreated while moving frames. The fixed seven-bin blue palette, keyboard controls, sorted accessible list, Ukrainian local/UTC times, target-hour labels, separate nowcast option, and prefers-color-scheme support are included. No external fonts/libraries/images/tiles, network API, storage, server, or live data. CSP forbids network connections.
- VERIFIED: 10 synthetic app tests pass, including Node decode/render and withheld-tail checks. Full Python 3.14 suite: 102 passed, 15 pre-existing skips. Cached headless Chromium loaded the actual file:// page at 380/1280 px, with zero HTTP requests, zero console errors and no horizontal overflow. Checked forecast outcome hiding, toggle invariance, lead bounds, nowcast/SES-CI labels, error outlines, arrows/PageUp, playback and dark mode. Screenshots are temporary and not committed. In-app browser tooling was unavailable, so the documented headless fallback was used.
- Known limitations: retrospective only; different frozen models/weights by lead; lead 0 is current-hour nowcast, never pooled; excluded regions and incomplete adjacency; small Kyiv polygon shown with a marker; saved probabilities are quantised for display, never recomputed; raw-error outlines may differ from a rounded 50.0% tie; existing model/data limitations remain. No new metrics or predictions were created.

## Viewer presentation follow-up

- User-requested presentation changes supersede the earlier seven-bin palette and top retrospective/commit text. Branding is now “Тривожник”, with the supplied tagline on the right and the historical-data subtitle. The visible keyboard hint is removed while controls remain functional. Region details are above the map; playback is larger and more prominent; time labels use the supplied wording, with next-day target dates retained when needed.
- VERIFIED: Probability colour now uses a fixed continuous darker blue gradient over 0–100%, rather than buckets. This changes display only: the embedded saved data block is byte-identical to the previously published page. Frozen forecasts, outcomes, summaries and error flags are unchanged. System light/dark themes remain supported.
- VERIFIED: 10 app tests pass, including Node continuous-colour/decode/render checks. Offline headless Chromium checked 380/1280 px, controls, bounds, dark mode and zero HTTP requests/console errors. No refitting, new predictions, commits or pushes were performed.

## 2026-10-12 — Approved repository cleanup

VERIFIED: Removed the duplicate root notebook, conversation export, unused preliminary Natural Earth geometry, step5b_core.md, steps3_6.md, steps3_6_summary.csv, and project OS/Python/pytest caches after user approval. Kept the combined notebook, canonical reports, current geometry, raw/API snapshots, frozen configuration, predictions and append-only results. No staging or commit was performed. Caches can regenerate on later runs.
