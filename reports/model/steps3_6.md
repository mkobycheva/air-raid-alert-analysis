# Task 5B steps 3–6; stopped before HGB

VERIFIED: Group A has exactly 8 named predictors; Group B has exactly 4. The extra never_alerted flag is removed. No old lag, cap-72, 28-day/calendar/STL or identity predictors enter the pooled models. Confirmed neighbors exclude Luhanska/Crimea; the Donetska/Kharkivska/Khersonska neighborhoods are incomplete geographically.

VERIFIED: four independent fold experiments, common 25-hour embargo, one lead at a time; cached observations have 139,968 rows. First TRAIN has 104,232 rows. No TEST target hour or classifier evaluation. Per-oblast/ALL/ALL_excl_flagged metrics and pooled rows append to results.csv. latest_results ignores stale executions per model/fold/lead, retaining scopes.

VERIFIED: 84 passed, 14 skipped under Python 3.14; 21 passed in the Python 3.12 forecasting suite, including both sklearn tests skipped in 3.14. Twelve skips are existing unavailable upstream-parser tests. No failures. No network, credentials or raw modifications. Modelling uses offline installed sklearn 1.6.1 on Python 3.12; calibration plots use cached Python 3.13 matplotlib. sklearn modelling on 3.14 remains unverified.

VERIFIED: candidate fold-fit counts from score files: {'A': 144, 'AB': 576, 'recency': 144}. One C per lead minimizes pooled VALID Brier; recency fixes the chosen C and base model, fitting weighted scaler/loss on TRAIN. Weights are not normalized. Base rates remain ordinary TRAIN y_0 means. These CIs do not adjust for validation hyperparameter selection or multiple comparisons.

VERIFIED: selected pooled validation scores read from latest results.csv:

```text
 lead   A_bss  AB_bss          model  half_life  bss_vs_clim  bss_vs_persistence  bss_vs_ses     ece
    0 0.43616 0.43842  logreg_A_hl60   60.00000      0.43702             0.04029     0.34723 0.01385
    1 0.09006 0.09940 logreg_AB_hl14   14.00000      0.10409             0.04688     0.04954 0.02709
    2 0.05454 0.06520 logreg_AB_hl14   14.00000      0.06965             0.04973     0.02755 0.02385
    3 0.04708 0.05783 logreg_AB_hl30   30.00000      0.06067             0.04625     0.01685 0.02470
    4 0.04292 0.04899 logreg_AB_hl30   30.00000      0.05271             0.03756     0.00062 0.02514
    5 0.03703 0.04377 logreg_AB_hl30   30.00000      0.04750             0.03395    -0.00273 0.02337
    6 0.03069 0.03981 logreg_AB_hl14   14.00000      0.04349             0.03306    -0.00526 0.02027
   12 0.01712 0.02558  logreg_A_hl60   60.00000      0.01729             0.01432    -0.02877 0.02615
   24 0.00974 0.01617 logreg_A_hlinf        inf      0.00974             0.00378    -0.03152 0.02848
```

VERIFIED: full context is carried forward only for leads 1–6; at 0/12/24 the gain CI crosses zero: no evidence of improvement. Ablation results are in AB_validation.csv. Recency at 0/12 has inconclusive gain, and 24 selects inf. No unusually high long-lead skill was observed; synthetic future perturbation, pooled rate/scaler and embargo/TEST guard tests pass.

VERIFIED: merged notebooks/00_eda.ipynb has historical EDA first and TRAIN-only STL below it; historical cells were not re-executed. Notebooks 01/02/03 read run tables and have executed cells, setup, calibration/ECE and conclusions. The original root EDA is retained. No step 7+, optional experiment, final config or FINAL evaluation is run.

VERIFIED: commands: pytest (3.14 full, 3.12 forecasting subset); run_model_ladder.py --stage prepare/A/AB/recency; report_model_ladder.py --stage A/AB/recency --notebooks-only; cached offline renderer with --plots-only; reference equality/latest-log checks; git diff --check/status.
