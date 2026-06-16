# Data Quality Report — Apex Asset Management Case Study
**Owner:** Agent 1 (Data Engineering) · **Date:** 2026-06-16 · **as_of_date:** 2026-05-31
**Source of rules:** `definitions.yaml` (single source of truth) · **Seed:** 42

This report documents profiling, every cleaning action, every quality flag, and
the conservation of rows through each transform. Numbers below are produced by
`clean/build_clean.py` (reproducible) and dumped to `clean/_report_numbers.json`.

---

## 1. Source profiling

### `Apex_Core_Database.xlsx` → sheet `Master File` — 12,229 rows × 21 cols
| Column | dtype | nulls | sentinel~ | nunique | note |
|---|---|---|---|---|---|
| Registration No | object | 0 | 0 | 12,229 | account key — unique ✓ |
| Fund | object | 0 | 0 | 4 | matches `definitions.funds` |
| Investment Type | object | 0 | 0 | 2 | SIP 10,428 / NON SIP 1,801 |
| Customer No. | int64 | 0 | 0 | 8,569 | cross-check key |
| Activity Status | object | 0 | 0 | 5 | see status section |
| Mobile No | int64 | 0 | 0 | 8,570 | customer key ✓ |
| Customer Name | object | 0 | 0 | 8,567 | |
| Age | float64 | 57 | 57 | 72 | 57 blank; 2 below 18 (min 9) |
| Amount (While onboarding) | int64 | 0 | 0 | 37 | |
| Current Installment Amount | int64 | 0 | 0 | 60 | ==0 for all NON SIP ✓ |
| Tenor In Month | int64 | 0 | 0 | 29 | 0 for 1,801 NON SIP + 1 SIP |
| First Purchase Date | object | 0 | 0 | 1,628 | onboarding date |
| Tenure Maturity Date | object | 0 | 1,801 | 610 | sentinel `00:00:00` |
| Service RM Name | object | 0 | 0 | 22 | servicing role |
| Service RM CIF | float64 | 9 | 9 | 16 | 16 official CIFs |
| Onboarding Department | object | 1,983 | 1,983 | 1 | only 'Retail Sales' |
| Introducer RM Name | object | 0 | 0 | 188 | acquisition role |
| Introducer RM CIF | float64 | 1,983 | 1,983 | 42 | null exactly where dept null |
| Investment Value (At Market) | float64 | 0 | 0 | 6,556 | market AUM |
| Account Closing Date | object | 2 | 8,732 | 977 | sentinel ` ` (blank) |
| SIP Discontinuation Date | object | 1 | 11,552 | 220 | sentinel ` ` (blank) |

### `Apex_Core_Database.xlsx` → sheet `RM List` — 16 rows
Two columns; `Unnamed: 0` is fully empty (dropped). 16 official Introducer RM names.
The RM List carries **names only, no CIF** — CIFs reconstructed from master (see §6).

### `Apex_Transaction_Ledger.xlsx` → sheet `Transection` — 231,254 rows × 5 cols
| Column | dtype | nulls | nunique | note |
|---|---|---|---|---|
| Account Number | object | 0 | 12,232 | joins to Registration No; 3 orphans |
| Customer Name | object | 0 | 8,570 | |
| Type of Transaction | object | 0 | 3 | Purchase 209,675 / Dividend 13,524 / Surrender 8,055 |
| Total | float64 | 0 | 41,485 | amount |
| Purchase/Surrender Date | object | 0 | 1,903 | range 2017-02-06 → 2026-05-04 |

---

## 2. Identifier checks
- **Registration No**: 12,229 rows, 12,229 unique, 0 duplicates. **PASS (==12,229).**
- **Mobile No** (customer key): 8,570 unique. **PASS (~8,570).**
- **Customer No.**: 8,569 unique (kept as cross-check only, per definitions).
- **Multi-account customers** (Mobile with >1 account): **2,352. PASS (~2,352).**
- Mobile↔Customer No. is *not* perfectly 1:1 (2 Mobiles map to >1 Customer No.; 3 Customer No. map to >1 Mobile). Mobile is the chosen customer key per `definitions.keys`; logged as a judgment note (see decisions log).

---

## 3. Status / churn
Raw `Activity Status` → canonical via `definitions.status.raw_to_canonical`:

| canonical | count |
|---|---|
| active | 6,925 |
| closed | 3,500 |
| inactive | 1,124 |
| discontinued | 678 |
| suspended | 2 |
| **sum** | **12,229** |

**PASS** — canonical counts sum to 12,229.

- `churn_strict` (closed + discontinued) = **4,178**.
- `churn_broad` (closed + discontinued + inactive) = **5,302**.
- **Inactive (1,124)**: NOT in headline churn. Treated as a separate at-risk tier surfaced only via `churn_broad` (broad sensitivity). Locked in decisions log.
- **Suspended (2)**: flagged `excluded_from_rates = True`; to be dropped from rate denominators by Agent 2. Rows retained in `accounts_clean`.

---

## 4. Date cleaning & sentinels
All sentinels in `definitions.null_sentinels` (`" "`, `""`, `"00:00:00"`, `"1900-01-01"`)
converted to null before parsing. Cleaned counts:
- Tenure Maturity Date: 1,801 `00:00:00` → null.
- Account Closing Date: 8,732 blanks → null (2 native nulls + 8,730 ` `).
- SIP Discontinuation Date: 11,552 blanks → null.

**Residual sentinel audit (post-clean): 0** in every date and amount column
(`first_purchase_date`, `tenure_maturity_date`, `account_closing_date`,
`sip_discontinuation_date`, `age`, `onboarding_amount`, `current_installment_amount`).

**Date-ordering validation (all targets):**
| check | violations |
|---|---|
| First Purchase ≤ Account Closing (where closed) | 0 |
| First Purchase ≤ SIP Discontinuation (where disc.) | 0 |
| First Purchase ≤ as_of (2026-05-31) | 0 |
| Account Closing ≤ as_of | 0 |
| SIP Discontinuation ≤ as_of | 0 |
| Tenure Maturity ≥ First Purchase (non-null) | 0 |

**PASS** on all.

---

## 5. Numeric coercion & flags (flag, never drop)
| flag | count | meaning |
|---|---|---|
| flag_age_missing | 57 | Age blank |
| flag_age_out_of_range | 2 | Age outside [18,100] (both = 9, below 18) |
| flag_age_invalid | 59 | union of the two above |
| flag_nonsip_installment_nonzero | 0 | NON SIP with installment ≠ 0 |
| flag_sip_tenor_zero | 1 | SIP with tenor 0 (AGF-SIP-002441, status=closed) |
| flag_closed_no_closing_date | 3 | Closed account missing closing date |
| flag_disc_no_disc_date | 1 | Discontinued account missing discontinuation date |

**Current Installment Amount == 0 for ALL 1,801 NON SIP rows. PASS.**
(And all 10,428 SIP rows have non-zero installment.)

---

## 6. RM reconciliation
- **RM List = 16 official Introducer RM names.** All 16 resolve to a unique CIF via master.
- **CIF↔name identity** built from union of Service + Introducer pairs: **42 distinct CIFs, all 1:1** (0 CIFs map to >1 name). Used to produce canonical RM names.
- **Service RM names in master not in RM List: 6** — `A.H.M. MAMUNUR MOLLA`, `ABDUL BAYEZID TALUKDER`, `ABUL RUHUL HOSSAIN`, `KAZI KHOKON MOLLA`, `MOHAMMAD SADEKUR RANA`, `TARASH CHAKRABORTY` (9 accounts total; these carry null Service RM CIF). Flagged `service_in_rmlist=False`, `service_cif_missing` where applicable.
- **Introducer RM names in master not in RM List: 172 distinct.** Introducer is a broad acquisition field (188 distinct names) including external/legacy introducers; not all are Apex RMs. Flagged `introducer_in_rmlist`.
- **Introducer RM CIF missing: 1,983 rows** — *exactly* the rows where `Onboarding Department` is also null. These are non-official-RM introducers. Flagged `introducer_cif_missing`.
- **Service RM CIF missing: 9 rows** (the 6 non-list service RMs).
- All 16 RM List names appear in master as both Service and Introducer (no RM-in-list-absent-from-master).

---

## 7. Ledger → master join & orphan quarantine
- Join key: ledger `Account Number` = master `Registration No`.
- **Orphan ledger accounts (in ledger, not in master): 3** —
  `ABF-002091`, `IIF-SIP-000267-wr`, `ISF-SIP-001766-Wrong`
  (the latter two carry `-wr`/`-Wrong` suffixes → data-entry errors). **PASS (~3).**
- These 3 accounts span **6 ledger rows**, all quarantined to `clean/orphans.csv` and excluded from `transactions_clean` / `monthly_flows`.
- **Master accounts that lose rows: 0.** Every master account joins; post-orphan-removal every transaction matched to a fund/RM (0 unmatched). **PASS.**

---

## 8. Transaction → monthly_flows reconciliation
`monthly_flows` (account × calendar-month) totals reconcile **exactly** to
`transactions_clean` by type:
| type | transactions_clean | monthly_flows | target | match |
|---|---|---|---|---|
| Purchase | 5,219,456,433.47 | 5,219,456,433.47 | ~5.22bn | ✓ |
| Surrender | 2,726,818,228.83 | 2,726,818,228.83 | ~2.73bn | ✓ |
| Dividend | 249,886,432.00 | 249,886,432.00 | ~0.25bn | ✓ |

---

## 9. Row-conservation log (auditable)
See `clean/_conservation_log.txt`. Summary:
```
load master:        12,229  → 12,229
load ledger:       231,254  → 231,254
accounts_clean:     12,229  → 12,229  (one row per account)
orphan quarantine: 231,254  →      6  (3 accounts removed)
tx after orphans:  231,254  → 231,248
tx join master:    231,248  → 231,248  (all matched)
monthly_flows:     231,248  → 212,796  (account×month grain)
customers:          12,229  →   8,570  (rolled to Mobile)
```

---

## 10. Outputs written to `clean/`
`accounts_clean`, `customers`, `transactions_clean`, `monthly_flows`,
`rm_attribution` (each Parquet + CSV), `orphans.csv`,
`data_quality_report.md`, `derived_field_dictionary.md`,
plus `_report_numbers.json` and `_conservation_log.txt` (evidence artifacts).
