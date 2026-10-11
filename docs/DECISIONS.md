# Data decisions

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
