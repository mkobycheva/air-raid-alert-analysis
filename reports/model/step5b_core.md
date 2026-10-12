# Task 5B: steps 0–2 only

VERIFIED: run 3157b3124f2a6925, common 25-hour embargo; 80 passed, 12 skipped (UPSTREAM_DIR absent). Seven-day paired circular blocks, seed 42, 300 samples; one-day sensitivity in bootstrap.csv. No TEST evaluation. No classifier run.

VERIFIED: latest_results keeps newest run_id per (model,fold_id,lead), retaining all scopes; stale records stay in results.csv. Legacy 28,080 records retain original field values/order; additive SES column is blank in legacy rows.

VERIFIED: pooled validation BSS versus climatology, calculated as 1−sum(n×BS_model)/sum(n×BS_climatology) across the latest ALL fold rows in results.csv; verified equal to reference_validation.csv. Lead 0 is separate; 12/24 are secondary.

```text
model  climatology  persistence_hard  persistence_prob  seasonal_day  seasonal_week      ses
lead                                                                                        
0              0.0           0.14769           0.41338       0.01620       -0.08938  0.13755
1              0.0          -0.53605           0.06002       0.01625       -0.08939  0.05739
2              0.0          -0.69999           0.02097       0.01618       -0.08966  0.04330
3              0.0          -0.74542           0.01513       0.01609       -0.08969  0.04458
4              0.0          -0.75448           0.01574       0.01581       -0.08988  0.05212
5              0.0          -0.77281           0.01402       0.01559       -0.09014  0.05009
6              0.0          -0.79972           0.01079       0.01555       -0.09038  0.04850
12             0.0          -0.88692           0.00300       0.01620       -0.09004  0.04477
24             0.0          -0.86345           0.00599       0.00993       -0.08876  0.04000
```

VERIFIED: STL strengths (180 complete first-fold TRAIN days; descriptive, two-sided):

```text
                series  n_days  period_days     F_T     F_S
              NATIONAL     180            7 0.14525 0.00000
Dnipropetrovska oblast     180            7 0.07458 0.00000
  Kirovohradska oblast     180            7 0.15339 0.07648
    Zakarpatska oblast     180            7 0.01088 0.04565
```

VERIFIED: Group A/B only; real-file smoke check: 24 regions × 13 finite feature values at 2026-06-01 12:00 UTC. No step-2 validation score exists. Unknown endings are masked; future-perturbation tests pass. No unusually high long-lead reference skill was observed; embargo and label cap checks pass.

HYPOTHESIS / NEEDS HUMAN REVIEW: administrative neighbors below. Exact keys/symmetry/no self-links are VERIFIED; geographic correctness is unverified. Kyiv City uses the enclosing-oblast link. Steps 3 onward await confirmation.

```python
NEIGHBORS = {
    'Cherkaska oblast': ('Kirovohradska oblast', 'Kyivska oblast', 'Poltavska oblast', 'Vinnytska oblast'),
    'Chernihivska oblast': ('Kyivska oblast', 'Poltavska oblast', 'Sumska oblast'),
    'Chernivetska oblast': ('Ivano-Frankivska oblast', 'Khmelnytska oblast', 'Ternopilska oblast', 'Vinnytska oblast'),
    'Dnipropetrovska oblast': ('Donetska oblast', 'Kharkivska oblast', 'Khersonska oblast', 'Kirovohradska oblast', 'Mykolaivska oblast', 'Poltavska oblast', 'Zaporizka oblast'),
    'Donetska oblast': ('Dnipropetrovska oblast', 'Kharkivska oblast', 'Zaporizka oblast'),
    'Ivano-Frankivska oblast': ('Chernivetska oblast', 'Lvivska oblast', 'Ternopilska oblast', 'Zakarpatska oblast'),
    'Kharkivska oblast': ('Dnipropetrovska oblast', 'Donetska oblast', 'Poltavska oblast', 'Sumska oblast'),
    'Khersonska oblast': ('Dnipropetrovska oblast', 'Mykolaivska oblast', 'Zaporizka oblast'),
    'Khmelnytska oblast': ('Chernivetska oblast', 'Rivnenska oblast', 'Ternopilska oblast', 'Vinnytska oblast', 'Zhytomyrska oblast'),
    'Kirovohradska oblast': ('Cherkaska oblast', 'Dnipropetrovska oblast', 'Mykolaivska oblast', 'Odeska oblast', 'Poltavska oblast', 'Vinnytska oblast'),
    'Kyiv City': ('Kyivska oblast',),
    'Kyivska oblast': ('Cherkaska oblast', 'Chernihivska oblast', 'Kyiv City', 'Poltavska oblast', 'Vinnytska oblast', 'Zhytomyrska oblast'),
    'Lvivska oblast': ('Ivano-Frankivska oblast', 'Rivnenska oblast', 'Ternopilska oblast', 'Volynska oblast', 'Zakarpatska oblast'),
    'Mykolaivska oblast': ('Dnipropetrovska oblast', 'Khersonska oblast', 'Kirovohradska oblast', 'Odeska oblast'),
    'Odeska oblast': ('Kirovohradska oblast', 'Mykolaivska oblast', 'Vinnytska oblast'),
    'Poltavska oblast': ('Cherkaska oblast', 'Chernihivska oblast', 'Dnipropetrovska oblast', 'Kharkivska oblast', 'Kirovohradska oblast', 'Kyivska oblast', 'Sumska oblast'),
    'Rivnenska oblast': ('Khmelnytska oblast', 'Lvivska oblast', 'Ternopilska oblast', 'Volynska oblast', 'Zhytomyrska oblast'),
    'Sumska oblast': ('Chernihivska oblast', 'Kharkivska oblast', 'Poltavska oblast'),
    'Ternopilska oblast': ('Chernivetska oblast', 'Ivano-Frankivska oblast', 'Khmelnytska oblast', 'Lvivska oblast', 'Rivnenska oblast'),
    'Vinnytska oblast': ('Cherkaska oblast', 'Chernivetska oblast', 'Khmelnytska oblast', 'Kirovohradska oblast', 'Kyivska oblast', 'Odeska oblast', 'Zhytomyrska oblast'),
    'Volynska oblast': ('Lvivska oblast', 'Rivnenska oblast'),
    'Zakarpatska oblast': ('Ivano-Frankivska oblast', 'Lvivska oblast'),
    'Zaporizka oblast': ('Dnipropetrovska oblast', 'Donetska oblast', 'Khersonska oblast'),
    'Zhytomyrska oblast': ('Khmelnytska oblast', 'Kyivska oblast', 'Rivnenska oblast', 'Vinnytska oblast'),
}
```

VERIFIED: computation/notebook cells ran on installed Python 3.12 statsmodels; PNG rendering ran on cached Python 3.13 matplotlib; tests ran on Python 3.14. No network or credential access. Those EDA dependencies are not installed in the Python 3.14 venv; execution there remains unverified. The pre-existing root eda.ipynb was left intact.
