# long: validation only

> Historical validation/progress snapshot. Statements about TEST not being evaluated or later stages being unstarted describe this report’s original stage. FINAL is now complete; see [final_test.md](final_test.md). Numeric results below are preserved unchanged.

VERIFIED: run 69afb997281b6d84. Fixed 672-hour exact share and 336-hour EWMA half-life; no window/half-life tuning. ABL retention requires positive gain CI against AB with matched recency. SES is comparison only. Unweighted AB comparison is also saved.

Four independent fold fits, 25-hour embargo; no TEST. VALID selects candidates, so scores/CIs are descriptive selection results and do not adjust for selection/multiple comparisons. Seven-day paired blocks are primary; one-day sensitivity is saved.

```text
     model  lead     n   brier  bss_vs_clim  bss_vs_persistence  bss_vs_ses  bss_ci_low  bss_ci_high     ece
logreg_ABL     0 35136 0.05453      0.44136             0.04769     0.35226     0.41069      0.47302 0.00991
logreg_ABL     1 35112 0.08724      0.10632             0.04926     0.05191     0.07165      0.14485 0.02422
logreg_ABL     2 35088 0.09069      0.07112             0.05122     0.02908     0.04676      0.09483 0.02302
logreg_ABL     3 35064 0.09147      0.06328             0.04889     0.01957     0.04280      0.08363 0.02305
logreg_ABL     4 35040 0.09228      0.05492             0.03981     0.00296     0.03813      0.07202 0.02272
logreg_ABL     5 35016 0.09276      0.04979             0.03628    -0.00031     0.03384      0.06534 0.02228
logreg_ABL     6 34992 0.09320      0.04532             0.03490    -0.00335     0.02814      0.06016 0.01946
logreg_ABL    12 34848 0.09426      0.03505             0.03215    -0.01017     0.01590      0.05343 0.02902
logreg_ABL    24 34560 0.09441      0.02795             0.02210    -0.01255     0.00844      0.04465 0.03175
```
