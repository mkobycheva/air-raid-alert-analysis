# Reference validation only

> Historical validation/progress snapshot. Statements about TEST not being evaluated or later stages being unstarted describe this report’s original stage. FINAL is now complete; see [final_test.md](final_test.md). Numeric results below are preserved unchanged.

Run: 3157b3124f2a6925; git: 25e9fea78a073e1d35a5d0b9db19ba36a8fdd3a5; dirty worktree: True

Parameters: `{"alphas": [0.01, 0.05, 0.1, 0.3, 0.6], "block_days": 7, "bootstrap_samples": 300, "day_windows": [7, 14, 28], "dirty_worktree": true, "ece_bins": 10, "embargo_hours": 25, "flag_high": 0.95, "flag_low": 0.03, "fold_boundaries": ["2026-06-01", "2026-06-16", "2026-07-01", "2026-07-16", "2026-08-01"], "input_sha256": "b396f87696243069eec0219880e87dcd642b20beb0a7bae0d0e1f61e1ed20ec4", "leads": [0, 1, 2, 3, 4, 5, 6, 12, 24], "official": "data/raw/official_data_en.csv", "seed": 42, "source_sha256": "bb68e1e24ddc174b3fcce7615a6816a839078110f438d85b3c9a164c6a684773", "test_start": "2026-08-01", "train_start": "2025-12-01", "validation_label_boundary": "2026-08-01T00:00:00+00:00", "variant": "B", "week_windows": [4, 8]}`

No TEST rows or target hours were used. Labels beyond the validation boundary are missing; the last fold therefore has fewer eligible rows at longer leads. Leads are evaluated separately, including 0. Pooled BSS is computed from pooled squared errors, not averaged fold scores. Fold spread is min/max BSS vs climatology. Intervals use paired circular 7-day blocks across all oblasts; all three references and 1-day sensitivity are in bootstrap.csv. Flagging is lead/fold-specific and based only on TRAIN. Results.csv is append-only; other summaries describe this run.

```text
           model  lead            scope     n  bss_vs_clim  bss_vs_persistence  bss_vs_ses  fold_bss_min  fold_bss_max  bss_ci_low  bss_ci_high
     climatology     0              ALL 35136      0.00000            -0.70468    -0.15949       0.00000       0.00000     0.00000      0.00000
     climatology     0 ALL_excl_flagged 30696      0.00000            -0.71362    -0.16243       0.00000       0.00000     0.00000      0.00000
     climatology     1              ALL 35112      0.00000            -0.06385    -0.06088       0.00000       0.00000     0.00000      0.00000
     climatology     1 ALL_excl_flagged 30677      0.00000            -0.06504    -0.06127       0.00000       0.00000     0.00000      0.00000
     climatology     2              ALL 35088      0.00000            -0.02142    -0.04526       0.00000       0.00000     0.00000      0.00000
     climatology     2 ALL_excl_flagged 30658      0.00000            -0.02169    -0.04545       0.00000       0.00000     0.00000      0.00000
     climatology     3              ALL 35064      0.00000            -0.01536    -0.04666       0.00000       0.00000     0.00000      0.00000
     climatology     3 ALL_excl_flagged 30639      0.00000            -0.01552    -0.04660       0.00000       0.00000     0.00000      0.00000
     climatology     4              ALL 35040      0.00000            -0.01600    -0.05498       0.00000       0.00000     0.00000      0.00000
     climatology     4 ALL_excl_flagged 30620      0.00000            -0.01624    -0.05501       0.00000       0.00000     0.00000      0.00000
     climatology     5              ALL 35016      0.00000            -0.01422    -0.05273       0.00000       0.00000     0.00000      0.00000
     climatology     5 ALL_excl_flagged 30601      0.00000            -0.01446    -0.05272       0.00000       0.00000     0.00000      0.00000
     climatology     6              ALL 34992      0.00000            -0.01091    -0.05097       0.00000       0.00000     0.00000      0.00000
     climatology     6 ALL_excl_flagged 30582      0.00000            -0.01105    -0.05096       0.00000       0.00000     0.00000      0.00000
     climatology    12              ALL 34848      0.00000            -0.00301    -0.04687       0.00000       0.00000     0.00000      0.00000
     climatology    12 ALL_excl_flagged 30468      0.00000            -0.00305    -0.04685       0.00000       0.00000     0.00000      0.00000
     climatology    24              ALL 34560      0.00000            -0.00603    -0.04167       0.00000       0.00000     0.00000      0.00000
     climatology    24 ALL_excl_flagged 30240      0.00000            -0.00607    -0.04159       0.00000       0.00000     0.00000      0.00000
persistence_hard     0              ALL 35136      0.14769            -0.45291     0.01176       0.11136       0.18131     0.09295      0.20009
persistence_hard     0 ALL_excl_flagged 30696      0.17273            -0.41762     0.03836       0.13778       0.21781     0.12588      0.21923
persistence_hard     1              ALL 35112     -0.53605            -0.63412    -0.62957      -0.61937      -0.49073    -0.62908     -0.44405
persistence_hard     1 ALL_excl_flagged 30677     -0.50365            -0.60144    -0.59578      -0.57907      -0.46406    -0.58975     -0.41780
persistence_hard     2              ALL 35088     -0.69999            -0.73640    -0.77692      -0.78732      -0.58963    -0.80175     -0.60678
persistence_hard     2 ALL_excl_flagged 30658     -0.66755            -0.70373    -0.74334      -0.74424      -0.56725    -0.76456     -0.58129
persistence_hard     3              ALL 35064     -0.74542            -0.77222    -0.82685      -0.81647      -0.63063    -0.84803     -0.65247
persistence_hard     3 ALL_excl_flagged 30639     -0.71361            -0.74020    -0.79347      -0.77397      -0.60902    -0.80984     -0.62672
persistence_hard     4              ALL 35040     -0.75448            -0.78254    -0.85094      -0.80067      -0.69584    -0.82620     -0.68588
persistence_hard     4 ALL_excl_flagged 30620     -0.72278            -0.75076    -0.81755      -0.75985      -0.67297    -0.79043     -0.65992
persistence_hard     5              ALL 35016     -0.77281            -0.79801    -0.86628      -0.83366      -0.69699    -0.83142     -0.71177
persistence_hard     5 ALL_excl_flagged 30601     -0.74193            -0.76712    -0.83377      -0.79347      -0.67415    -0.79361     -0.68591
persistence_hard     6              ALL 34992     -0.79972            -0.81935    -0.89146      -0.88978      -0.69219    -0.86281     -0.73161
persistence_hard     6 ALL_excl_flagged 30582     -0.76978            -0.78934    -0.85998      -0.85296      -0.66926    -0.83252     -0.70691
persistence_hard    12              ALL 34848     -0.88692            -0.89260    -0.97535      -0.94890      -0.74780    -0.95959     -0.82022
persistence_hard    12 ALL_excl_flagged 30468     -0.85812            -0.86378    -0.94517      -0.93419      -0.72842    -0.92594     -0.79780
persistence_hard    24              ALL 34560     -0.86345            -0.87468    -0.94110      -0.95132      -0.80412    -0.90376     -0.82356
persistence_hard    24 ALL_excl_flagged 30240     -0.83506            -0.84620    -0.91137      -0.90735      -0.78815    -0.87111     -0.79923
persistence_prob     0              ALL 35136      0.41338             0.00000     0.31982       0.37921       0.44525     0.38286      0.44472
persistence_prob     0 ALL_excl_flagged 30696      0.41644             0.00000     0.32165       0.38347       0.44952     0.38732      0.44701
persistence_prob     1              ALL 35112      0.06002             0.00000     0.00279       0.04364       0.08013     0.02940      0.09451
persistence_prob     1 ALL_excl_flagged 30677      0.06107             0.00000     0.00354       0.04458       0.08104     0.03023      0.09586
persistence_prob     2              ALL 35088      0.02097             0.00000    -0.02334       0.00865       0.03368    -0.00373      0.04410
persistence_prob     2 ALL_excl_flagged 30658      0.02123             0.00000    -0.02325       0.00856       0.03401    -0.00384      0.04459
persistence_prob     3              ALL 35064      0.01513             0.00000    -0.03083       0.00775       0.02499    -0.00541      0.03335
persistence_prob     3 ALL_excl_flagged 30639      0.01528             0.00000    -0.03061       0.00768       0.02523    -0.00556      0.03364
persistence_prob     4              ALL 35040      0.01574             0.00000    -0.03837       0.01067       0.02278     0.00369      0.02705
persistence_prob     4 ALL_excl_flagged 30620      0.01598             0.00000    -0.03815       0.01061       0.02304     0.00374      0.02758
persistence_prob     5              ALL 35016      0.01402             0.00000    -0.03797       0.00976       0.02182     0.00653      0.02171
persistence_prob     5 ALL_excl_flagged 30601      0.01425             0.00000    -0.03772       0.00970       0.02199     0.00674      0.02189
persistence_prob     6              ALL 34992      0.01079             0.00000    -0.03963       0.00359       0.02303     0.00272      0.01827
persistence_prob     6 ALL_excl_flagged 30582      0.01093             0.00000    -0.03948       0.00361       0.02321     0.00279      0.01850
persistence_prob    12              ALL 34848      0.00300             0.00000    -0.04372      -0.00243       0.00891    -0.00168      0.00696
persistence_prob    12 ALL_excl_flagged 30468      0.00304             0.00000    -0.04367      -0.00253       0.00903    -0.00170      0.00698
persistence_prob    24              ALL 34560      0.00599             0.00000    -0.03543       0.00073       0.01264     0.00055      0.01159
persistence_prob    24 ALL_excl_flagged 30240      0.00604             0.00000    -0.03530       0.00069       0.01262     0.00050      0.01163
    seasonal_day     0              ALL 35136      0.01620            -0.67706    -0.14070      -0.01259       0.05250    -0.00642      0.03822
    seasonal_day     0 ALL_excl_flagged 30696      0.01618            -0.68589    -0.14362      -0.01359       0.05318    -0.00651      0.03840
    seasonal_day     1              ALL 35112      0.01625            -0.04656    -0.04365      -0.01164       0.05230    -0.00669      0.03826
    seasonal_day     1 ALL_excl_flagged 30677      0.01622            -0.04776    -0.04406      -0.01263       0.05298    -0.00691      0.03834
    seasonal_day     2              ALL 35088      0.01618            -0.00489    -0.02834      -0.01105       0.05241    -0.00677      0.03844
    seasonal_day     2 ALL_excl_flagged 30658      0.01615            -0.00519    -0.02856      -0.01202       0.05309    -0.00699      0.03868
    seasonal_day     3              ALL 35064      0.01609             0.00098    -0.02982      -0.01086       0.05269    -0.00688      0.03802
    seasonal_day     3 ALL_excl_flagged 30639      0.01606             0.00079    -0.02980      -0.01184       0.05338    -0.00710      0.03850
    seasonal_day     4              ALL 35040      0.01581             0.00007    -0.03830      -0.01052       0.05350    -0.00774      0.03790
    seasonal_day     4 ALL_excl_flagged 30620      0.01578            -0.00020    -0.03836      -0.01148       0.05422    -0.00810      0.03838
    seasonal_day     5              ALL 35016      0.01559             0.00159    -0.03632      -0.00987       0.05381    -0.00722      0.03787
    seasonal_day     5 ALL_excl_flagged 30601      0.01555             0.00132    -0.03635      -0.01083       0.05455    -0.00784      0.03821
    seasonal_day     6              ALL 34992      0.01555             0.00481    -0.03463      -0.00978       0.05405    -0.00753      0.03804
    seasonal_day     6 ALL_excl_flagged 30582      0.01552             0.00465    -0.03465      -0.01072       0.05479    -0.00822      0.03844
    seasonal_day    12              ALL 34848      0.01620             0.01323    -0.02991      -0.01177       0.05322    -0.00756      0.03967
    seasonal_day    12 ALL_excl_flagged 30468      0.01617             0.01317    -0.02992      -0.01277       0.05398    -0.00831      0.03988
    seasonal_day    24              ALL 34560      0.00993             0.00396    -0.03133      -0.02172       0.04758    -0.01217      0.03380
    seasonal_day    24 ALL_excl_flagged 30240      0.00985             0.00383    -0.03133      -0.02065       0.04822    -0.01250      0.03446
   seasonal_week     0              ALL 35136     -0.08938            -0.85705    -0.26313      -0.11821      -0.05302    -0.10853     -0.07118
   seasonal_week     0 ALL_excl_flagged 30696     -0.08695            -0.86262    -0.26351      -0.11520      -0.05048    -0.10520     -0.06937
   seasonal_week     1              ALL 35112     -0.08939            -0.15894    -0.15572      -0.11896      -0.05340    -0.10819     -0.07045
   seasonal_week     1 ALL_excl_flagged 30677     -0.08696            -0.15765    -0.15355      -0.11594      -0.05086    -0.10483     -0.06851
   seasonal_week     2              ALL 35088     -0.08966            -0.11300    -0.13897      -0.12101      -0.05226    -0.10810     -0.07024
   seasonal_week     2 ALL_excl_flagged 30658     -0.08723            -0.11081    -0.13664      -0.11800      -0.04968    -0.10525     -0.06818
   seasonal_week     3              ALL 35064     -0.08969            -0.10642    -0.14053      -0.12154      -0.05216    -0.10892     -0.07017
   seasonal_week     3 ALL_excl_flagged 30639     -0.08725            -0.10413    -0.13792      -0.11853      -0.04957    -0.10623     -0.06750
   seasonal_week     4              ALL 35040     -0.08988            -0.10731    -0.14980      -0.12204      -0.05195    -0.10965     -0.06971
   seasonal_week     4 ALL_excl_flagged 30620     -0.08744            -0.10510    -0.14727      -0.11903      -0.04934    -0.10725     -0.06705
   seasonal_week     5              ALL 35016     -0.09014            -0.10564    -0.14762      -0.12345      -0.05268    -0.11073     -0.06962
   seasonal_week     5 ALL_excl_flagged 30601     -0.08771            -0.10344    -0.14506      -0.12046      -0.05009    -0.10830     -0.06698
   seasonal_week     6              ALL 34992     -0.09038            -0.10228    -0.14596      -0.12445      -0.05285    -0.11126     -0.06964
   seasonal_week     6 ALL_excl_flagged 30582     -0.08797            -0.09999    -0.14342      -0.12153      -0.05027    -0.10828     -0.06749
   seasonal_week    12              ALL 34848     -0.09004            -0.09333    -0.14113      -0.12416      -0.05367    -0.11053     -0.07130
   seasonal_week    12 ALL_excl_flagged 30468     -0.08768            -0.09099    -0.13863      -0.12128      -0.05104    -0.10786     -0.06940
   seasonal_week    24              ALL 34560     -0.08876            -0.09532    -0.13413      -0.11517      -0.05534    -0.10658     -0.07031
   seasonal_week    24 ALL_excl_flagged 30240     -0.08642            -0.09302    -0.13160      -0.11219      -0.05266    -0.10397     -0.06808
             ses     0              ALL 35136      0.13755            -0.47021     0.00000       0.09464       0.17820     0.10201      0.17344
             ses     0 ALL_excl_flagged 30696      0.13973            -0.47417     0.00000       0.09509       0.17979     0.10371      0.17547
             ses     1              ALL 35112      0.05739            -0.00279     0.00000       0.03070       0.07550     0.03882      0.07664
             ses     1 ALL_excl_flagged 30677      0.05773            -0.00355     0.00000       0.03015       0.07552     0.03892      0.07706
             ses     2              ALL 35088      0.04330             0.02280     0.00000       0.01751       0.06117     0.02463      0.06197
             ses     2 ALL_excl_flagged 30658      0.04347             0.02272     0.00000       0.01691       0.06230     0.02454      0.06226
             ses     3              ALL 35064      0.04458             0.02990     0.00000       0.01030       0.07943     0.02032      0.06743
             ses     3 ALL_excl_flagged 30639      0.04453             0.02970     0.00000       0.00966       0.08024     0.02004      0.06720
             ses     4              ALL 35040      0.05212             0.03695     0.00000       0.03056       0.07754     0.02963      0.07294
             ses     4 ALL_excl_flagged 30620      0.05214             0.03675     0.00000       0.03094       0.07830     0.02953      0.07280
             ses     5              ALL 35016      0.05009             0.03658     0.00000       0.02881       0.07561     0.02774      0.07187
             ses     5 ALL_excl_flagged 30601      0.05008             0.03635     0.00000       0.02915       0.07633     0.02762      0.07189
             ses     6              ALL 34992      0.04850             0.03812     0.00000       0.02687       0.07474     0.02597      0.07048
             ses     6 ALL_excl_flagged 30582      0.04849             0.03798     0.00000       0.02720       0.07547     0.02587      0.07057
             ses    12              ALL 34848      0.04477             0.04189     0.00000       0.01606       0.07644     0.01972      0.06873
             ses    12 ALL_excl_flagged 30468      0.04475             0.04184     0.00000       0.01631       0.07729     0.01964      0.06893
             ses    24              ALL 34560      0.04000             0.03422     0.00000       0.00923       0.07142     0.01352      0.06328
             ses    24 ALL_excl_flagged 30240      0.03993             0.03409     0.00000       0.00934       0.07210     0.01345      0.06336
```
