# QA Report — GATE 1 (Data Engineering / `clean/`)

**Gate:** 1 of 2 (after Agent 1, before Agent 2)
**Date:** 2026-06-16
**Validator:** Agent 3 (Validation & QA)
**Principle:** Reproduce, don't trust. Every number below was recomputed independently
from `raw/` and cross-checked against `clean/` by `qa/gate1_checks.py`. Agent 1's
reported numbers were used only as expected targets, never as inputs.

**Reproduce with:** `d:/GitHub/apex/.venv/Scripts/python.exe qa/gate1_checks.py`

Raw baselines recomputed from source: master = 12,229 rows; RM List = 16; ledger
('Transection') = 231,254 rows. Investment Type split SIP 10,428 / NON SIP 1,801.
Activity Status raw: Active 6,925 / Closed 3,500 / Inactive 1,124 / Discontinue 678 / Suspended 2.

---

## Structural / Integrity

| ID | Check | Result | Evidence (recomputed) |
|----|-------|--------|-----------------------|
| S1 | `Registration No` unique == 12,229 (raw) | **PASS** | raw rows = 12,229, unique = 12,229 |
| S1b | `accounts_clean.registration_no` unique == 12,229 | **PASS** | clean rows = 12,229, unique = 12,229 |
| S2 | Mobile unique ~8,570 (raw) | **PASS** | raw Mobile unique = 8,570 |
| S2b | Multi-account customers ~2,352 (raw) | **PASS** | mobiles with >1 account = 2,352 |
| S2c | `customers.parquet` rows==8,570 & multi==2,352 | **PASS** | rows = 8,570; accounts_per_customer>1 = 2,352; is_multi_account flag = 2,352 |
| S3 | Exactly 3 orphan ledger accounts (raw set-diff) | **PASS** | `ABF-002091`, `IIF-SIP-000267-wr`, `ISF-SIP-001766-Wrong` (n=3); 6 orphan rows |
| S3b | 0 master accounts dropped | **PASS** | master accounts missing from accounts_clean = 0 |
| S3c | `orphans.csv` accounts == raw orphan set | **PASS** | exact match, 6 rows quarantined |
| S4a | accounts_clean rows == master rows | **PASS** | 12,229 == 12,229 |
| S4b | transactions_clean + orphan rows == ledger rows | **PASS** | 231,248 + 6 = 231,254 == 231,254 |
| S5 | Status canonical counts match & sum to 12,229 | **PASS** | active 6,925 / closed 3,500 / inactive 1,124 / discontinued 678 / suspended 2; sum = 12,229 (raw and clean identical) |
| S6 | No null_sentinels / `1900-01-01` in date/amount cols | **PASS** | residual sentinel count = 0 across all 4 date + 5 amount cols; tx_date 1900 count = 0 |

## Logic

| ID | Check | Result | Evidence (recomputed) |
|----|-------|--------|-----------------------|
| L1 | FPD <= closing (closed); <= disc (discontinued); all <= as_of (2026-05-31) | **PASS** | fpd>close=0, fpd>disc=0, fpd>asof=0, close>asof=0, disc>asof=0 |
| L2 | Tenure Maturity Date >= First Purchase Date | **PASS** | tmd<fpd violations = 0 |
| L3 | Current Installment Amount == 0 for all Non-SIP | **PASS** | clean Non-SIP rows = 1,801; nonzero installment = 0; raw cross-check nonzero = 0 |
| L4 | Age out-of-range flagged, not dropped (rows conserved) | **PASS** | rows 12,229==12,229; recomputed out_of_range=2 == flag; recomputed missing=57 == flag |
| L5 | `monthly_flows` totals reconcile to `transactions_clean` by type | **PASS** | Purchase 5,219,456,433.47 / Surrender 2,726,818,228.83 / Dividend 249,886,432.00 (tx == mf, exact) |
| L5b | transactions_clean totals == raw ledger (orphans removed) | **PASS** | raw-minus-orphan totals tie out exactly to transactions_clean |

## Churn / Activity Status flags

| ID | Check | Result | Evidence (recomputed) |
|----|-------|--------|-----------------------|
| C1 | `churn_strict` == {closed, discontinued}; count == 4,178 | **PASS** | column matches status definition row-for-row; count = 4,178 (3,500 + 678) |
| C2 | `churn_broad` == {closed, discontinued, inactive}; count == 5,302 | **PASS** | column matches definition row-for-row; count = 5,302 (4,178 + 1,124) |
| C3 | `excluded_from_rates` == suspended exactly (2 rows) | **PASS** | excluded_from_rates = 2; suspended = 2; row-for-row match |
| C4 | Suspended excluded from both churn flags | **PASS** | suspended in churn_strict = 0; in churn_broad = 0 |

---

## Summary

- **22 / 22 checks PASS.** No FAILs, no required corrections for Agent 1.
- Every headline integrity number was independently reproduced from `raw/`:
  12,229 accounts, 8,570 customers, 2,352 multi-account, 3 orphans (6 rows, 0 master
  dropped), status sum 12,229, churn_strict 4,178, churn_broad 5,302.
- Flow reconciliation is exact (to the cent) across raw -> transactions_clean -> monthly_flows.
- The churn definition that the whole study depends on (strict = closed+discontinued,
  broad adds inactive, suspended excluded from denominators) is encoded in the
  `accounts_clean` flag columns exactly as locked in `definitions.yaml` / `decisions_log.md`.

### Notes carried forward to GATE 2 (not blocking)
- `monthly_flows` is sparse (212,796 account×month rows, only where a transaction exists).
  Cohort/persistency work in Section 3 needs a dense month spine — confirm Agent 2 reindexes.
- Documented anomalies persist as flags (correct behavior): 1 SIP account tenor 0
  (`AGF-SIP-002441`, closed), 3 Closed accounts with no closing date, 1 Discontinued
  with no disc date, 57 age-missing + 2 age-out-of-range. Section 1/2 should treat these
  via the flag columns, not drop them.

---

`GATE 1: PASS`

---

## GATE 2 — Analysis (`analysis/`)

**Date:** 2026-06-16 · **Validator:** Agent 3 · **Principle:** reproduce, don't trust.
Every metric below was recomputed directly from `clean/` by `qa/gate2_checks.py` and compared
to the notebook-persisted `analysis/<section>/_metrics.json` (tol 0.5%).

**Reproduce with:** `d:/GitHub/apex/.venv/Scripts/python.exe qa/gate2_checks.py`

**Fresh-kernel re-execution:** all four notebooks (`section1`, `section2`, `section3`, `synthesis`)
re-run top-to-bottom via `nbconvert --execute` against a fresh `apex` kernel — **0 error outputs**
across all 61 cells. No hidden state.

| ID | Check | Result | Evidence (recomputed) |
|----|-------|--------|-----------------------|
| G2-1a | net_flow column == purchase-surrender (dividends excluded) | **PASS** | max abs diff=0.000000 |
| G2-1b | total net flow ties tx (Purchase-Surrender) | **PASS** | mf=2492638204.64 tx=2492638204.64 |
| G2-1c | per-fund net flow value reproduced | **PASS** | Fixed:81.7Cr; Shariah:74.3Cr; Balanced:25.1Cr; Capital:68.1Cr |
| G2-2a | per-fund closure/discontinuation/strict-churn reproduced | **PASS** | Fixed churn=0.160; Shariah=0.375; Balanced=0.337; Capital=0.472 |
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
| G6-3 | cross-sell Play3 (Non-SIP->SIP) count + Taka reproduced | **PASS** | recomputed n=348 taka=29232000; persisted n=348 |
| G7-1 | saved tables match recomputed values (3 spot-checks) | **PASS** | scorecard-churn ✓, rank#1=FixedIncome ✓, crosssell-taka ✓ |
| G7-2 | referenced figures exist on disk | **PASS** | 07_fund_ranking.png; 04_cross_sell.png; 01_rm_quadrant.png |
| G8-1 | Section 1 states the no-NAV / flow-not-return caveat | **PASS** | explicit caveat present in section1.ipynb |

### Summary
- **18 / 18 checks PASS.** Every Agent 2 headline metric independently reproduced from `clean/`
  within tolerance; all rates bound-checked in [0,1]; clustering stable across 3 seeds (ARI=1.0);
  cross-sell Taka ties back to reproducible customer counts; the no-NAV caveat is present.
- All four notebooks execute clean top-to-bottom in a fresh kernel (no hidden state).

`GATE 2: PASS`
