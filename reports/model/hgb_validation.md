# hgb: validation only

VERIFIED: run 3d8fa45bd7f5114f. Full 8-point HGB grid at all nine leads. Explicit chronological stopping/calibration TRAIN tails with 25-hour inner gaps; no random split. Raw VALID ECE >0.03 triggers TRAIN-tail Platt, logging both versions.

Four independent fold fits, 25-hour embargo; no TEST. VALID selects candidates, so scores/CIs are descriptive selection results and do not adjust for selection/multiple comparisons. Seven-day paired blocks are primary; one-day sensitivity is saved.

```text
model  lead     n   brier  bss_vs_clim  bss_vs_persistence  bss_vs_ses  bss_ci_low  bss_ci_high     ece
  hgb     0 35136 0.05482      0.43838             0.04262     0.34881     0.40849      0.46645 0.01155
  hgb     1 35112 0.08757      0.10293             0.04566     0.04831     0.06742      0.14058 0.01425
  hgb     2 35088 0.09135      0.06440             0.04436     0.02206     0.03423      0.09065 0.01962
  hgb     3 35064 0.09201      0.05776             0.04329     0.01380     0.03690      0.07704 0.02086
  hgb     4 35040 0.09267      0.05095             0.03577    -0.00123     0.03547      0.06733 0.01974
  hgb     5 35016 0.09349      0.04231             0.02870    -0.00818     0.02788      0.05771 0.02072
  hgb     6 34992 0.09469      0.03005             0.01947    -0.01939     0.01525      0.04430 0.02357
  hgb    12 34848 0.09439      0.03372             0.03081    -0.01156     0.02004      0.04562 0.02646
  hgb    24 34560 0.09398      0.03241             0.02658    -0.00791     0.01457      0.04786 0.02413
```
