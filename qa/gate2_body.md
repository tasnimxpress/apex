## GATE 2 — Analysis (`analysis/`)

**Date:** 2026-06-16 · **Validator:** Agent 3 · **Principle:** reproduce, don't trust.
Every metric below was recomputed directly from `clean/` by `qa/gate2_checks.py` and compared
to the notebook-persisted `analysis/<section>/_metrics.json` (tol 0.5%).

| ID | Check | Result | Evidence (recomputed) |
|----|-------|--------|-----------------------|
| G2-1a | net_flow column == purchase-surrender (dividends excluded) | **PASS** | max abs diff=0.000000 |
| G2-1b | total net flow ties tx (Purchase-Surrender) | **PASS** | mf=2492638204.64 tx=2492638204.64 |
| G2-1c | per-fund net flow value reproduced | **PASS** | Fixed:81.7Cr; Shariah:74.3Cr; Balanced:25.1Cr; Capital:68.1Cr |
| G2-2a | per-fund closure/discontinuation/strict-churn reproduced | **PASS** | Fixed churn=0.160; Shariah churn=0.375; Balanced churn=0.337; Capital churn=0.472 |
| G2-2b | rate sanity: active+inactive+churn==100%, all rates in [0,1] | **PASS** | all fund status-shares sum to 1.0; no rate <0 or >1 |
| G3-1 | case cohort denominator (2024-05) reproduced | **PASS** | recomputed=136 persisted=136 |
| G3-2 | case cohort numerator (retained @2025-05, point-in-time) reproduced | **PASS** | recomputed=115 persisted=115 |
| G3-3 | case 1-yr retention rate reproduced & in [0,1] | **PASS** | recomputed=0.8456 persisted=0.8456 |
| G3-4 | overall official-RM 1-yr retention reproduced & bound-checked | **PASS** | recomputed=0.8622 persisted=0.8622 |
| G4-1 | overall SIP persistency (paid/expected) reproduced & in [0,1] | **PASS** | recomputed=0.8795 persisted=0.8795 |
| G5-1 | clustering re-runs stable across 3 seeds (min ARI>=0.8) | **PASS** | ARIs=[1.0, 1.0, 1.0] |
| G5-2 | silhouette reproduced at k=4 | **PASS** | recomputed=0.4175 persisted=0.4175 |
| G6-1 | cross-sell Play1 customer count reproduced | **PASS** | recomputed=4251 persisted=4251 |
| G6-2 | cross-sell Play1 Taka == count x ticket | **PASS** | recomputed=51012000 persisted=51012000 |
| G6-3 | cross-sell Play3 (Non-SIP->SIP) count + Taka reproduced | **PASS** | recomputed n=348 taka=29232000 | persisted n=348 |
| G7-1 | saved tables match recomputed values (3 spot-checks) | **PASS** | scorecard-churn=True, rank#1=FixedIncome=True, crosssell-taka=True |
| G7-2 | referenced figures exist on disk | **PASS** | 07_fund_ranking.png; 04_cross_sell.png; 01_rm_quadrant.png |
| G8-1 | Section 1 states the no-NAV / flow-not-return caveat | **PASS** | found explicit caveat in section1.ipynb |

**18/18 checks PASS.**

`GATE 2: PASS`