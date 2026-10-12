# Step A: validation only

> Historical validation/progress snapshot. Statements about TEST not being evaluated or later stages being unstarted describe this report’s original stage. FINAL is now complete; see [final_test.md](final_test.md). Numeric results below are preserved unchanged.

VERIFIED: run 19e91e2083bdf3a2; 25-hour embargo, independent fold fits, pooled TRAIN, no class resampling, no calendar/identity/STL features, no TEST.

C is chosen across the four VALID folds for each lead, not separately on each fold. Recency fixes the previous selected C and selects half-life on VALID. These validation-selected metrics are descriptive selection scores, not unbiased final performance. CI uses paired circular seven-day UTC blocks; one-day sensitivity and all three references are in the bootstrap table. Per-region and excluded-flagged metrics are logged.

```text
   model  lead   brier  bss_vs_clim  bss_vs_persistence  bss_vs_ses  bss_ci_low  bss_ci_high     ece
logreg_A     0 0.05504      0.43616             0.03882     0.34623     0.40876      0.46426 0.01365
logreg_A     1 0.08883      0.09006             0.03196     0.03466     0.06151      0.12512 0.02852
logreg_A     2 0.09231      0.05454             0.03428     0.01175     0.03504      0.07440 0.02492
logreg_A     3 0.09305      0.04708             0.03244     0.00262     0.03094      0.06332 0.02491
logreg_A     4 0.09346      0.04292             0.02761    -0.00970     0.02665      0.05811 0.02258
logreg_A     5 0.09401      0.03703             0.02334    -0.01374     0.02135      0.05132 0.02297
logreg_A     6 0.09463      0.03069             0.02012    -0.01872     0.01314      0.04580 0.02421
logreg_A    12 0.09601      0.01712             0.01416    -0.02894    -0.00807      0.03742 0.02881
logreg_A    24 0.09618      0.00974             0.00378    -0.03152    -0.01774      0.03239 0.02848
```
