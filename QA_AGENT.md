# QA Agent — Apex Asset Management Case Study

Validation record for the two-gate QA process that preceded the final deliverables.
All checks were run independently from `raw/` — no Agent 1 or Agent 2 outputs were
trusted without re-derivation.

---

## QA Architecture

```
Agent 1 (Data Engineering)
  └── Gate 1: 22 structural / logic / churn checks against raw/
      └── PASS → Agent 2 (Analysis)
            └── Gate 2: 18 metric reproduction + notebook execution checks
                └── PASS → Lead assembles deliverables
```

**Principle:** Reproduce, don't trust. Every number below was recomputed directly
from `raw/` (Gate 1) or `clean/` (Gate 2) using independent scripts. Agent outputs
were used only as expected targets, never as inputs to re-checks.

---

## Gate 1 — Data Engineering

**Date:** 2026-06-16  
**Script:** `qa/gate1_checks.py`  
**Result:** **22 / 22 PASS**

### Raw Baselines (re-derived from source)

| Item | Value |
|------|-------|
| Master File rows | 12,229 |
| RM List rows | 16 |
| Ledger rows (`Transection` sheet) | 231,254 |
| Investment Type: SIP | 10,428 |
| Investment Type: NON SIP | 1,801 |
| Status — Active | 6,925 |
| Status — Closed | 3,500 |
| Status — Inactive | 1,124 |
| Status — Discontinue | 678 |
| Status — Suspended | 2 |

### Structural / Integrity Checks

| ID | Check | Result |
|----|-------|--------|
| S1 | `Registration No` unique == 12,229 in raw | PASS |
| S1b | `accounts_clean.registration_no` unique == 12,229 | PASS |
| S2 | Mobile unique == 8,570 in raw | PASS |
| S2b | Multi-account customers (>1 account) == 2,352 in raw | PASS |
| S2c | `customers.parquet` rows == 8,570; multi-account flag == 2,352 | PASS |
| S3 | Exactly 3 orphan ledger accounts (set-diff raw→master) | PASS |
| S3b | 0 master accounts dropped from `accounts_clean` | PASS |
| S3c | `orphans.csv` matches raw orphan set exactly (6 rows) | PASS |
| S4a | `accounts_clean` rows == master rows (12,229) | PASS |
| S4b | `transactions_clean` + orphan rows == ledger rows (231,254) | PASS |
| S5 | Status canonical counts match raw and sum to 12,229 | PASS |
| S6 | No null sentinels / `1900-01-01` in date or amount columns | PASS |

**Orphan accounts (quarantined, not dropped from master):**
`ABF-002091`, `IIF-SIP-000267-wr`, `ISF-SIP-001766-Wrong` — 6 ledger rows quarantined to `orphans.csv`.

### Logic Checks

| ID | Check | Result |
|----|-------|--------|
| L1 | First Purchase Date ≤ closing/discontinuation date ≤ as_of (2026-05-31) | PASS |
| L2 | Tenure Maturity Date ≥ First Purchase Date | PASS |
| L3 | Current Installment Amount == 0 for all Non-SIP (1,801 rows) | PASS |
| L4 | Age out-of-range flagged, not dropped (rows conserved at 12,229) | PASS |
| L5 | `monthly_flows` totals reconcile to `transactions_clean` by type | PASS |
| L5b | `transactions_clean` totals == raw ledger minus orphan rows (exact) | PASS |

**Flow reconciliation (exact, to the cent):**

| Type | Total (BDT) |
|------|-------------|
| Purchase | 5,219,456,433.47 |
| Surrender | 2,726,818,228.83 |
| Dividend | 249,886,432.00 |

### Churn / Activity Status Checks

| ID | Check | Result |
|----|-------|--------|
| C1 | `churn_strict` == {closed, discontinued}; count == 4,178 | PASS |
| C2 | `churn_broad` == {closed, discontinued, inactive}; count == 5,302 | PASS |
| C3 | `excluded_from_rates` == suspended exactly (2 rows) | PASS |
| C4 | Suspended excluded from both churn flag columns | PASS |

**Churn breakdown:** 3,500 closed + 678 discontinued = 4,178 strict; + 1,124 inactive = 5,302 broad.

### Anomalies Documented (not blocking)

- 1 SIP account with tenor == 0 (`AGF-SIP-002441`, status: closed) — flagged, not dropped.
- 3 Closed accounts with no closing date — flagged.
- 1 Discontinued account with no discontinuation date — flagged.
- 57 accounts with missing age + 2 with out-of-range age — flagged, not dropped.
- `monthly_flows` is sparse (rows exist only where transactions occur). Analysis notebooks must reindex to a dense month spine for cohort / persistency work.

**Gate 1: PASS**

---

## Gate 2 — Analysis

**Date:** 2026-06-16  
**Script:** `qa/gate2_checks.py`  
**Fresh-kernel execution:** all four notebooks (`section1`, `section2`, `section3`, `synthesis`) re-run top-to-bottom via `nbconvert --execute` — **0 error outputs across 61 cells**.  
**Result:** **18 / 18 PASS**

### Net Flow Checks

| ID | Check | Result |
|----|-------|--------|
| G2-1a | `net_flow` column == purchase − surrender per account (dividends excluded) | PASS |
| G2-1b | Total net flow ties transaction totals (Purchase − Surrender) | PASS |
| G2-1c | Per-fund net flow reproduced | PASS |

**Per-fund net flow (reproduced):**

| Fund | Net Flow |
|------|----------|
| Fixed Income | ৳81.7 Cr |
| Shariah Growth | ৳74.3 Cr |
| Balanced Opportunity | ৳25.1 Cr |
| Capital Growth | ৳68.1 Cr |

### Churn Rate Checks

| ID | Check | Result |
|----|-------|--------|
| G2-2a | Per-fund strict churn rate reproduced | PASS |
| G2-2b | Rate sanity: active + inactive + churn == 100% per fund; all rates in [0, 1] | PASS |

**Per-fund strict churn (reproduced):**

| Fund | Churn Rate |
|------|------------|
| Fixed Income | 16.0% |
| Shariah Growth | 37.5% |
| Balanced Opportunity | 33.7% |
| Capital Growth | 47.2% |

### Retention / Cohort Checks

| ID | Check | Result |
|----|-------|--------|
| G3-1 | Case cohort denominator (accounts first purchased 2024-05) == 136 | PASS |
| G3-2 | Case cohort numerator (still active 2025-05, point-in-time) == 115 | PASS |
| G3-3 | Case 1-yr retention rate == 84.56% (115 / 136); in [0, 1] | PASS |
| G3-4 | Overall official-RM 1-yr retention == 86.22%; in [0, 1] | PASS |

### SIP Persistency Check

| ID | Check | Result |
|----|-------|--------|
| G4-1 | Overall SIP persistency (installments paid / expected) == 87.95%; in [0, 1] | PASS |

### Clustering Stability Checks

| ID | Check | Result |
|----|-------|--------|
| G5-1 | K-means re-runs stable across 3 seeds (min ARI ≥ 0.80) | PASS |
| G5-2 | Silhouette at k=4 reproduced == 0.4175 | PASS |

**ARI values across 3 seeds:** [1.0, 1.0, 1.0] — perfectly stable assignment.

### Cross-sell Checks

| ID | Check | Result |
|----|-------|--------|
| G6-1 | Play 1 (single → multi-fund) customer count reproduced == 4,251 | PASS |
| G6-2 | Play 1 BDT == count × median ticket reproduced == ৳51,012,000 | PASS |
| G6-3 | Play 3 (Non-SIP → SIP) count == 348; BDT == ৳29,232,000 | PASS |

### Output Integrity Checks

| ID | Check | Result |
|----|-------|--------|
| G7-1 | Saved tables match recomputed values (3 spot-checks) | PASS |
| G7-2 | Referenced figures exist on disk | PASS |
| G8-1 | Section 1 states the no-NAV / flow-not-return caveat | PASS |

**Spot-check targets:** `fund_scorecard.csv` churn column ✓, rank #1 == Fixed Income ✓, cross-sell BDT ✓.  
**Figure existence confirmed:** `07_fund_ranking.png`, `04_cross_sell.png`, `01_rm_quadrant.png`.

**Gate 2: PASS**

---

## Key Definitions (locked in `definitions.yaml`)

These were set before any agent ran and never changed mid-analysis.

| Definition | Value |
|------------|-------|
| Customer identity | Mobile No |
| Snapshot / as-of date | 2026-05-31 |
| Strict churn | Closed + Discontinued |
| Broad churn (sensitivity) | Closed + Discontinued + Inactive |
| Excluded from denominators | Suspended (2 accounts) |
| Net flow | sum(Purchase) − sum(Surrender); dividends excluded |
| RM acquisition metric | Introducer RM CIF |
| RM servicing metric | Service RM CIF |
| Clustering level | Customer (Mobile No), not account |
| Clustering features | age, current_installment_amount, tenor_in_month, onboarding_amount |
| k selected | 4 (elbow + silhouette; ARI=1.0 across 3 seeds) |
| 1-yr retention cohort | Accounts first purchased 2024-05, measured active at 2025-05 |
| Random seed | 42 |

---

## What the QA Process Does Not Cover

- **Investment return / NAV performance** — no NAV data exists; all metrics are capital-flow based.
- **RM transfer history** — RM attribution is based on `Introducer RM CIF` at account open. Accounts transferred after opening retain original RM attribution.
- **2025 annualisation** — data runs to 2025-05 only (~5 months). 2025 totals are partial; projections are directional.
- **Shared mobile numbers** — mobile used as customer key per the brief; shared or reassigned numbers may cause ~1–3% customer count inaccuracy.
- **Inactive classification** — 1,124 accounts are Inactive (soft-churn). They are excluded from the strict churn headline and included only in the broad sensitivity. Business may reclassify; change `definitions.yaml` and re-run from Agent 1 if so.
