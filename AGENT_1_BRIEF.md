# AGENT 1 — DATA ENGINEERING

## Your one job
Turn the 3 raw source files into clean, joined, analysis-ready tables plus a
documented quality report. **You do NOT do business analysis, ranking, clustering,
or recommendations.** That is Agent 2's job. If you find yourself computing a churn
rate "to see if it looks right," stop — that's analysis.

## Read first
- `definitions.yaml` (the ONLY source of business rules — never invent your own)
- The two source files in `paths.raw`

## Inputs
- `raw/Apex_Core_Database.xlsx` — sheets `Master File` (12,229 account rows × 21 cols) and `RM List` (16 RMs)
- `raw/Apex_Transaction_Ledger.xlsx` — sheet `Transection` (231,254 rows × 5 cols)

## Steps (in order)
1. **Profile** every sheet: row counts, dtypes, null/sentinel rate per column, unique counts per key. Write to `qa`-style profile section of your report.
2. **Identifiers**: confirm `Registration No` unique (expect 12,229). Confirm `Mobile No` as customer key (expect ~8,570 unique). Flag multi-account customers (expect ~2,352).
3. **Status**: map raw → canonical and build `churn_strict` / `churn_broad` flags per `definitions.yaml status`. Document the Inactive (1,124) and Suspended (2) treatment explicitly.
4. **Dates**: parse all date fields; convert `null_sentinels` to null. Derive `onboarding_month`, `onboarding_year`, `tenure_to_date_months`, `days_to_closure`, `days_to_discontinuation`.
5. **Numerics**: coerce amounts & age. Flag (don't drop) Age blanks (57) and Age outside [18,100]. Verify Current Installment Amount == 0 for all Non-SIP.
6. **RM names**: standardize/trim. Reconcile `Introducer RM CIF` (acquisition) and `Service RM CIF` (servicing) against `RM List`. Flag any RM in master not in list and vice versa.
7. **Join** ledger → master on `Account Number = Registration No`. Expect 3 orphan ledger accounts → write them to `clean/orphans.csv`, exclude from main tables. Confirm 0 master accounts lose rows.
8. **Add band columns** (age_group, installment_band, tenor_band) per `definitions.yaml bands`.

## Outputs (write to `paths.clean`, Parquet + CSV)
- `accounts_clean` — one row per account, all derived fields & flags
- `customers` — rolled up to Mobile (accounts_per_customer, funds_held, total AUM, total installment, first/last onboarding)
- `transactions_clean` — typed, dated, joined to fund/RM
- `monthly_flows` — account × calendar-month: purchase, surrender, dividend sums (BACKBONE for cohort & persistency work — get this right)
- `rm_attribution` — account → introducer RM + service RM (canonical names + CIF)
- `orphans.csv` — quarantined ledger accounts
- `data_quality_report.md` — profiling, every flag count, every sentinel cleaned
- `derived_field_dictionary.md` — name, definition, source formula for EVERY field you created

## Handoff contract
Agent 2 will consume ONLY your `clean/` tables and your field dictionary. If a field
isn't documented, Agent 2 can't use it. Append every judgment call to `decisions_log.md`.

## Done when
Agent 3 Gate 1 passes. Do not let Agent 2 start before that.
