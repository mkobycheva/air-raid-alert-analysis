# ensemble: validation only

VERIFIED: run b4c2e7b7541abb31. Fixed SES averaging weights {0.25,0.5,0.75} selected on pooled VALID; learned base respects context/long-memory/recency gates. No other optional experiment run.

Four independent fold fits, 25-hour embargo; no TEST. VALID selects candidates, so scores/CIs are descriptive selection results and do not adjust for selection/multiple comparisons. Seven-day paired blocks are primary; one-day sensitivity is saved.

```text
                 model  lead     n   brier  bss_vs_clim  bss_vs_persistence  bss_vs_ses  bss_ci_low  bss_ci_high     ece
           ens_ses_hgb     0 35136 0.05584      0.42791             0.02476     0.33667     0.39807      0.45571 0.01489
    ens_ses_logreg_ABL     1 35112 0.08683      0.11049             0.05369     0.05633     0.08178      0.14256 0.01577
    ens_ses_logreg_ABL     2 35088 0.09028      0.07534             0.05554     0.03350     0.05574      0.09640 0.01597
    ens_ses_logreg_ABL     3 35064 0.09103      0.06770             0.05338     0.02420     0.04767      0.08623 0.01745
ens_ses_logreg_AB_hl30     4 35040 0.09147      0.06329             0.04831     0.01179     0.04534      0.08004 0.01272
ens_ses_logreg_AB_hl30     5 35016 0.09193      0.05834             0.04495     0.00869     0.04050      0.07503 0.01242
    ens_ses_logreg_ABL     6 34992 0.09234      0.05411             0.04379     0.00590     0.03503      0.07152 0.01011
    ens_ses_logreg_ABL    12 34848 0.09306      0.04730             0.04443     0.00265     0.02383      0.06958 0.00762
           ens_ses_hgb    24 34560 0.09278      0.04479             0.03903     0.00498     0.02297      0.06377 0.01418
```
