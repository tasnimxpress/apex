# Apex Asset Management — Fund Intelligence Report

Senior Data Analyst Case Study · IDLC Asset Management · June 2026

---

## What This Is

A full-cycle analysis of Apex Asset Management's mutual fund portfolio: 4 funds, 12,229 accounts, 8,570 unique customers, and 16 relationship managers. The study covers fund performance ranking, customer segmentation, cross-sell sizing, and RM acquisition-quality screening — tied to 8 owner-assigned actions with timelines.

All figures are **flow / retention / engagement metrics** — not investment return. No NAV series exists in the source data; AUM = book value (capital deployed minus surrendered).

---

## Repository Structure

```
apex/
├── raw/                               # Source data — read-only
│   ├── Apex_Core_Database.xlsx        # Master account file + RM List (sheets)
│   ├── Apex_Transaction_Ledger.xlsx   # All purchases, surrenders, dividends
│   ├── Case_Study.pdf                 # Original brief
│   └── Data_Dictionary.pdf            # Field definitions
│
└── deliverables/
    ├── apex_analysis.ipynb            # Full analytical notebook (primary deliverable)
    ├── apex_dashboard.html            # Interactive BI dashboard (5-tab, Chart.js)
    ├── apex_presentation.html         # 10-slide presentation deck (speaker notes included)
    ├── apex_deck.pptx                 # PowerPoint export
    └── clean/
        ├── master_clean.csv           # Cleaned master file (feature-engineered)
        └── ledger_clean.csv           # Cleaned transaction ledger
```

---

## Key Numbers

| Metric | Value |
|--------|-------|
| Total AUM (book) | ৳276.0 Cr |
| Cumulative net flow (purchases − surrenders) | ৳249.3 Cr |
| Net flow peak year | ~৳60 Cr (2022–23) |
| Unique customers | 8,570 |
| Total accounts | 12,229 |
| Average strict churn (closed + discontinued) | 33.6% |
| SIP persistency (installments paid / expected) | 75.2% |
| Top 10% customer AUM share | 68.0% (857 customers · ৳205 Cr) |
| Single-fund customers | 81.5% of all customers |
| Team avg 1-year retention (Introducer RM) | 87.8% |
| Cross-sell pipeline (3 plays) | ৳8.02 Cr / year |

---

## Source Data

**`Apex_Core_Database.xlsx`** — two sheets:
- `Master File`: one row per account (12,229 rows). Key fields: Registration No, Mobile No, Fund Name, Investment Type (SIP / NON SIP), Activity Status, Current Installment Amount, Tenor in Month, First Purchase Date, Account Closing Date, SIP Discontinuation Date, Introducer RM Name/CIF, Service RM Name/CIF.
- `RM List`: 16 official relationship managers with CIF codes and names.

**`Apex_Transaction_Ledger.xlsx`** — sheet `Transection` (231,254 rows). Fields: Account Number, Type of Transaction (Purchase / Surrender / Dividend), Purchase/Surrender Date, Total (BDT amount).

**Key definitions locked at project start:**
- Customer identity = Mobile No (~8,570 unique)
- Strict churn = Closed + Discontinued (4,178 accounts, 34.2% of 12,227 excluding 2 suspended)
- Broad churn = adds Inactive (5,302 accounts) — reported as sensitivity only
- Net flow = sum(Purchase) − sum(Surrender); dividends excluded
- Snapshot date: 2026-05-31

---

## Findings Summary

### Finding 1 — Balanced Opportunity Fund: worst fund, net decumulation
Composite score **28.8 / 100** (vs Fixed Income 74.6). Book multiple **0.78×** — the only fund where current AUM is below capital originally deployed. Customers have withdrawn more than they invested net. Requires a 30-day diagnostic sprint and a redesign or consolidation decision.

### Finding 2 — Capital Growth: biggest fund, highest churn
**47.2% strict churn** on 3,779 accounts. 36-month cohort survival only 53.8% vs Fixed Income's 77.5%. Book multiple is 2.97× (capital grows while it's held), meaning the problem is retention, not performance. Win-back campaigns and RM redeployment are the fastest fixes.

### Finding 3 — 68% of AUM concentrated in the top 10% of customers
857 customers hold ৳205 Cr. No differentiated service tier exists. A cluster of high-value churners would constitute an outsized balance-sheet event; losing one top-decile customer is worth ~nine median customers in AUM terms.

### Finding 4 — Two Introducer RMs with below-average and declining acquisition quality
Team average 1-year retention across all matured cohorts is **87.8%**. Two Introducer RMs sit in the low-retention tail: **Mohammad Jasim Ahmed** (83.4%, consistently below average across every cohort, 70 yr-1 churned from 422 accounts) and **Shibani Datta** (86.3%, deteriorating trend: 92.0%→90.5%→85.0%→79.6% across 2021–2024 cohorts, most churned accounts at 74). **Most. Sumaya Siddique** (74.5%) is an emerging watch on a thin single-cohort record. Acquisition quality — not product — is the root cause of that leakage. Best performer MST. Sonia Sheikh achieves **91.8%** 1-year retention on 296 accounts.

### Finding 5 — ৳8.02 Cr in cross-sell sits in existing relationships
Three plays: (1) single → second-fund for 4,251 active single-fund customers — ৳5.1 Cr / year; (2) Non-SIP → SIP migration for 348 lump-sum customers — ৳2.9 Cr / year recurring; (3) high-value singles as a priority sub-target — ৳1.6 Cr. Zero acquisition cost — all via existing RM relationships.

---

## Customer Segments (K-Means, k=4)

| Segment | Customers | Description |
|---------|-----------|-------------|
| Young Core SIP | 5,350 | Median age 33 · small balances · where most new sign-ups land · largest cross-sell pool |
| Older Mass-Market | 2,296 | Older, mid-tier balances · mix of SIP and lump-sum |
| High-Value Multi-fund | 848 | Larger portfolios · 2+ funds · low churn risk · priority servicing tier |
| Ultra-Wealthy Whales | 41 | Median ৳96 L each · 66% multi-fund · no dedicated service currently exists |

The 41 Ultra-Wealthy Whales are tiny in number but critical — losing one is worth hundreds of ordinary accounts in AUM terms.

---

## Prioritised Actions

| # | Action | Owner | Timeline |
|---|--------|-------|----------|
| 1 | Diagnose Balanced Opportunity — exit interviews + redesign or merge decision | Head of Funds / PM | 30 days |
| 2 | Win back closed / stopped Capital Growth accounts (last 24 months) | Head of Funds / PM | 2 weeks |
| 3 | Auto-flag first missed SIP installment → same-day save-the-SIP call | Head of Retention / Ops | 2 weeks |
| 4 | Launch second-fund campaign to 4,251 single-fund active customers | Head of Sales | 30 days |
| 5 | Reinvest-your-dividend offer sent with every Jan / Jul distribution | Marketing + PM | 1 month |
| 6 | Compliance & suitability review of Mohammad Jasim Ahmed and Shibani Datta; add Most. Sumaya Siddique to early-coaching monitoring; 90-day post-onboarding quality check on all new accounts | Head of Compliance / Distribution Quality | 2 weeks |
| 7 | Deploy high-retention RMs (Sonia Sheikh model) onto Capital Growth new accounts | Head of Sales | 30 days |
| 8 | Offer 348 lump-sum customers a switch to recurring monthly plans | Head of Sales | 30 days |

---

## Deliverables

**`apex_analysis.ipynb`** — Primary deliverable. Self-contained notebook (13 sections, ~100 cells) covering data loading, cleaning, feature engineering, all three analytical sections (Fund Performance, Customer Intelligence, RM Productivity), and a cross-business synthesis with action register. Open in Jupyter or VS Code. Cleaned outputs saved to `deliverables/clean/`.

**`apex_dashboard.html`** — Open in any browser. Five tabs: Overview, Funds, Customers, RM Performance, Findings & Actions. All charts are interactive (Chart.js 4). Legend indicators are type-aware: line datasets show a line, bar datasets show a box. No server required — single file, fully self-contained.

**`apex_presentation.html`** — Open in any browser. 10-slide deck with full speaker notes. Navigate with arrow keys or the bottom nav bar. Print-to-PDF supported (`@media print` outputs one slide per page at A4 / Letter).

---

## Methodology Notes

- **SIP persistency ≠ retention.** Persistency measures whether installments are paid. A customer can maintain high persistency and still close their account (Capital Growth: 70.0% persistency, 47.2% churn). Do not substitute one metric for the other.
- **Book multiple = AUM ÷ onboarding capital.** Measures capital retention over time, not investment performance. No NAV data was available.
- **Churn = strict** (closed + discontinued) unless marked otherwise. Inactive accounts are excluded from the headline rate but reported as sensitivity. Suspended (2 accounts) excluded from all denominators.
- **1-year retention (Introducer RM)** is computed on matured cohorts only (anniversary ≤ 2026-05-31). An account is "alive at year 1" if it was not closed or discontinued before its first anniversary.
- **2026 data is partial** (Jan–May only, through the 2026-05-31 snapshot). All 2026 totals understate the full year; 2025 is the latest complete year.
- **Cohort survival gaps are intentional.** 24-month survival is only shown through the 2024 cohort; 36-month survival through 2023. Newer cohorts have not yet reached those time marks as of the snapshot date.
- **Customer key = Mobile No** per the case brief. Shared or changed numbers may cause ~1–3% count inaccuracy.
- **Net flow peaked at ~৳60 Cr in 2022–23** (purchases near ৳100 Cr, surrenders still low). Rising surrenders (~৳65 Cr by 2024–25) have compressed net flow to ৳28–38 Cr — the book leaks more as it matures.
