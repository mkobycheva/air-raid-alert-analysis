# Step AB: validation only

> Historical validation/progress snapshot. Statements about TEST not being evaluated or later stages being unstarted describe this report’s original stage. FINAL is now complete; see [final_test.md](final_test.md). Numeric results below are preserved unchanged.

VERIFIED: run 49c1b9df8760bf2f; 25-hour embargo, independent fold fits, pooled TRAIN, no class resampling, no calendar/identity/STL features, no TEST.

C is chosen across the four VALID folds for each lead, not separately on each fold. Recency fixes the previous selected C and selects half-life on VALID. These validation-selected metrics are descriptive selection scores, not unbiased final performance. CI uses paired circular seven-day UTC blocks; one-day sensitivity and all three references are in the bootstrap table. Per-region and excluded-flagged metrics are logged.

```text
              model  lead   brier  bss_vs_clim  bss_vs_persistence  bss_vs_ses  bss_ci_low  bss_ci_high     ece
          logreg_AB     0 0.05481      0.43842             0.04269     0.34886     0.40924      0.47007 0.01335
logreg_AB_neighbors     0 0.05475      0.43912             0.04388     0.34967     0.40973      0.46957 0.01138
 logreg_AB_national     0 0.05503      0.43622             0.03893     0.34630     0.40876      0.46594 0.01216
     logreg_AB_base     0 0.05499      0.43664             0.03965     0.34679     0.40855      0.46572 0.01538
          logreg_AB     1 0.08792      0.09940             0.04190     0.04457     0.06550      0.13923 0.02906
logreg_AB_neighbors     1 0.08831      0.09534             0.03758     0.04026     0.06218      0.13441 0.02763
 logreg_AB_national     1 0.08828      0.09566             0.03792     0.04060     0.06413      0.13237 0.02708
     logreg_AB_base     1 0.08864      0.09196             0.03399     0.03668     0.06361      0.12635 0.03092
          logreg_AB     2 0.09127      0.06520             0.04517     0.02289     0.04115      0.08889 0.02874
logreg_AB_neighbors     2 0.09180      0.05978             0.03964     0.01723     0.03650      0.08299 0.02791
 logreg_AB_national     2 0.09175      0.06029             0.04016     0.01776     0.03949      0.08138 0.02581
     logreg_AB_base     2 0.09203      0.05748             0.03729     0.01483     0.03682      0.07782 0.03061
          logreg_AB     3 0.09200      0.05783             0.04336     0.01388     0.03930      0.07690 0.02813
logreg_AB_neighbors     3 0.09245      0.05323             0.03869     0.00906     0.03406      0.07354 0.02555
 logreg_AB_national     3 0.09257      0.05193             0.03737     0.00769     0.03433      0.06952 0.02399
     logreg_AB_base     3 0.09270      0.05068             0.03610     0.00639     0.03679      0.06605 0.02941
          logreg_AB     4 0.09286      0.04899             0.03378    -0.00330     0.03325      0.06518 0.02824
logreg_AB_neighbors     4 0.09312      0.04634             0.03108    -0.00610     0.02929      0.06345 0.02415
 logreg_AB_national     4 0.09342      0.04331             0.02801    -0.00929     0.02545      0.06047 0.02398
     logreg_AB_base     4 0.09303      0.04727             0.03203    -0.00511     0.03361      0.06016 0.02910
          logreg_AB     5 0.09335      0.04377             0.03017    -0.00665     0.02941      0.05791 0.02784
logreg_AB_neighbors     5 0.09360      0.04121             0.02758    -0.00935     0.02497      0.05708 0.02405
 logreg_AB_national     5 0.09396      0.03753             0.02384    -0.01322     0.02076      0.05346 0.02379
     logreg_AB_base     5 0.09353      0.04190             0.02828    -0.00862     0.02909      0.05376 0.02958
          logreg_AB     6 0.09374      0.03981             0.02934    -0.00913     0.02648      0.05285 0.02997
logreg_AB_neighbors     6 0.09407      0.03642             0.02590    -0.01270     0.02016      0.05174 0.02469
 logreg_AB_national     6 0.09446      0.03243             0.02187    -0.01689     0.01504      0.04763 0.02403
     logreg_AB_base     6 0.09409      0.03625             0.02574    -0.01287     0.02204      0.04894 0.03153
          logreg_AB    12 0.09518      0.02558             0.02264    -0.02009     0.00962      0.04001 0.03443
logreg_AB_neighbors    12 0.09557      0.02163             0.01868    -0.02422    -0.00106      0.04125 0.02888
 logreg_AB_national    12 0.09598      0.01736             0.01440    -0.02869    -0.00771      0.03758 0.02857
     logreg_AB_base    12 0.09530      0.02437             0.02143    -0.02136     0.00683      0.03946 0.03506
          logreg_AB    24 0.09556      0.01617             0.01024    -0.02483    -0.00073      0.02989 0.03626
logreg_AB_neighbors    24 0.09604      0.01120             0.00524    -0.03000    -0.01365      0.03203 0.03181
 logreg_AB_national    24 0.09617      0.00989             0.00393    -0.03137    -0.01710      0.03256 0.02827
     logreg_AB_base    24 0.09543      0.01741             0.01149    -0.02353     0.00005      0.03351 0.03814
```

```text
 lead  relative_brier_gain_vs_A    ci_low  ci_high  keep_context                   decision           run_id
    0                  0.004023 -0.006054 0.013975         False no evidence of improvement 49c1b9df8760bf2f
    1                  0.010262  0.000645 0.020713          True                improvement 49c1b9df8760bf2f
    2                  0.011275  0.001634 0.020618          True                improvement 49c1b9df8760bf2f
    3                  0.011288  0.002113 0.019024          True                improvement 49c1b9df8760bf2f
    4                  0.006336  0.000626 0.012019          True                improvement 49c1b9df8760bf2f
    5                  0.006991  0.000732 0.012913          True                improvement 49c1b9df8760bf2f
    6                  0.009409  0.002923 0.016336          True                improvement 49c1b9df8760bf2f
   12                  0.008603 -0.000724 0.018027         False no evidence of improvement 49c1b9df8760bf2f
   24                  0.006489 -0.005147 0.018128         False no evidence of improvement 49c1b9df8760bf2f
```
