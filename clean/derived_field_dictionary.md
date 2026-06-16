# Derived Field Dictionary — Apex clean tables
**Owner:** Agent 1 · **Date:** 2026-06-16 · **as_of_date (AS_OF):** 2026-05-31

Every field Agent 2 may consume. Fields not listed here are not contract-stable.
Source columns are from the raw Master File / Ledger unless noted. Rules per `definitions.yaml`.

---

## `accounts_clean` (one row per account, key = `registration_no`)

| field | type | definition / formula | source |
|---|---|---|---|
| registration_no | str | trimmed account key | Registration No |
| fund | str | fund name (4 canonical) | Fund |
| investment_type | str | 'SIP' or 'NON SIP' | Investment Type |
| is_sip | bool | `investment_type == 'SIP'` | derived |
| customer_no | Int64 | cross-check customer id | Customer No. |
| mobile_no | str | customer key | Mobile No |
| customer_name | str | trimmed | Customer Name |
| activity_status_raw | str | trimmed raw status | Activity Status |
| status | str | canonical via `status.raw_to_canonical` (active/closed/inactive/discontinued/suspended) | derived |
| churn_strict | bool | `status in {closed, discontinued}` (headline churn) | derived |
| churn_broad | bool | `status in {closed, discontinued, inactive}` (sensitivity) | derived |
| is_active | bool | `status == active` | derived |
| excluded_from_rates | bool | `status == suspended` (drop from rate denominators) | derived |
| age | float | numeric Age; NaN if blank | Age |
| onboarding_amount | float | initial investment amount (BDT) | Amount (While onboarding) |
| current_installment_amount | float | current SIP installment (BDT); 0 for NON SIP | Current Installment Amount |
| tenor_in_month | float | planned tenor (months); 0 for NON SIP | Tenor In Month |
| investment_value_market | float | current market AUM (BDT) | Investment Value (At Market) |
| first_purchase_date | datetime | onboarding date (sentinels→null) | First Purchase Date |
| tenure_maturity_date | datetime | maturity date (sentinels→null) | Tenure Maturity Date |
| account_closing_date | datetime | closing date, null if open | Account Closing Date |
| sip_discontinuation_date | datetime | SIP stop date, null if not discontinued | SIP Discontinuation Date |
| onboarding_month | str (YYYY-MM) | `first_purchase_date` period-M | derived |
| onboarding_year | Int64 | `first_purchase_date.year` | derived |
| tenure_to_date_months | Float64 | calendar months from first_purchase to min(closing_date, AS_OF); open accounts use AS_OF | derived |
| days_to_closure | Int64 | `account_closing_date - first_purchase_date` in days; null if open | derived |
| days_to_discontinuation | Int64 | `sip_discontinuation_date - first_purchase_date` in days; null if not disc. | derived |
| introducer_rm_name | str | raw trimmed introducer (acquisition) | Introducer RM Name |
| introducer_rm_name_canon | str | canonical name from CIF map, else raw | derived |
| introducer_rm_cif | Int64 | introducer CIF; null for non-official introducers | Introducer RM CIF |
| service_rm_name | str | raw trimmed service RM (servicing) | Service RM Name |
| service_rm_name_canon | str | canonical name from CIF map, else raw | derived |
| service_rm_cif | Int64 | service CIF; null for 9 non-list rows | Service RM CIF |
| onboarding_department | str | dept (only 'Retail Sales'); null cleaned | Onboarding Department |
| introducer_in_rmlist | bool | introducer name ∈ 16 official RM List | derived |
| service_in_rmlist | bool | service name ∈ 16 official RM List | derived |
| introducer_cif_missing | bool | `introducer_rm_cif` is null | derived |
| service_cif_missing | bool | `service_rm_cif` is null | derived |
| age_group | str | band per `bands.age_groups` (left-closed); NA if age null | derived |
| installment_band | str | band per `bands.installment_bands_sip`; NA for NON SIP | derived |
| tenor_band | str | band per `bands.tenor_bands_months` | derived |
| flag_age_missing | bool | age is null | derived |
| flag_age_out_of_range | bool | age present and outside [18,100] | derived |
| flag_age_invalid | bool | `flag_age_missing OR flag_age_out_of_range` | derived |
| flag_nonsip_installment_nonzero | bool | NON SIP with installment ≠ 0 (expect 0 rows) | derived |
| flag_sip_tenor_zero | bool | SIP with tenor == 0 | derived |
| flag_closed_no_closing_date | bool | status closed but closing date null | derived |
| flag_disc_no_disc_date | bool | status discontinued but disc. date null | derived |

**Banding rule:** all bands are left-closed `[min, max)` per `definitions.bands`.

---

## `customers` (one row per Mobile, key = `mobile_no`)

| field | type | definition |
|---|---|---|
| mobile_no | str | customer key |
| accounts_per_customer | int | count of accounts for this Mobile |
| customer_name | str | first name seen |
| customer_no_primary | Int64 | first Customer No. seen |
| funds_held | int | distinct funds across accounts |
| total_aum_market | float | Σ `investment_value_market` |
| total_onboarding_amount | float | Σ `onboarding_amount` |
| total_current_installment | float | Σ `current_installment_amount` |
| first_onboarding_date | datetime | min `first_purchase_date` |
| last_onboarding_date | datetime | max `first_purchase_date` |
| first_onboarding_month | str | period-M of first |
| last_onboarding_month | str | period-M of last |
| n_active_accounts | int | count active |
| n_churn_strict_accounts | int | count churned (strict) |
| n_sip_accounts | int | count SIP |
| is_multi_account | bool | `accounts_per_customer > 1` |

---

## `transactions_clean` (one row per ledger transaction; orphans excluded)

| field | type | definition |
|---|---|---|
| account_number | str | = registration_no (joined) |
| customer_name_ledger | str | name as in ledger |
| transaction_type | str | Purchase / Surrender / Dividend |
| amount | float | transaction Total (BDT) |
| transaction_date | datetime | Purchase/Surrender Date |
| transaction_month | str (YYYY-MM) | period-M of transaction_date |
| fund | str | from master |
| investment_type | str | from master |
| status | str | account canonical status (from master) |
| introducer_rm_name_canon | str | from master |
| introducer_rm_cif | Int64 | from master |
| service_rm_name_canon | str | from master |
| service_rm_cif | Int64 | from master |

---

## `monthly_flows` (account × calendar-month — BACKBONE for cohort/persistency)

| field | type | definition |
|---|---|---|
| account_number | str | = registration_no |
| transaction_month | str (YYYY-MM) | calendar month |
| purchase_amount | float | Σ Purchase that month (0 if none) |
| surrender_amount | float | Σ Surrender that month |
| dividend_amount | float | Σ Dividend that month |
| net_flow | float | `purchase_amount - surrender_amount` (dividends excluded, per `transactions.net_flow`) |
| fund | str | from master |
| investment_type | str | from master |
| status | str | account canonical status |
| service_rm_name_canon | str | from master |
| onboarding_month | str | account's onboarding month (for cohorting) |

Grain note: only account×month combinations with at least one transaction are present
(212,796 rows). Months with no activity for an account are absent (sparse); downstream
cohort work should reindex against a full month spine if dense panels are needed.

---

## `rm_attribution` (one row per account)

| field | type | definition |
|---|---|---|
| registration_no | str | account key |
| introducer_rm_name | str | raw introducer (acquisition role) |
| introducer_rm_name_canon | str | canonical introducer |
| introducer_rm_cif | Int64 | introducer CIF |
| introducer_in_rmlist | bool | ∈ 16 official RMs |
| service_rm_name | str | raw service RM (servicing role) |
| service_rm_name_canon | str | canonical service RM |
| service_rm_cif | Int64 | service CIF |
| service_in_rmlist | bool | ∈ 16 official RMs |

**Role separation (per `definitions.rm`):** acquisition metrics use *introducer*;
portfolio/book metrics use *service*. Keep separate — do not blend.

---

## `orphans.csv` (quarantined ledger rows, excluded from main tables)
Columns: `account_number, customer_name_ledger, transaction_type, amount, transaction_date`.
3 accounts / 6 rows: `ABF-002091`, `IIF-SIP-000267-wr`, `ISF-SIP-001766-Wrong`.
