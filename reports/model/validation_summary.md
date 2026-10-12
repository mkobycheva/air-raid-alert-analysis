# Validation comparison and freeze

VERIFIED: experiments ran in order: reference models → A → AB/ablations → recency → fixed long memory → HGB → SES ensemble. TEST was not evaluated. All numbers below use latest pooled results.csv records; stale runs remain in the append-only log and are ignored by latest_results.

VERIFIED: selected models (pooled VALID Brier; lead 0 separate):

```text
 lead                  model     n   brier  bss_vs_clim  bss_vs_persistence  bss_vs_ses     ece half_life  ensemble_weight
    0                    hgb 35136 0.05482      0.43838             0.04262     0.34881 0.01155       inf              NaN
    1     ens_ses_logreg_ABL 35112 0.08683      0.11049             0.05369     0.05633 0.01577  14.00000          0.75000
    2     ens_ses_logreg_ABL 35088 0.09028      0.07534             0.05554     0.03350 0.01597  14.00000          0.75000
    3     ens_ses_logreg_ABL 35064 0.09103      0.06770             0.05338     0.02420 0.01745  30.00000          0.75000
    4 ens_ses_logreg_AB_hl30 35040 0.09147      0.06329             0.04831     0.01179 0.01272  30.00000          0.50000
    5 ens_ses_logreg_AB_hl30 35016 0.09193      0.05834             0.04495     0.00869 0.01242  30.00000          0.50000
    6     ens_ses_logreg_ABL 34992 0.09234      0.05411             0.04379     0.00590 0.01011  14.00000          0.50000
   12     ens_ses_logreg_ABL 34848 0.09306      0.04730             0.04443     0.00265 0.00762       inf          0.25000
   24            ens_ses_hgb 34560 0.09278      0.04479             0.03903     0.00498 0.01418       inf          0.50000
```

VERIFIED: lead 1 BSS versus SES: logreg_A=0.03466, logreg_AB=0.04457, logreg_ABL=0.05191, hgb=0.04831.
VERIFIED: lead 6 BSS versus SES: logreg_A=-0.01872, logreg_AB=-0.00913, logreg_ABL=-0.00335, hgb=-0.01939.
VERIFIED: lead 12 BSS versus SES: logreg_A=-0.02894, logreg_AB=-0.02009, logreg_ABL=-0.01017, hgb=-0.01156.
VERIFIED: lead 24 BSS versus SES: logreg_A=-0.03152, logreg_AB=-0.02483, logreg_ABL=-0.01255, hgb=-0.00791.

VERIFIED: long-memory retention uses the matched-recency AB gain gate, not superiority to SES. The complete per-lead paired gains are in long_gains.csv. HGB used the full eight-point grid and chronological TRAIN stopping/calibration tails; no random holdout. Raw and triggered Platt ECE are in hgb_validation.csv. Ensemble weights were selected only from 0.25/0.5/0.75.

VERIFIED: table, seven-day CIs for all three references, per-oblast TRAIN flags, and calibration are in comparison_table.csv, best_per_oblast.csv and best_reliability.csv. Config freezes rules/hyperparameters; final coefficients, SES alpha and HGB stopping iterations must be fitted on FINAL TRAIN only, if later authorised.

## HYPOTHESES NOT CONFIRMED

- VERIFIED: plain logistic superiority to SES at lead 12 is not supported by its point score: A=-0.02894, AB=-0.02009; long-memory ABL=-0.01017.
- VERIFIED: plain logistic superiority to SES at lead 24 is not supported by its point score: A=-0.03152, AB=-0.02483; long-memory ABL=-0.01255.
- VERIFIED: universal long-memory improvement is not confirmed; retention failed at lead 0 (ABL BSS versus climatology 0.44136; paired gate in long_gains.csv).
- VERIFIED: universal long-memory improvement is not confirmed; retention failed at lead 4 (ABL BSS versus climatology 0.05492; paired gate in long_gains.csv).
- VERIFIED: universal long-memory improvement is not confirmed; retention failed at lead 5 (ABL BSS versus climatology 0.04979; paired gate in long_gains.csv).
- HYPOTHESIS: validation gains will generalise beyond June–July; no FINAL evaluation of these frozen models exists.
- HYPOTHESIS: calendar features, rolling refits or robustness to A/D/earlier TRAIN_START will help; these remain unstarted.

VERIFIED: reported CIs are conditional on validation selection and do not adjust for tuning or multiple comparisons. Existing artificial-close, definition-break, incomplete-adjacency and earlier TEST-overlap limitations remain. No HGB/software library/network provenance was inferred from a live service.
