# Source comparison — descriptive only

> Descriptive snapshot, not model selection or FINAL evidence. Results below retain their original inputs and windows; current project status is in [README](../../README.md).

Existing components retained: official/volunteer loaders, UTC interval grid and exact unions, Telegram topup/census, API collector and their tests. The API collector is not run by this program.

Official primary definition is B (oblast+raion); A and D are sensitivities. The official CSV has no alert-type field; variant B is a level-based definition, not a row-level siren label.

Volunteer channel provenance is user-supplied UkraineAlarmSignal; the CSV has no channel field, so provenance cannot be independently verified from that file. Earlier documentation naming eTryvoga is superseded by this supplied fact.

API collector review: Authorization: Bearer is retained, with 31-second request spacing and a 429 Retry-After-aware backoff. Auth/header and endpoint limits were not tested against the live API. Clear fixes are ISO8601 mixed-precision parsing, stable empty-output schema, null threat-type handling, refusal of missing ids/invalid timestamps, latest-query duplicate-id resolution, and completion-time fetched_at. Null finished_at remains open; missing alert_level is not inferred.

SKIPPED dated template aggregations: census_message_templates_*.csv is missing.

Existing undated census contains 13127 messages; it is inventoried separately, not relabelled or combined with dated censuses.

2026 census totals and the June 2026 break cannot be checked unless their date-ranged census files are present. Telegram silence is supplied context; offline CSV endpoints cannot verify live channel silence.

API file covers 24 non-excluded oblasts: Cherkaska oblast, Chernihivska oblast, Chernivetska oblast, Dnipropetrovska oblast, Donetska oblast, Ivano-Frankivska oblast, Kharkivska oblast, Khersonska oblast, Khmelnytska oblast, Kirovohradska oblast, Kyiv City, Kyivska oblast, Lvivska oblast, Mykolaivska oblast, Odeska oblast, Poltavska oblast, Rivnenska oblast, Sumska oblast, Ternopilska oblast, Vinnytska oblast, Volynska oblast, Zakarpatska oblast, Zaporizka oblast, Zhytomyrska oblast. Partial coverage is retained; absent oblasts are not treated as zero alerts. The API archive is assumed to cover the 30 days preceding the earliest fetched_at timestamp; long-lived alert starts do not extend this archive window backwards.

FACT discrepancy in API UID schema: 16313/16532 rows require an oblast name/query fallback; location_oblast_uid does not identify their oblast. Resolution methods are in api_counts.csv.

FACT discrepancy: the current API CSV also contains non-raion rows; API ALL/RED OR all its air_raid levels. See api_counts.csv.

FACT discrepancy in API snapshot timestamp: 3 rows start after their fetched_at. The existing collector recorded a pre-request timestamp; future runs now use fetch completion. This comparison conservatively bounds the API end by the stored fetched_at as requested.

Configured exclusions: Luhanska oblast, Crimea and Sevastopol. Only actually present excluded regions appear below.

All windows are half-open [start, end), in UTC unless marked Europe/Kyiv. Exact shares use union time with second/subsecond precision. Sources are never merged or averaged. All counts, conditional grid probabilities, differences, episode lengths and reference ratios are descriptive; no targets, splits, features, models or forecast evaluation are created.

Tail rule: max(started_at) − 48 h per original source, bounded by max(fetched_at) for API. Compute before definition/region/naive filters; clip intervals at each pair's earlier valid end. Open API alerts are counted separately and excluded from every interval metric. Touch shares weight bins equally, including a partial final bin. Daily presence uses Kyiv calendar boundaries (time-grid bins are anchored at each pair's start) with DST and includes partial boundary days. Episodes merge strict overlaps; abutting intervals remain separate. An empty conditional denominator is blank/NaN, not zero.

Pair A/B labels in conditional columns refer to source_a/source_b, not official definition variants. The API pairs use A=API-ALL or API-RED and B=volunteer. API-level/threat overlap categories are non-exclusive: one volunteer interval can appear in several categories.

## Explicit pairs and windows

| source_a | source_b | period | start_utc | end_utc |
| --- | --- | --- | --- | --- |
| official_A | volunteer | full | 2022-03-15T00:00:00+00:00 | 2026-09-05T05:28:22+00:00 |
| official_A | volunteer_no_naive | full | 2022-03-15T00:00:00+00:00 | 2026-09-05T05:28:22+00:00 |
| official_B | volunteer | full | 2022-03-15T00:00:00+00:00 | 2026-09-05T05:28:22+00:00 |
| official_B | volunteer_no_naive | full | 2022-03-15T00:00:00+00:00 | 2026-09-05T05:28:22+00:00 |
| official_A | volunteer | 2023 | 2023-01-01T00:00:00+00:00 | 2024-01-01T00:00:00+00:00 |
| official_A | volunteer_no_naive | 2023 | 2023-01-01T00:00:00+00:00 | 2024-01-01T00:00:00+00:00 |
| official_B | volunteer | 2023 | 2023-01-01T00:00:00+00:00 | 2024-01-01T00:00:00+00:00 |
| official_B | volunteer_no_naive | 2023 | 2023-01-01T00:00:00+00:00 | 2024-01-01T00:00:00+00:00 |
| official_A | volunteer | 2024 | 2024-01-01T00:00:00+00:00 | 2025-01-01T00:00:00+00:00 |
| official_A | volunteer_no_naive | 2024 | 2024-01-01T00:00:00+00:00 | 2025-01-01T00:00:00+00:00 |
| official_B | volunteer | 2024 | 2024-01-01T00:00:00+00:00 | 2025-01-01T00:00:00+00:00 |
| official_B | volunteer_no_naive | 2024 | 2024-01-01T00:00:00+00:00 | 2025-01-01T00:00:00+00:00 |
| official_A | volunteer | 2025-01..06 | 2025-01-01T00:00:00+00:00 | 2025-07-01T00:00:00+00:00 |
| official_A | volunteer_no_naive | 2025-01..06 | 2025-01-01T00:00:00+00:00 | 2025-07-01T00:00:00+00:00 |
| official_B | volunteer | 2025-01..06 | 2025-01-01T00:00:00+00:00 | 2025-07-01T00:00:00+00:00 |
| official_B | volunteer_no_naive | 2025-01..06 | 2025-01-01T00:00:00+00:00 | 2025-07-01T00:00:00+00:00 |
| official_A | volunteer | 2025-12..2026-01 | 2025-12-01T00:00:00+00:00 | 2026-02-01T00:00:00+00:00 |
| official_A | volunteer_no_naive | 2025-12..2026-01 | 2025-12-01T00:00:00+00:00 | 2026-02-01T00:00:00+00:00 |
| official_B | volunteer | 2025-12..2026-01 | 2025-12-01T00:00:00+00:00 | 2026-02-01T00:00:00+00:00 |
| official_B | volunteer_no_naive | 2025-12..2026-01 | 2025-12-01T00:00:00+00:00 | 2026-02-01T00:00:00+00:00 |
| official_A | volunteer | 2026-02..valid_end | 2026-02-01T00:00:00+00:00 | 2026-09-05T05:28:22+00:00 |
| official_A | volunteer_no_naive | 2026-02..valid_end | 2026-02-01T00:00:00+00:00 | 2026-09-05T05:28:22+00:00 |
| official_B | volunteer | 2026-02..valid_end | 2026-02-01T00:00:00+00:00 | 2026-09-05T05:28:22+00:00 |
| official_B | volunteer_no_naive | 2026-02..valid_end | 2026-02-01T00:00:00+00:00 | 2026-09-05T05:28:22+00:00 |
| API-ALL | volunteer | API overlap | 2026-09-11T08:31:59.112875+00:00 | 2026-10-08T04:47:44+00:00 |
| API-ALL | volunteer_no_naive | API overlap | 2026-09-11T08:31:59.112875+00:00 | 2026-10-08T04:47:44+00:00 |
| API-RED | volunteer | API overlap | 2026-09-11T08:31:59.112875+00:00 | 2026-10-08T04:47:44+00:00 |
| API-RED | volunteer_no_naive | API overlap | 2026-09-11T08:31:59.112875+00:00 | 2026-10-08T04:47:44+00:00 |

## Excluded regions

| source | oblast | rows |
| --- | --- | --- |
| official | Luhanska oblast | 1 |
| volunteer | Luhanska oblast | 3 |
| alerts.in.ua | Luhanska oblast | 1 |

## Input inventory and cheaply checked facts

| source | rows | min_started_at | max_started_at | max_finished_at | valid_end | oblasts | open_rows | min_fetched_at | max_fetched_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| official | 185430 | 2022-03-15 16:10:34+00:00 | 2026-09-07 05:28:22+00:00 | 2026-09-07 05:39:33+00:00 | 2026-09-05 05:28:22+00:00 | 25 | 0 | nan | nan |
| volunteer | 115793 | 2022-02-25 16:36:22+00:00 | 2026-10-10 04:47:44+00:00 | 2026-10-10 04:59:31+00:00 | 2026-10-08 04:47:44+00:00 | 25 | 0 | nan | nan |
| alerts.in.ua | 16532 | 2022-04-04 16:45:39+00:00 | 2026-10-11 08:35:07.803000+00:00 | 2026-10-11 08:34:24+00:00 | 2026-10-09 08:31:59.112875+00:00 | 25 | 70 | 2026-10-11 08:31:59.112875+00:00 | 2026-10-11 08:31:59.112875+00:00 |

## Fact 3 regression (explicit untrimmed reference windows)

| period | oblast | start_utc | end_utc | A | B | C | D | expected_A | expected_B | expected_C | discrepancy_gt002 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2024 | Dnipropetrovska oblast | 2024-01-01T00:00:00+00:00 | 2025-01-01T00:00:00+00:00 | 0.910783 | 0.219894 | 0.856174 | 0.219894 | 0.911000 | 0.220000 | 0.856000 | False |
| 2024 | Donetska oblast | 2024-01-01T00:00:00+00:00 | 2025-01-01T00:00:00+00:00 | 0.611963 | 0.451728 | 0.608227 | 0.451728 | 0.612000 | 0.452000 | 0.608000 | False |
| 2024 | Kharkivska oblast | 2024-01-01T00:00:00+00:00 | 2025-01-01T00:00:00+00:00 | 0.748367 | 0.450981 | 0.431077 | 0.431043 | 0.748000 | 0.451000 | 0.431000 | False |
| 2026 | Dnipropetrovska oblast | 2026-02-01T00:00:00+00:00 | 2026-09-07T00:00:00+00:00 | 0.999055 | 0.904603 | 0.951667 | 0.857247 | 0.999000 | 0.905000 | 0.952000 | False |
| 2026 | Donetska oblast | 2026-02-01T00:00:00+00:00 | 2026-09-07T00:00:00+00:00 | 0.962350 | 0.912560 | 0.743509 | 0.650413 | 0.962000 | 0.913000 | 0.744000 | False |
| 2026 | Kharkivska oblast | 2026-02-01T00:00:00+00:00 | 2026-09-07T00:00:00+00:00 | 0.882113 | 0.880835 | 0.862115 | 0.860837 | 0.882000 | 0.881000 | 0.862000 | False |
| 2026 | Zaporizka oblast | 2026-02-01T00:00:00+00:00 | 2026-09-07T00:00:00+00:00 | 0.832878 | 0.832496 | 0.782249 | 0.752824 | 0.833000 | 0.832000 | 0.782000 | False |
| 2026 | Odeska oblast | 2026-02-01T00:00:00+00:00 | 2026-09-07T00:00:00+00:00 | 0.207852 | 0.207852 | 0.207852 | 0.207852 | 0.208000 | 0.208000 | 0.208000 | False |
| 2026 | Kyiv City | 2026-02-01T00:00:00+00:00 | 2026-09-07T00:00:00+00:00 | 0.066220 | 0.066220 | 0.066220 | 0.066220 | 0.066000 | 0.066000 | 0.066000 | False |
| 2026 | Lvivska oblast | 2026-02-01T00:00:00+00:00 | 2026-09-07T00:00:00+00:00 | 0.011453 | 0.011453 | 0.011453 | 0.011453 | 0.011000 | 0.011000 | 0.011000 | False |

## External reference (user-supplied; not retrieved offline)

[Reference](https://www.slovoidilo.ua/2026/03/24/infografika/suspilstvo/yakyx-oblastyax-prolunalo-najbilshe-najmenshe-povitryanyx-tryvoh-pochatku-roku)

| source | oblast | start_utc | end_utc | end_kyiv | union_hours | reference_hours | ratio_to_reference |
| --- | --- | --- | --- | --- | --- | --- | --- |
| official_A | Dnipropetrovska oblast | 2025-12-31T22:00:00+00:00 | 2026-03-23T22:00:00+00:00 | 2026-03-24T00:00:00+02:00 | 1968.000000 | 1780 | 1.105618 |
| official_A | Kyiv City | 2025-12-31T22:00:00+00:00 | 2026-03-23T22:00:00+00:00 | 2026-03-24T00:00:00+02:00 | 122.059444 | 122 | 1.000487 |
| official_A | Kyivska oblast | 2025-12-31T22:00:00+00:00 | 2026-03-23T22:00:00+00:00 | 2026-03-24T00:00:00+02:00 | 366.116667 | 375 | 0.976311 |
| official_A | Poltavska oblast | 2025-12-31T22:00:00+00:00 | 2026-03-23T22:00:00+00:00 | 2026-03-24T00:00:00+02:00 | 517.726389 | 532 | 0.973170 |
| official_A | Kirovohradska oblast | 2025-12-31T22:00:00+00:00 | 2026-03-23T22:00:00+00:00 | 2026-03-24T00:00:00+02:00 | 293.971944 | 302 | 0.973417 |
| official_B | Dnipropetrovska oblast | 2025-12-31T22:00:00+00:00 | 2026-03-23T22:00:00+00:00 | 2026-03-24T00:00:00+02:00 | 1761.661111 | 1780 | 0.989697 |
| official_B | Kyiv City | 2025-12-31T22:00:00+00:00 | 2026-03-23T22:00:00+00:00 | 2026-03-24T00:00:00+02:00 | 122.059444 | 122 | 1.000487 |
| official_B | Kyivska oblast | 2025-12-31T22:00:00+00:00 | 2026-03-23T22:00:00+00:00 | 2026-03-24T00:00:00+02:00 | 366.116667 | 375 | 0.976311 |
| official_B | Poltavska oblast | 2025-12-31T22:00:00+00:00 | 2026-03-23T22:00:00+00:00 | 2026-03-24T00:00:00+02:00 | 517.726389 | 532 | 0.973170 |
| official_B | Kirovohradska oblast | 2025-12-31T22:00:00+00:00 | 2026-03-23T22:00:00+00:00 | 2026-03-24T00:00:00+02:00 | 293.971944 | 302 | 0.973417 |
| volunteer | Dnipropetrovska oblast | 2025-12-31T22:00:00+00:00 | 2026-03-23T22:00:00+00:00 | 2026-03-24T00:00:00+02:00 | 344.892778 | 1780 | 0.193760 |
| volunteer | Kyiv City | 2025-12-31T22:00:00+00:00 | 2026-03-23T22:00:00+00:00 | 2026-03-24T00:00:00+02:00 | 83.485833 | 122 | 0.684310 |
| volunteer | Kyivska oblast | 2025-12-31T22:00:00+00:00 | 2026-03-23T22:00:00+00:00 | 2026-03-24T00:00:00+02:00 | 151.850278 | 375 | 0.404934 |
| volunteer | Poltavska oblast | 2025-12-31T22:00:00+00:00 | 2026-03-23T22:00:00+00:00 | 2026-03-24T00:00:00+02:00 | 228.324722 | 532 | 0.429182 |
| volunteer | Kirovohradska oblast | 2025-12-31T22:00:00+00:00 | 2026-03-23T22:00:00+00:00 | 2026-03-24T00:00:00+02:00 | 160.935833 | 302 | 0.532900 |
| official_A | Dnipropetrovska oblast | 2025-12-31T22:00:00+00:00 | 2026-03-24T22:00:00+00:00 | 2026-03-25T00:00:00+02:00 | 1992.000000 | 1780 | 1.119101 |
| official_A | Kyiv City | 2025-12-31T22:00:00+00:00 | 2026-03-24T22:00:00+00:00 | 2026-03-25T00:00:00+02:00 | 130.961944 | 122 | 1.073459 |
| official_A | Kyivska oblast | 2025-12-31T22:00:00+00:00 | 2026-03-24T22:00:00+00:00 | 2026-03-25T00:00:00+02:00 | 377.525556 | 375 | 1.006735 |
| official_A | Poltavska oblast | 2025-12-31T22:00:00+00:00 | 2026-03-24T22:00:00+00:00 | 2026-03-25T00:00:00+02:00 | 533.725000 | 532 | 1.003242 |
| official_A | Kirovohradska oblast | 2025-12-31T22:00:00+00:00 | 2026-03-24T22:00:00+00:00 | 2026-03-25T00:00:00+02:00 | 310.703333 | 302 | 1.028819 |
| official_B | Dnipropetrovska oblast | 2025-12-31T22:00:00+00:00 | 2026-03-24T22:00:00+00:00 | 2026-03-25T00:00:00+02:00 | 1783.945000 | 1780 | 1.002216 |
| official_B | Kyiv City | 2025-12-31T22:00:00+00:00 | 2026-03-24T22:00:00+00:00 | 2026-03-25T00:00:00+02:00 | 130.961944 | 122 | 1.073459 |
| official_B | Kyivska oblast | 2025-12-31T22:00:00+00:00 | 2026-03-24T22:00:00+00:00 | 2026-03-25T00:00:00+02:00 | 377.525556 | 375 | 1.006735 |
| official_B | Poltavska oblast | 2025-12-31T22:00:00+00:00 | 2026-03-24T22:00:00+00:00 | 2026-03-25T00:00:00+02:00 | 533.725000 | 532 | 1.003242 |
| official_B | Kirovohradska oblast | 2025-12-31T22:00:00+00:00 | 2026-03-24T22:00:00+00:00 | 2026-03-25T00:00:00+02:00 | 310.703333 | 302 | 1.028819 |
| volunteer | Dnipropetrovska oblast | 2025-12-31T22:00:00+00:00 | 2026-03-24T22:00:00+00:00 | 2026-03-25T00:00:00+02:00 | 350.581389 | 1780 | 0.196956 |
| volunteer | Kyiv City | 2025-12-31T22:00:00+00:00 | 2026-03-24T22:00:00+00:00 | 2026-03-25T00:00:00+02:00 | 86.865000 | 122 | 0.712008 |
| volunteer | Kyivska oblast | 2025-12-31T22:00:00+00:00 | 2026-03-24T22:00:00+00:00 | 2026-03-25T00:00:00+02:00 | 154.551111 | 375 | 0.412136 |
| volunteer | Poltavska oblast | 2025-12-31T22:00:00+00:00 | 2026-03-24T22:00:00+00:00 | 2026-03-25T00:00:00+02:00 | 229.842500 | 532 | 0.432035 |
| volunteer | Kirovohradska oblast | 2025-12-31T22:00:00+00:00 | 2026-03-24T22:00:00+00:00 | 2026-03-25T00:00:00+02:00 | 167.682500 | 302 | 0.555240 |

## INDIRECT bridge — windows do not overlap

| label | oblast | official_start_utc | official_end_utc | api_start_utc | api_end_utc | windows_do_not_overlap | official_B | volunteer_official_window | API_ALL | API_RED | volunteer_API_window |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| INDIRECT | Cherkaska oblast | 2026-08-01T00:00:00+00:00 | 2026-09-05T05:28:22+00:00 | 2026-09-11T08:31:59.112875+00:00 | 2026-10-08T04:47:44+00:00 | True | 0.156553 | 0.113423 | 0.425957 | 0.087468 | 0.151228 |
| INDIRECT | Chernihivska oblast | 2026-08-01T00:00:00+00:00 | 2026-09-05T05:28:22+00:00 | 2026-09-11T08:31:59.112875+00:00 | 2026-10-08T04:47:44+00:00 | True | 0.718661 | 0.225872 | 0.818991 | 0.161855 | 0.156990 |
| INDIRECT | Chernivetska oblast | 2026-08-01T00:00:00+00:00 | 2026-09-05T05:28:22+00:00 | 2026-09-11T08:31:59.112875+00:00 | 2026-10-08T04:47:44+00:00 | True | 0.004024 | 0.005109 | 0.032662 | 0.002872 | 0.026006 |
| INDIRECT | Dnipropetrovska oblast | 2026-08-01T00:00:00+00:00 | 2026-09-05T05:28:22+00:00 | 2026-09-11T08:31:59.112875+00:00 | 2026-10-08T04:47:44+00:00 | True | 0.955645 | 0.220963 | 0.991805 | 0.977113 | 0.214005 |
| INDIRECT | Donetska oblast | 2026-08-01T00:00:00+00:00 | 2026-09-05T05:28:22+00:00 | 2026-09-11T08:31:59.112875+00:00 | 2026-10-08T04:47:44+00:00 | True | 0.970076 | 0.107452 | 0.969843 | 0.909913 | 0.157575 |
| INDIRECT | Ivano-Frankivska oblast | 2026-08-01T00:00:00+00:00 | 2026-09-05T05:28:22+00:00 | 2026-09-11T08:31:59.112875+00:00 | 2026-10-08T04:47:44+00:00 | True | 0.001911 | 0.001697 | 0.007804 | 0.001657 | 0.003611 |
| INDIRECT | Kharkivska oblast | 2026-08-01T00:00:00+00:00 | 2026-09-05T05:28:22+00:00 | 2026-09-11T08:31:59.112875+00:00 | 2026-10-08T04:47:44+00:00 | True | 0.948573 | 0.219811 | 0.925190 | 0.764399 | 0.241047 |
| INDIRECT | Khersonska oblast | 2026-08-01T00:00:00+00:00 | 2026-09-05T05:28:22+00:00 | 2026-09-11T08:31:59.112875+00:00 | 2026-10-08T04:47:44+00:00 | True | 0.287838 | 0.138918 | 0.273731 | 0.044589 | 0.116087 |
| INDIRECT | Khmelnytska oblast | 2026-08-01T00:00:00+00:00 | 2026-09-05T05:28:22+00:00 | 2026-09-11T08:31:59.112875+00:00 | 2026-10-08T04:47:44+00:00 | True | 0.012782 | 0.103630 | 0.107424 | 0.003187 | 0.038100 |
| INDIRECT | Kirovohradska oblast | 2026-08-01T00:00:00+00:00 | 2026-09-05T05:28:22+00:00 | 2026-09-11T08:31:59.112875+00:00 | 2026-10-08T04:47:44+00:00 | True | 0.292179 | 0.125643 | 0.563844 | 0.377174 | 0.169863 |
| INDIRECT | Kyiv City | 2026-08-01T00:00:00+00:00 | 2026-09-05T05:28:22+00:00 | 2026-09-11T08:31:59.112875+00:00 | 2026-10-08T04:47:44+00:00 | True | 0.124266 | 0.070595 | 0.298744 | 0.026108 | 0.086794 |
| INDIRECT | Kyivska oblast | 2026-08-01T00:00:00+00:00 | 2026-09-05T05:28:22+00:00 | 2026-09-11T08:31:59.112875+00:00 | 2026-10-08T04:47:44+00:00 | True | 0.352220 | 0.088460 | 0.678755 | 0.128947 | 0.153045 |
| INDIRECT | Lvivska oblast | 2026-08-01T00:00:00+00:00 | 2026-09-05T05:28:22+00:00 | 2026-09-11T08:31:59.112875+00:00 | 2026-10-08T04:47:44+00:00 | True | 0.000902 | 0.127457 | 0.015452 | 0.001657 | 0.063819 |
| INDIRECT | Mykolaivska oblast | 2026-08-01T00:00:00+00:00 | 2026-09-05T05:28:22+00:00 | 2026-09-11T08:31:59.112875+00:00 | 2026-10-08T04:47:44+00:00 | True | 0.336909 | 0.203264 | 0.465566 | 0.062564 | 0.203717 |
| INDIRECT | Odeska oblast | 2026-08-01T00:00:00+00:00 | 2026-09-05T05:28:22+00:00 | 2026-09-11T08:31:59.112875+00:00 | 2026-10-08T04:47:44+00:00 | True | 0.291351 | 0.127287 | 0.391808 | 0.071780 | 0.110138 |
| INDIRECT | Poltavska oblast | 2026-08-01T00:00:00+00:00 | 2026-09-05T05:28:22+00:00 | 2026-09-11T08:31:59.112875+00:00 | 2026-10-08T04:47:44+00:00 | True | 0.374873 | 0.176239 | 0.545801 | 0.105390 | 0.168395 |
| INDIRECT | Rivnenska oblast | 2026-08-01T00:00:00+00:00 | 2026-09-05T05:28:22+00:00 | 2026-09-11T08:31:59.112875+00:00 | 2026-10-08T04:47:44+00:00 | True | 0.009385 | 0.008138 | 0.136706 | 0.002878 | 0.065125 |
| INDIRECT | Sumska oblast | 2026-08-01T00:00:00+00:00 | 2026-09-05T05:28:22+00:00 | 2026-09-11T08:31:59.112875+00:00 | 2026-10-08T04:47:44+00:00 | True | 0.900662 | 0.191958 | 0.838586 | 0.570475 | 0.174037 |
| INDIRECT | Ternopilska oblast | 2026-08-01T00:00:00+00:00 | 2026-09-05T05:28:22+00:00 | 2026-09-11T08:31:59.112875+00:00 | 2026-10-08T04:47:44+00:00 | True | 0.005182 | 0.114107 | 0.037810 | 0.001657 | 0.138755 |
| INDIRECT | Vinnytska oblast | 2026-08-01T00:00:00+00:00 | 2026-09-05T05:28:22+00:00 | 2026-09-11T08:31:59.112875+00:00 | 2026-10-08T04:47:44+00:00 | True | 0.049254 | 0.028803 | 0.164625 | 0.034432 | 0.066125 |
| INDIRECT | Volynska oblast | 2026-08-01T00:00:00+00:00 | 2026-09-05T05:28:22+00:00 | 2026-09-11T08:31:59.112875+00:00 | 2026-10-08T04:47:44+00:00 | True | 0.002409 | 0.150057 | 0.056792 | 0.001654 | 0.149102 |
| INDIRECT | Zakarpatska oblast | 2026-08-01T00:00:00+00:00 | 2026-09-05T05:28:22+00:00 | 2026-09-11T08:31:59.112875+00:00 | 2026-10-08T04:47:44+00:00 | True | 0.000909 | 0.000000 | 0.001653 | 0.001653 | 0.000000 |
| INDIRECT | Zaporizka oblast | 2026-08-01T00:00:00+00:00 | 2026-09-05T05:28:22+00:00 | 2026-09-11T08:31:59.112875+00:00 | 2026-10-08T04:47:44+00:00 | True | 0.929935 | 0.122036 | 0.909178 | 0.806061 | 0.183886 |
| INDIRECT | Zhytomyrska oblast | 2026-08-01T00:00:00+00:00 | 2026-09-05T05:28:22+00:00 | 2026-09-11T08:31:59.112875+00:00 | 2026-10-08T04:47:44+00:00 | True | 0.058447 | 0.082050 | 0.326051 | 0.082554 | 0.110625 |

## API snapshot and Fact 5 subset

| field | value | count |
| --- | --- | --- |
| alert_type | air_raid | 16249 |
| alert_type | artillery_shelling | 282 |
| alert_type | urban_fights | 1 |
| alert_level | red | 6284 |
| alert_level | yellow | 10248 |
| location_type | city | 1068 |
| location_type | hromada | 1076 |
| location_type | oblast | 219 |
| location_type | raion | 14169 |
| oblast | Cherkaska oblast | 614 |
| oblast | Chernihivska oblast | 730 |
| oblast | Chernivetska oblast | 50 |
| oblast | Dnipropetrovska oblast | 2290 |
| oblast | Donetska oblast | 577 |
| oblast | Ivano-Frankivska oblast | 42 |
| oblast | Kharkivska oblast | 2373 |
| oblast | Khersonska oblast | 385 |
| oblast | Khmelnytska oblast | 197 |
| oblast | Kirovohradska oblast | 1096 |
| oblast | Kyiv City | 217 |
| oblast | Kyivska oblast | 1460 |
| oblast | Luhanska oblast | 1 |
| oblast | Lvivska oblast | 48 |
| oblast | Mykolaivska oblast | 954 |
| oblast | Odeska oblast | 876 |
| oblast | Poltavska oblast | 760 |
| oblast | Rivnenska oblast | 315 |
| oblast | Sumska oblast | 1057 |
| oblast | Ternopilska oblast | 126 |
| oblast | Vinnytska oblast | 489 |
| oblast | Volynska oblast | 140 |
| oblast | Zakarpatska oblast | 18 |
| oblast | Zaporizka oblast | 1205 |
| oblast | Zhytomyrska oblast | 512 |
| oblast_resolution | location_oblast_name_fallback | 16313 |
| oblast_resolution | location_oblast_uid | 219 |

| metric | actual | expected_test_snapshot | discrepancy |
| --- | --- | --- | --- |
| Lvivska+Volynska rows | 188 | 188 | False |
| raion rows | 188 | 188 | False |
| air_raid rows | 188 | 188 | False |
| yellow rows | 155 | 155 | False |
| red rows | 33 | 33 | False |

## API threat metadata

| alert_level | rows | nonempty_threat_rows | nonempty_threat_share |
| --- | --- | --- | --- |
| red | 6284 | 0 | 0.000000 |
| yellow | 10248 | 0 | 0.000000 |

## Open API alerts (not used in interval maths)

| oblast | rows | open_rows |
| --- | --- | --- |
| Cherkaska oblast | 614 | 4 |
| Chernihivska oblast | 730 | 5 |
| Chernivetska oblast | 50 | 0 |
| Dnipropetrovska oblast | 2290 | 13 |
| Donetska oblast | 577 | 8 |
| Ivano-Frankivska oblast | 42 | 0 |
| Kharkivska oblast | 2373 | 11 |
| Khersonska oblast | 385 | 0 |
| Khmelnytska oblast | 197 | 0 |
| Kirovohradska oblast | 1096 | 2 |
| Kyiv City | 217 | 1 |
| Kyivska oblast | 1460 | 7 |
| Luhanska oblast | 1 | 1 |
| Lvivska oblast | 48 | 0 |
| Mykolaivska oblast | 954 | 0 |
| Odeska oblast | 876 | 0 |
| Poltavska oblast | 760 | 4 |
| Rivnenska oblast | 315 | 0 |
| Sumska oblast | 1057 | 3 |
| Ternopilska oblast | 126 | 0 |
| Vinnytska oblast | 489 | 4 |
| Volynska oblast | 140 | 0 |
| Zakarpatska oblast | 18 | 0 |
| Zaporizka oblast | 1205 | 7 |
| Zhytomyrska oblast | 512 | 0 |

## CSV tables

- [official_volunteer.csv](official_volunteer.csv): 576 rows
- [monthly_exact_shares.csv](monthly_exact_shares.csv): 1320 rows
- [variants.csv](variants.csv): 48 rows
- [fact3_regression.csv](fact3_regression.csv): 10 rows
- [hromada_drivers.csv](hromada_drivers.csv): 48 rows
- [external_reference.csv](external_reference.csv): 30 rows
- [long_counts.csv](long_counts.csv): 17 rows
- [long_top_locations.csv](long_top_locations.csv): 20 rows
- [longest_20.csv](longest_20.csv): 20 rows
- [census_groups.csv](census_groups.csv): 0 rows
- [census_siren_shares.csv](census_siren_shares.csv): 0 rows
- [legacy_census_groups.csv](legacy_census_groups.csv): 8 rows
- [legacy_census_siren_shares.csv](legacy_census_siren_shares.csv): 3 rows
- [api_counts.csv](api_counts.csv): 36 rows
- [api_fact5_regression.csv](api_fact5_regression.csv): 5 rows
- [api_threat_shares.csv](api_threat_shares.csv): 2 rows
- [api_open_counts.csv](api_open_counts.csv): 25 rows
- [api_volunteer.csv](api_volunteer.csv): 96 rows
- [api_alert_overlap.csv](api_alert_overlap.csv): 4 rows
- [api_red_time_coverage.csv](api_red_time_coverage.csv): 24 rows
- [indirect_bridge.csv](indirect_bridge.csv): 24 rows
- [inventory.csv](inventory.csv): 3 rows
- [excluded_regions.csv](excluded_regions.csv): 3 rows
