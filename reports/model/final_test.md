# FINAL TEST — frozen configuration

> Status: completed FINAL evaluation. This is the TEST report; selection evidence remains in validation_summary.md. The viewer displays these saved forecasts without recomputation.

VERIFIED: config commit `296573221359a2ce12d9c45e729500980807a71c`; run `final-20261012T142247472660`. TEST UTC [2026-08-01 00:00:00+00:00, 2026-09-05 05:00:00+00:00); independently trimmed source end 2026-09-05 05:28:22+00:00, floored to the hour. Target windows beyond this end are excluded per lead. TRAIN T ends exclusively at 2026-07-30 23:00:00+00:00 (25-hour embargo). HGB retains the frozen inner tails and pre-calibration refit; fitted details are in final_test_metrics.csv.

VERIFIED: single prediction per lead; no TEST tuning or settings changes. Lead 0 is separate; 1–6 primary; 12/24 secondary. Seven-day paired circular UTC blocks, seed 42, 300 draws. All regions share sampled days. Flags come from FINAL TRAIN, not TEST. Luhanska, Crimea and Sevastopol excluded.

## Pooled TEST metrics and 95% CIs

VERIFIED: lead 0; n=20280; Brier=0.05455; ECE=0.01597. BSS vs clim=0.48450 [0.39095, 0.59971]. BSS vs persistence=0.10360 [0.06498, 0.16269]. BSS vs ses=0.28549 [0.24815, 0.31028]. 

VERIFIED: lead 1; n=20256; Brier=0.08118; ECE=0.01281. BSS vs clim=0.23205 [0.11287, 0.38662]. BSS vs persistence=0.13762 [0.07900, 0.21997]. BSS vs ses=0.04891 [0.02598, 0.07380]. 

VERIFIED: lead 2; n=20232; Brier=0.08418; ECE=0.01366. BSS vs clim=0.20388 [0.08697, 0.35613]. BSS vs persistence=0.12956 [0.06534, 0.22558]. BSS vs ses=0.03189 [0.01339, 0.04976]. 

VERIFIED: lead 3; n=20208; Brier=0.08736; ECE=0.01789. BSS vs clim=0.17376 [0.07900, 0.29903]. BSS vs persistence=0.11100 [0.05672, 0.19086]. BSS vs ses=0.05576 [0.00834, 0.12672]. 

VERIFIED: lead 4; n=20184; Brier=0.08945; ECE=0.01613. BSS vs clim=0.15425 [0.06711, 0.26608]. BSS vs persistence=0.10127 [0.04823, 0.17160]. BSS vs ses=0.03764 [0.00218, 0.09393]. 

VERIFIED: lead 5; n=20160; Brier=0.09037; ECE=0.01695. BSS vs clim=0.14586 [0.05658, 0.25270]. BSS vs persistence=0.10342 [0.04418, 0.16831]. BSS vs ses=0.03157 [-0.00218, 0.08664]. 

VERIFIED: lead 6; n=20136; Brier=0.09147; ECE=0.01840. BSS vs clim=0.13574 [0.05385, 0.22668]. BSS vs persistence=0.09805 [0.04435, 0.15564]. BSS vs ses=0.02343 [-0.00134, 0.06188]. 

VERIFIED: lead 12; n=19992; Brier=0.09405; ECE=0.01428. BSS vs clim=0.11175 [0.05123, 0.17815]. BSS vs persistence=0.09134 [0.04665, 0.13721]. BSS vs ses=0.01224 [-0.00049, 0.03153]. 

VERIFIED: lead 24; n=19704; Brier=0.09718; ECE=0.02248. BSS vs clim=0.08561 [0.05413, 0.11495]. BSS vs persistence=0.06655 [0.04939, 0.08562]. BSS vs ses=0.00584 [-0.00646, 0.02096]. 

## Validation side-by-side

```text
 lead   brier  validation_brier     ece  validation_ece  bss_vs_clim  validation_bss_clim  bss_vs_persistence  validation_bss_persistence  bss_vs_ses  validation_bss_ses
    0 0.05455           0.05482 0.01597         0.01155      0.48450              0.43838             0.10360                     0.04262     0.28549             0.34881
    1 0.08118           0.08683 0.01281         0.01577      0.23205              0.11049             0.13762                     0.05369     0.04891             0.05633
    2 0.08418           0.09028 0.01366         0.01597      0.20388              0.07534             0.12956                     0.05554     0.03189             0.03350
    3 0.08736           0.09103 0.01789         0.01745      0.17376              0.06770             0.11100                     0.05338     0.05576             0.02420
    4 0.08945           0.09147 0.01613         0.01272      0.15425              0.06329             0.10127                     0.04831     0.03764             0.01179
    5 0.09037           0.09193 0.01695         0.01242      0.14586              0.05834             0.10342                     0.04495     0.03157             0.00869
    6 0.09147           0.09234 0.01840         0.01011      0.13574              0.05411             0.09805                     0.04379     0.02343             0.00590
   12 0.09405           0.09306 0.01428         0.00762      0.11175              0.04730             0.09134                     0.04443     0.01224             0.00265
   24 0.09718           0.09278 0.02248         0.01418      0.08561              0.04479             0.06655                     0.03903     0.00584             0.00498
```

VERIFIED: lead 0 TEST is worse on ECE, BSS vs SES. Different periods/base rates mean this is descriptive, not a paired significance test.
VERIFIED: lead 1 TEST is worse on BSS vs SES. Different periods/base rates mean this is descriptive, not a paired significance test.
VERIFIED: lead 2 TEST is worse on BSS vs SES. Different periods/base rates mean this is descriptive, not a paired significance test.
VERIFIED: lead 3 TEST is worse on ECE. Different periods/base rates mean this is descriptive, not a paired significance test.
VERIFIED: lead 4 TEST is worse on ECE. Different periods/base rates mean this is descriptive, not a paired significance test.
VERIFIED: lead 5 TEST is worse on ECE. Different periods/base rates mean this is descriptive, not a paired significance test.
VERIFIED: lead 6 TEST is worse on ECE. Different periods/base rates mean this is descriptive, not a paired significance test.
VERIFIED: lead 12 TEST is worse on Brier, ECE. Different periods/base rates mean this is descriptive, not a paired significance test.
VERIFIED: lead 24 TEST is worse on Brier, ECE. Different periods/base rates mean this is descriptive, not a paired significance test.

## Per-oblast TEST table

```text
 lead                  oblast  train_positive_rate  flagged   n  base_rate   brier  bss_vs_clim  bss_vs_persistence  bss_vs_ses     ece
    0        Cherkaska oblast              0.21595    False 845    0.28402 0.10552      0.49268             0.04673     0.32125 0.01037
    0     Chernihivska oblast              0.79077    False 845    0.87929 0.06785      0.40473             0.12075     0.30345 0.02870
    0     Chernivetska oblast              0.03444    False 845    0.01065 0.00717      0.35447            -0.00681     0.33513 0.00925
    0  Dnipropetrovska oblast              0.96194     True 845    0.99763 0.00394     -0.08462             0.34254    -0.41592 0.01266
    0         Donetska oblast              0.95626     True 845    0.99763 0.00291      0.28489             0.37278    -0.04601 0.00834
    0 Ivano-Frankivska oblast              0.02704     True 845    0.00592 0.00370      0.41565            -0.01818     0.39055 0.01181
    0       Kharkivska oblast              0.92457    False 845    0.99763 0.00414      0.46272             0.50492    -0.48552 0.01338
    0       Khersonska oblast              0.44653    False 845    0.47929 0.13939      0.44387             0.06909     0.30864 0.03924
    0      Khmelnytska oblast              0.05115    False 845    0.03314 0.02288      0.29313             0.00997     0.28123 0.00459
    0    Kirovohradska oblast              0.28500    False 845    0.46272 0.12659      0.54822             0.07514     0.29801 0.03055
    0               Kyiv City              0.11417    False 845    0.23314 0.09053      0.53076             0.11229     0.23360 0.02153
    0          Kyivska oblast              0.28827    False 845    0.48757 0.10075      0.65207             0.09404     0.35299 0.02762
    0          Lvivska oblast              0.02790     True 845    0.00355 0.00256      0.38060            -0.02511     0.31942 0.01279
    0      Mykolaivska oblast              0.40313    False 845    0.60473 0.15020      0.46293             0.16800     0.18545 0.08304
    0           Odeska oblast              0.36077    False 845    0.56805 0.16218      0.43752             0.15985     0.22816 0.08541
    0        Poltavska oblast              0.48752    False 845    0.56568 0.12763      0.49310             0.06578     0.34554 0.04430
    0        Rivnenska oblast              0.07147    False 845    0.02840 0.02072      0.29653             0.00833     0.27463 0.00301
    0           Sumska oblast              0.89030    False 845    0.98343 0.01454      0.41751             0.30038     0.10151 0.01178
    0      Ternopilska oblast              0.03203    False 845    0.01302 0.01078      0.18378            -0.02123     0.24822 0.00693
    0        Vinnytska oblast              0.08490    False 845    0.10888 0.05550      0.43134             0.02960     0.35975 0.01307
    0         Volynska oblast              0.04116    False 845    0.01183 0.00943      0.24889             0.00446     0.25564 0.00693
    0      Zakarpatska oblast              0.02239     True 845    0.00355 0.00256      0.34358            -0.04257     0.32030 0.01266
    0        Zaporizka oblast              0.88445    False 845    0.99053 0.00977      0.52659             0.42680    -0.00686 0.01450
    0      Zhytomyrska oblast              0.16411    False 845    0.12781 0.06791      0.39791             0.01373     0.32991 0.01224
    1        Cherkaska oblast              0.21595    False 844    0.28318 0.17228      0.16978             0.05419     0.07833 0.07070
    1     Chernihivska oblast              0.79077    False 844    0.87915 0.09923      0.12998             0.12351     0.02724 0.03410
    1     Chernivetska oblast              0.03444    False 844    0.01066 0.01127     -0.01359             0.02443    -0.02777 0.01404
    1  Dnipropetrovska oblast              0.96194     True 844    0.99763 0.00274      0.24757             0.27626    -0.12699 0.01422
    1         Donetska oblast              0.95626     True 844    0.99763 0.00261      0.35993             0.31253    -0.07352 0.01096
    1 Ivano-Frankivska oblast              0.02704     True 844    0.00592 0.00621      0.01902             0.03827    -0.01995 0.00984
    1       Kharkivska oblast              0.92457    False 844    0.99763 0.00272      0.64743             0.57006    -0.11719 0.01483
    1       Khersonska oblast              0.44670    False 844    0.47867 0.22005      0.12178             0.05138     0.05818 0.06386
    1      Khmelnytska oblast              0.05115    False 844    0.03318 0.03181      0.01827             0.04581     0.01632 0.01139
    1    Kirovohradska oblast              0.28500    False 844    0.46209 0.18933      0.32362             0.15689     0.07665 0.03028
    1               Kyiv City              0.11417    False 844    0.23223 0.13960      0.27379             0.13121     0.07703 0.06129
    1          Kyivska oblast              0.28827    False 844    0.48697 0.16895      0.41604             0.18279     0.06666 0.06950
    1          Lvivska oblast              0.02790     True 844    0.00355 0.00391      0.05334             0.03991    -0.05771 0.01091
    1      Mykolaivska oblast              0.40331    False 844    0.60427 0.19731      0.29411             0.22163     0.03725 0.03285
    1           Odeska oblast              0.36094    False 844    0.56754 0.21342      0.25928             0.22157     0.01472 0.06693
    1        Poltavska oblast              0.48752    False 844    0.56517 0.21002      0.16587             0.09677     0.05313 0.05687
    1        Rivnenska oblast              0.07147    False 844    0.02844 0.02751      0.06688             0.05043     0.00945 0.01175
    1           Sumska oblast              0.89030    False 844    0.98341 0.01649      0.33999             0.28807     0.01532 0.00884
    1      Ternopilska oblast              0.03203    False 844    0.01303 0.01369     -0.03534            -0.01895    -0.03071 0.01672
    1        Vinnytska oblast              0.08490    False 844    0.10900 0.09007      0.07812             0.10364     0.03874 0.00987
    1         Volynska oblast              0.04116    False 844    0.01185 0.01259     -0.00167            -0.00147    -0.03219 0.01570
    1      Zakarpatska oblast              0.02239     True 844    0.00355 0.00390     -0.00194            -0.00224    -0.05506 0.01072
    1        Zaporizka oblast              0.88445    False 844    0.99052 0.00923      0.55260             0.41001     0.03525 0.01661
    1      Zhytomyrska oblast              0.16411    False 844    0.12678 0.10335      0.07802             0.07895     0.04204 0.00901
    2        Cherkaska oblast              0.21595    False 843    0.28351 0.18320      0.11796             0.02829     0.04525 0.08052
    2     Chernihivska oblast              0.79077    False 843    0.87900 0.10216      0.10494             0.12310     0.01122 0.03574
    2     Chernivetska oblast              0.03444    False 843    0.01068 0.01126     -0.01187            -0.06531    -0.01577 0.01536
    2  Dnipropetrovska oblast              0.96194     True 843    0.99763 0.00272      0.25283             0.23034    -0.11867 0.01635
    2         Donetska oblast              0.95626     True 843    0.99763 0.00261      0.35975             0.32374    -0.07326 0.01369
    2 Ivano-Frankivska oblast              0.02704     True 843    0.00593 0.00616      0.02902             0.03233    -0.01106 0.01130
    2       Kharkivska oblast              0.92457    False 843    0.99763 0.00270      0.64891             0.56593    -0.11152 0.01667
    2       Khersonska oblast              0.44687    False 843    0.47805 0.23186      0.07436             0.02977     0.03349 0.07587
    2      Khmelnytska oblast              0.05115    False 843    0.03321 0.03194      0.01505            -0.00319     0.02184 0.01239
    2    Kirovohradska oblast              0.28517    False 843    0.46263 0.19732      0.29554             0.15363     0.05732 0.05288
    2               Kyiv City              0.11417    False 843    0.23250 0.14979      0.22164             0.11804     0.03905 0.07076
    2          Kyivska oblast              0.28827    False 843    0.48754 0.17855      0.38335             0.18841     0.03418 0.07122
    2          Lvivska oblast              0.02790     True 843    0.00356 0.00388      0.06150             0.04526    -0.04847 0.01242
    2      Mykolaivska oblast              0.40348    False 843    0.60380 0.20212      0.27648             0.22603     0.03496 0.04287
    2           Odeska oblast              0.36112    False 843    0.56702 0.21345      0.25860             0.22998     0.02175 0.05914
    2        Poltavska oblast              0.48752    False 843    0.56465 0.21952      0.12809             0.09129     0.02669 0.06143
    2        Rivnenska oblast              0.07147    False 843    0.02847 0.02763      0.06380             0.06059     0.01384 0.01313
    2           Sumska oblast              0.89030    False 843    0.98339 0.01662      0.33499             0.26882     0.02146 0.01031
    2      Ternopilska oblast              0.03203    False 843    0.01305 0.01369     -0.03402            -0.02938    -0.03083 0.01799
    2        Vinnytska oblast              0.08490    False 843    0.10913 0.09149      0.06460             0.04373     0.03496 0.01548
    2         Volynska oblast              0.04116    False 843    0.01186 0.01255      0.00223            -0.00643    -0.02910 0.01707
    2      Zakarpatska oblast              0.02239     True 843    0.00356 0.00387      0.00698             0.00177    -0.04561 0.01219
    2        Zaporizka oblast              0.88445    False 843    0.99051 0.00964      0.53314             0.45330     0.00368 0.01634
    2      Zhytomyrska oblast              0.16411    False 843    0.12693 0.10565      0.05841             0.06217     0.03182 0.01202
    3        Cherkaska oblast              0.21595    False 842    0.28266 0.19211      0.07291             0.02904     0.05418 0.05285
    3     Chernihivska oblast              0.79077    False 842    0.87886 0.10410      0.08865             0.09181     0.01636 0.03081
    3     Chernivetska oblast              0.03444    False 842    0.01069 0.01138     -0.02148            -0.01733    -0.05504 0.01647
    3  Dnipropetrovska oblast              0.96194     True 842    0.99762 0.00276      0.24181             0.22192    -0.15811 0.01699
    3         Donetska oblast              0.95626     True 842    0.99762 0.00267      0.34664             0.31843    -0.11160 0.01408
    3 Ivano-Frankivska oblast              0.02704     True 842    0.00594 0.00619      0.02556             0.02483    -0.04621 0.01248
    3       Kharkivska oblast              0.92457    False 842    0.99762 0.00276      0.64123             0.55661    -0.15846 0.01805
    3       Khersonska oblast              0.44705    False 842    0.47743 0.23741      0.05192             0.02466     0.03320 0.08362
    3      Khmelnytska oblast              0.05115    False 842    0.03325 0.03197      0.01544            -0.00259     0.01715 0.01266
    3    Kirovohradska oblast              0.28535    False 842    0.46200 0.20356      0.27239             0.15693     0.07230 0.04568
    3               Kyiv City              0.11417    False 842    0.23278 0.16165      0.16097             0.09007     0.07286 0.06369
    3          Kyivska oblast              0.28827    False 842    0.48812 0.18879      0.34853             0.17634     0.07853 0.09318
    3          Lvivska oblast              0.02790     True 842    0.00356 0.00389      0.06190             0.04587    -0.08655 0.01345
    3      Mykolaivska oblast              0.40365    False 842    0.60333 0.21336      0.23579             0.19565     0.08432 0.05208
    3           Odeska oblast              0.36112    False 842    0.56651 0.22263      0.22633             0.19294     0.06983 0.05537
    3        Poltavska oblast              0.48769    False 842    0.56413 0.22690      0.09863             0.05045     0.06626 0.07314
    3        Rivnenska oblast              0.07147    False 842    0.02850 0.02753      0.06789             0.04372     0.01536 0.01364
    3           Sumska oblast              0.89030    False 842    0.98337 0.01668      0.33313             0.27342    -0.00770 0.01227
    3      Ternopilska oblast              0.03203    False 842    0.01306 0.01359     -0.02563            -0.02513    -0.04463 0.01851
    3        Vinnytska oblast              0.08490    False 842    0.10926 0.09381      0.04192             0.03228     0.03883 0.02900
    3         Volynska oblast              0.04116    False 842    0.01188 0.01246      0.01028             0.00149    -0.05446 0.01729
    3      Zakarpatska oblast              0.02239     True 842    0.00356 0.00388      0.00753             0.00144    -0.08353 0.01322
    3        Zaporizka oblast              0.88462    False 842    0.99050 0.00973      0.52802             0.45851    -0.02324 0.01792
    3      Zhytomyrska oblast              0.16411    False 842    0.12708 0.10671      0.04979             0.03485     0.04557 0.01824
    4        Cherkaska oblast              0.21595    False 841    0.28300 0.19731      0.04867             0.00788     0.03371 0.05939
    4     Chernihivska oblast              0.79094    False 841    0.87872 0.10375      0.09209             0.08563     0.02223 0.01026
    4     Chernivetska oblast              0.03444    False 841    0.01070 0.01120     -0.00439            -0.00332    -0.03744 0.01456
    4  Dnipropetrovska oblast              0.96194     True 841    0.99762 0.00258      0.29182             0.27181    -0.08126 0.01277
    4         Donetska oblast              0.95626     True 841    0.99762 0.00251      0.38635             0.33532    -0.04348 0.00955
    4 Ivano-Frankivska oblast              0.02704     True 841    0.00595 0.00611      0.03843             0.03560    -0.03259 0.01171
    4       Kharkivska oblast              0.92457    False 841    0.99762 0.00255      0.66910             0.58639    -0.06758 0.01220
    4       Khersonska oblast              0.44722    False 841    0.47681 0.24072      0.03844             0.02617     0.02325 0.08641
    4      Khmelnytska oblast              0.05115    False 841    0.03329 0.03240      0.00330             0.00961     0.00665 0.01166
    4    Kirovohradska oblast              0.28552    False 841    0.46254 0.21174      0.24363             0.15239     0.03992 0.05072
    4               Kyiv City              0.11417    False 841    0.23306 0.16534      0.14276             0.07675     0.05925 0.04615
    4          Kyivska oblast              0.28827    False 841    0.48870 0.19614      0.32377             0.19177     0.04832 0.09358
    4          Lvivska oblast              0.02790     True 841    0.00357 0.00379      0.08505             0.07275    -0.05965 0.01212
    4      Mykolaivska oblast              0.40382    False 841    0.60285 0.22140      0.20655             0.17446     0.05491 0.06258
    4           Odeska oblast              0.36112    False 841    0.56599 0.22912      0.20339             0.17240     0.04667 0.06500
    4        Poltavska oblast              0.48786    False 841    0.56480 0.23156      0.08009             0.02397     0.05097 0.04897
    4        Rivnenska oblast              0.07147    False 841    0.02854 0.02778      0.06036             0.05362     0.00871 0.01168
    4           Sumska oblast              0.89030    False 841    0.98335 0.01659      0.33718             0.28883    -0.00123 0.00848
    4      Ternopilska oblast              0.03203    False 841    0.01308 0.01337     -0.00778            -0.00868    -0.02660 0.01507
    4        Vinnytska oblast              0.08490    False 841    0.10939 0.09584      0.02228             0.00902     0.02246 0.01022
    4         Volynska oblast              0.04116    False 841    0.01189 0.01217      0.03464             0.02662    -0.02862 0.01362
    4      Zakarpatska oblast              0.02239     True 841    0.00357 0.00379      0.03126             0.02538    -0.05761 0.01193
    4        Zaporizka oblast              0.88479    False 841    0.99049 0.00963      0.53232             0.44946    -0.00917 0.01434
    4      Zhytomyrska oblast              0.16411    False 841    0.12723 0.10935      0.02719             0.01427     0.02589 0.00402
    5        Cherkaska oblast              0.21612    False 840    0.28333 0.19946      0.03908            -0.00098     0.02866 0.06390
    5     Chernihivska oblast              0.79111    False 840    0.87857 0.10396      0.09075             0.07014     0.02406 0.00999
    5     Chernivetska oblast              0.03444    False 840    0.01071 0.01120     -0.00325            -0.00532    -0.03633 0.01477
    5  Dnipropetrovska oblast              0.96194     True 840    0.99762 0.00259      0.29013             0.27121    -0.08339 0.01325
    5         Donetska oblast              0.95626     True 840    0.99762 0.00251      0.38578             0.33032    -0.04391 0.00997
    5 Ivano-Frankivska oblast              0.02704     True 840    0.00595 0.00611      0.03949             0.03644    -0.03165 0.01208
    5       Kharkivska oblast              0.92457    False 840    0.99762 0.00257      0.66725             0.58413    -0.07263 0.01259
    5       Khersonska oblast              0.44722    False 840    0.47738 0.24178      0.03440             0.03336     0.02136 0.06781
    5      Khmelnytska oblast              0.05115    False 840    0.03333 0.03244      0.00296            -0.00176     0.00722 0.01095
    5    Kirovohradska oblast              0.28552    False 840    0.46310 0.21500      0.23261             0.16324     0.02901 0.05567
    5               Kyiv City              0.11434    False 840    0.23333 0.16896      0.12475             0.08661     0.04572 0.04649
    5          Kyivska oblast              0.28844    False 840    0.48929 0.19877      0.31513             0.19256     0.04054 0.08905
    5          Lvivska oblast              0.02790     True 840    0.00357 0.00380      0.08556             0.07732    -0.05897 0.01251
    5      Mykolaivska oblast              0.40382    False 840    0.60357 0.22435      0.19639             0.17732     0.04523 0.07230
    5           Odeska oblast              0.36129    False 840    0.56548 0.23119      0.19560             0.16714     0.04164 0.06082
    5        Poltavska oblast              0.48803    False 840    0.56548 0.23475      0.06739             0.03309     0.04191 0.06785
    5        Rivnenska oblast              0.07147    False 840    0.02857 0.02779      0.06103             0.05385     0.00987 0.01174
    5           Sumska oblast              0.89048    False 840    0.98333 0.01663      0.33525             0.30084    -0.00252 0.00892
    5      Ternopilska oblast              0.03203    False 840    0.01310 0.01335     -0.00496            -0.00648    -0.02390 0.01517
    5        Vinnytska oblast              0.08490    False 840    0.10952 0.09625      0.01919             0.01601     0.02130 0.01548
    5         Volynska oblast              0.04116    False 840    0.01190 0.01213      0.03837             0.03135    -0.02476 0.01376
    5      Zakarpatska oblast              0.02239     True 840    0.00357 0.00379      0.03192             0.02665    -0.05689 0.01231
    5        Zaporizka oblast              0.88497    False 840    0.99048 0.00966      0.53052             0.43798    -0.00830 0.01484
    5      Zhytomyrska oblast              0.16428    False 840    0.12738 0.10991      0.02313             0.01400     0.02415 0.00463
    6        Cherkaska oblast              0.21629    False 839    0.28367 0.20245      0.02546            -0.00457     0.01980 0.05766
    6     Chernihivska oblast              0.79129    False 839    0.87843 0.10534      0.07905             0.05407     0.01394 0.02811
    6     Chernivetska oblast              0.03444    False 839    0.01073 0.01110      0.00646             0.00391    -0.02636 0.01257
    6  Dnipropetrovska oblast              0.96211     True 839    0.99762 0.00254      0.30317             0.28447    -0.05948 0.01155
    6         Donetska oblast              0.95643     True 839    0.99762 0.00251      0.38412             0.33252    -0.04255 0.01029
    6 Ivano-Frankivska oblast              0.02704     True 839    0.00596 0.00605      0.04950             0.04708    -0.02111 0.01042
    6       Kharkivska oblast              0.92457    False 839    0.99762 0.00255      0.66991             0.59089    -0.06316 0.01244
    6       Khersonska oblast              0.44722    False 839    0.47795 0.24349      0.02784             0.03125     0.01553 0.07358
    6      Khmelnytska oblast              0.05115    False 839    0.03337 0.03240      0.00533             0.00144     0.01048 0.00784
    6    Kirovohradska oblast              0.28569    False 839    0.46365 0.21626      0.22861             0.17158     0.02636 0.05672
    6               Kyiv City              0.11452    False 839    0.23361 0.17473      0.09572             0.06180     0.01986 0.06285
    6          Kyivska oblast              0.28862    False 839    0.48987 0.20394      0.29771             0.18915     0.02069 0.08160
    6          Lvivska oblast              0.02790     True 839    0.00358 0.00374      0.09913             0.09354    -0.04317 0.01089
    6      Mykolaivska oblast              0.40382    False 839    0.60310 0.22613      0.18972             0.17007     0.04126 0.06543
    6           Odeska oblast              0.36146    False 839    0.56496 0.23152      0.19386             0.17138     0.04357 0.02451
    6        Poltavska oblast              0.48820    False 839    0.56615 0.23972      0.04760             0.02438     0.02477 0.08491
    6        Rivnenska oblast              0.07147    False 839    0.02861 0.02788      0.05901             0.05171     0.00991 0.00939
    6           Sumska oblast              0.89065    False 839    0.98331 0.01655      0.33780             0.28779     0.00295 0.00721
    6      Ternopilska oblast              0.03203    False 839    0.01311 0.01326      0.00266            -0.01942    -0.01442 0.01267
    6        Vinnytska oblast              0.08507    False 839    0.10965 0.09698      0.01278            -0.00693     0.01764 0.01432
    6         Volynska oblast              0.04116    False 839    0.01192 0.01203      0.04780             0.04116    -0.01483 0.01150
    6      Zakarpatska oblast              0.02239     True 839    0.00358 0.00374      0.04618             0.04312    -0.04131 0.01068
    6        Zaporizka oblast              0.88514    False 839    0.99046 0.00963      0.53102             0.42659    -0.00249 0.01384
    6      Zhytomyrska oblast              0.16446    False 839    0.12753 0.11077      0.01653            -0.00207     0.01993 0.01191
   12        Cherkaska oblast              0.21698    False 833    0.28571 0.20926     -0.00217            -0.01145     0.00859 0.05580
   12     Chernihivska oblast              0.79146    False 833    0.87755 0.10696      0.06880             0.06587     0.01328 0.01639
   12     Chernivetska oblast              0.03444    False 833    0.01080 0.01099      0.02301             0.02104    -0.00970 0.00936
   12  Dnipropetrovska oblast              0.96211     True 833    0.99760 0.00253      0.30710             0.28644    -0.05087 0.01039
   12         Donetska oblast              0.95643     True 833    0.99760 0.00252      0.38454             0.34260    -0.03864 0.00917
   12 Ivano-Frankivska oblast              0.02704     True 833    0.00600 0.00609      0.04940             0.04702    -0.01399 0.00887
   12       Kharkivska oblast              0.92475    False 833    0.99760 0.00252      0.67295             0.59455    -0.04463 0.01014
   12       Khersonska oblast              0.44791    False 833    0.47899 0.24533      0.02073             0.02524     0.01052 0.04709
   12      Khmelnytska oblast              0.05115    False 833    0.03361 0.03313     -0.01048            -0.00985     0.00341 0.00395
   12    Kirovohradska oblast              0.28655    False 833    0.46579 0.22118      0.21276             0.19216     0.01372 0.06032
   12               Kyiv City              0.11503    False 833    0.23409 0.18121      0.06338             0.05559     0.01387 0.07173
   12          Kyivska oblast              0.28913    False 833    0.48980 0.20982      0.27689             0.21659     0.01023 0.08476
   12          Lvivska oblast              0.02790     True 833    0.00360 0.00369      0.11727             0.11319    -0.02171 0.00871
   12      Mykolaivska oblast              0.40434    False 833    0.60144 0.23633      0.15161             0.13641     0.01983 0.05793
   12           Odeska oblast              0.36249    False 833    0.56303 0.24220      0.15385             0.12473     0.02122 0.03180
   12        Poltavska oblast              0.48889    False 833    0.56543 0.24712      0.01773             0.00625     0.01272 0.06190
   12        Rivnenska oblast              0.07147    False 833    0.02881 0.02841      0.04656             0.04089     0.00412 0.00492
   12           Sumska oblast              0.89065    False 833    0.98319 0.01669      0.33466             0.29101     0.00176 0.00689
   12      Ternopilska oblast              0.03203    False 833    0.01321 0.01327      0.00855             0.00766    -0.00551 0.00773
   12        Vinnytska oblast              0.08559    False 833    0.11044 0.09981     -0.00960            -0.01250     0.00847 0.02479
   12         Volynska oblast              0.04116    False 833    0.01200 0.01196      0.05932             0.05257    -0.00335 0.00607
   12      Zakarpatska oblast              0.02239     True 833    0.00360 0.00369      0.06450             0.06154    -0.02128 0.00864
   12        Zaporizka oblast              0.88566    False 833    0.99040 0.00976      0.52349             0.43125    -0.01042 0.01304
   12      Zhytomyrska oblast              0.16411    False 833    0.12605 0.11268     -0.00962            -0.01127     0.00757 0.02568
   24        Cherkaska oblast              0.21715    False 821    0.28867 0.21221     -0.00833            -0.01228     0.01895 0.04799
   24     Chernihivska oblast              0.79232    False 821    0.87576 0.10984      0.05116             0.04436     0.01410 0.01709
   24     Chernivetska oblast              0.03444    False 821    0.01096 0.01412     -0.23903            -0.24025    -0.28198 0.04489
   24  Dnipropetrovska oblast              0.96246     True 821    0.99756 0.00260      0.29069             0.27014    -0.06339 0.01161
   24         Donetska oblast              0.95643     True 821    0.99756 0.00257      0.37548             0.32563    -0.04748 0.01105
   24 Ivano-Frankivska oblast              0.02704     True 821    0.00609 0.00658     -0.01395            -0.01594    -0.08359 0.02238
   24       Kharkivska oblast              0.92509    False 821    0.99756 0.00254      0.66956             0.57350    -0.03798 0.01041
   24       Khersonska oblast              0.44877    False 821    0.47381 0.24671      0.01292             0.01070     0.01698 0.05932
   24      Khmelnytska oblast              0.05115    False 821    0.03410 0.03360     -0.01106            -0.01105     0.00745 0.00853
   24    Kirovohradska oblast              0.28758    False 821    0.46772 0.23888      0.15114             0.13211    -0.04681 0.09023
   24               Kyiv City              0.11538    False 821    0.23752 0.18680      0.04706             0.05270     0.02171 0.08882
   24          Kyivska oblast              0.28913    False 821    0.49452 0.23209      0.20558             0.14320    -0.06217 0.12711
   24          Lvivska oblast              0.02790     True 821    0.00365 0.00400      0.05366             0.04936    -0.09455 0.01653
   24      Mykolaivska oblast              0.40520    False 821    0.59562 0.24018      0.13328             0.11610     0.04147 0.04654
   24           Odeska oblast              0.36335    False 821    0.56516 0.24656      0.13934             0.10232     0.03602 0.04794
   24        Poltavska oblast              0.48993    False 821    0.56395 0.24956      0.00729             0.00961     0.02685 0.08673
   24        Rivnenska oblast              0.07147    False 821    0.02923 0.02912      0.03464             0.02285    -0.00091 0.01712
   24           Sumska oblast              0.89134    False 821    0.98295 0.01692      0.32749             0.28643     0.00004 0.00509
   24      Ternopilska oblast              0.03203    False 821    0.01340 0.01491     -0.09884            -0.09949    -0.11406 0.03028
   24        Vinnytska oblast              0.08593    False 821    0.11206 0.10149     -0.01301            -0.01391     0.01972 0.05562
   24         Volynska oblast              0.04116    False 821    0.01218 0.01327     -0.03097            -0.03497    -0.09283 0.03099
   24      Zakarpatska oblast              0.02239     True 821    0.00365 0.00394      0.01366             0.01163    -0.07692 0.01538
   24        Zaporizka oblast              0.88669    False 821    0.99026 0.00985      0.51666             0.43136    -0.00638 0.01105
   24      Zhytomyrska oblast              0.16428    False 821    0.12789 0.11401     -0.01020            -0.00838     0.02111 0.01895
```

VERIFIED: ALL_excl_flagged metrics and per-region CIs are in the CSVs. Existing artificial-close, prior exploratory TEST overlap, definition-break and incomplete-adjacency limitations remain. No re-tuning after TEST.
