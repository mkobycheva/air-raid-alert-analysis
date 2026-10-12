# Step recency: validation only

VERIFIED: run c1c884d499a8a449; 25-hour embargo, independent fold fits, pooled TRAIN, no class resampling, no calendar/identity/STL features, no TEST.

C is chosen across the four VALID folds for each lead, not separately on each fold. Recency fixes the previous selected C and selects half-life on VALID. These validation-selected metrics are descriptive selection scores, not unbiased final performance. CI uses paired circular seven-day UTC blocks; one-day sensitivity and all three references are in the bootstrap table. Per-region and excluded-flagged metrics are logged.

```text
          model  lead   brier  bss_vs_clim  bss_vs_persistence  bss_vs_ses  bss_ci_low  bss_ci_high     ece
  logreg_A_hl14     0 0.05555      0.43091             0.02988     0.34014     0.40367      0.45940 0.01899
  logreg_A_hl30     0 0.05506      0.43589             0.03838     0.34593     0.40882      0.46439 0.01575
  logreg_A_hl60     0 0.05495      0.43702             0.04029     0.34723     0.40988      0.46530 0.01385
 logreg_A_hlinf     0 0.05504      0.43616             0.03882     0.34623     0.40876      0.46426 0.01365
 logreg_AB_hl14     1 0.08746      0.10409             0.04688     0.04954     0.06938      0.14269 0.02709
 logreg_AB_hl30     1 0.08752      0.10347             0.04623     0.04889     0.06906      0.14247 0.02770
 logreg_AB_hl60     1 0.08765      0.10214             0.04481     0.04747     0.06791      0.14139 0.02817
logreg_AB_hlinf     1 0.08792      0.09940             0.04190     0.04457     0.06550      0.13923 0.02906
 logreg_AB_hl14     2 0.09084      0.06965             0.04973     0.02755     0.04540      0.09382 0.02385
 logreg_AB_hl30     2 0.09095      0.06846             0.04851     0.02630     0.04428      0.09210 0.02596
 logreg_AB_hl60     2 0.09106      0.06735             0.04738     0.02515     0.04359      0.09110 0.02746
logreg_AB_hlinf     2 0.09127      0.06520             0.04517     0.02289     0.04115      0.08889 0.02874
 logreg_AB_hl14     3 0.09185      0.05940             0.04495     0.01551     0.03809      0.08067 0.02505
 logreg_AB_hl30     3 0.09172      0.06067             0.04625     0.01685     0.04102      0.08082 0.02470
 logreg_AB_hl60     3 0.09179      0.05999             0.04555     0.01613     0.04108      0.07953 0.02619
logreg_AB_hlinf     3 0.09200      0.05783             0.04336     0.01388     0.03930      0.07690 0.02813
 logreg_AB_hl14     4 0.09251      0.05258             0.03742     0.00049     0.03653      0.07000 0.02377
 logreg_AB_hl30     4 0.09250      0.05271             0.03756     0.00062     0.03648      0.06954 0.02514
 logreg_AB_hl60     4 0.09261      0.05162             0.03645    -0.00052     0.03536      0.06817 0.02656
logreg_AB_hlinf     4 0.09286      0.04899             0.03378    -0.00330     0.03325      0.06518 0.02824
 logreg_AB_hl14     5 0.09303      0.04704             0.03349    -0.00321     0.03103      0.06274 0.02290
 logreg_AB_hl30     5 0.09298      0.04750             0.03395    -0.00273     0.03196      0.06249 0.02337
 logreg_AB_hl60     5 0.09309      0.04642             0.03287    -0.00386     0.03152      0.06095 0.02562
logreg_AB_hlinf     5 0.09335      0.04377             0.03017    -0.00665     0.02941      0.05791 0.02784
 logreg_AB_hl14     6 0.09338      0.04349             0.03306    -0.00526     0.02767      0.05818 0.02027
 logreg_AB_hl30     6 0.09342      0.04306             0.03262    -0.00572     0.02847      0.05710 0.02381
 logreg_AB_hl60     6 0.09351      0.04211             0.03166    -0.00672     0.02844      0.05558 0.02628
logreg_AB_hlinf     6 0.09374      0.03981             0.02934    -0.00913     0.02648      0.05285 0.02997
  logreg_A_hl14    12 0.09608      0.01634             0.01338    -0.02976    -0.00990      0.03895 0.02294
  logreg_A_hl30    12 0.09600      0.01716             0.01420    -0.02890    -0.00965      0.03871 0.02450
  logreg_A_hl60    12 0.09599      0.01729             0.01432    -0.02877    -0.00901      0.03804 0.02615
 logreg_A_hlinf    12 0.09601      0.01712             0.01416    -0.02894    -0.00807      0.03742 0.02881
  logreg_A_hl14    24 0.09627      0.00885             0.00288    -0.03246    -0.02335      0.03575 0.02315
  logreg_A_hl30    24 0.09621      0.00945             0.00348    -0.03182    -0.02179      0.03459 0.02401
  logreg_A_hl60    24 0.09619      0.00960             0.00363    -0.03167    -0.01987      0.03360 0.02556
 logreg_A_hlinf    24 0.09618      0.00974             0.00378    -0.03152    -0.01774      0.03239 0.02848
```

```text
 lead          model    brier     C half_life base_model  relative_brier_gain_vs_base    ci_low  ci_high           run_id
    0  logreg_A_hl60 0.054951  0.01      60.0   logreg_A                     0.001524 -0.000789 0.003807 c1c884d499a8a449
    1 logreg_AB_hl14 0.087459  0.01      14.0  logreg_AB                     0.005204  0.000543 0.009566 c1c884d499a8a449
    2 logreg_AB_hl14 0.090837  0.10      14.0  logreg_AB                     0.004769  0.000696 0.009222 c1c884d499a8a449
    3 logreg_AB_hl30 0.091721  0.01      30.0  logreg_AB                     0.003011  0.000751 0.005258 c1c884d499a8a449
    4 logreg_AB_hl30 0.092499  0.01      30.0  logreg_AB                     0.003913  0.001518 0.005857 c1c884d499a8a449
    5 logreg_AB_hl30 0.092985  0.01      30.0  logreg_AB                     0.003901  0.001566 0.006145 c1c884d499a8a449
    6 logreg_AB_hl14 0.093379  0.10      14.0  logreg_AB                     0.003833  0.000095 0.007722 c1c884d499a8a449
   12  logreg_A_hl60 0.095992 10.00      60.0   logreg_A                     0.000168 -0.001275 0.001687 c1c884d499a8a449
   24 logreg_A_hlinf 0.096180  1.00       inf   logreg_A                     0.000000  0.000000 0.000000 c1c884d499a8a449
```
