# Apex Asset Management — Fund Intelligence Report

Senior Data Analyst Case Study · IDLC Asset Management · June 2026

---

## What This Is

A full-cycle analysis of Apex Asset Management's mutual fund portfolio: 4 funds, 12,229 accounts, 8,570 unique customers, and 16 relationship managers. The study covers fund performance ranking, customer segmentation, cross-sell sizing, and RM productivity — all tied to 8 owner-assigned actions.

All figures are **flow / retention / engagement metrics** — not investment return. No NAV series exists in the source data; AUM = book value (capital deployed minus surrendered).

---

## Repository Structure

```
apex/
├── raw/                          # Source data — read-only
│   ├── Apex_Core_Database.xlsx   # Master account file + RM List (sheets)
│   ├── Apex_Transaction_Ledger.xlsx  # All purchases, surrenders, dividends
│   ├── Case_Study.pdf            # Original brief
│   └── Data_Dictionary.pdf       # Field definitions
│
└── deliverables/
    ├── apex_analysis_final.ipynb # Full analytical notebook (primary deliverable)
    ├── apex_dashboard.html       # Interactive BI dashboard (5-tab, Chart.js)
    └── apex_presentation.html    # 10-slide presentation deck (speaker notes included)
```

---

## Key Numbers

| Metric | Value |
|--------|-------|
| Total AUM (book) | ৳301.6 Cr |
| Net flow (purchases − surrenders) | ৳249.3 Cr |
| Unique customers | 8,570 |
| Total accounts | 12,229 |
| Avg strict churn (closed + discontinued) | 33.6% |
| SIP persistency (installments paid / expected) | 87.9% |
| Top 10% customer AUM share | 68.0% |
| Cross-sell pipeline (3 plays) | ৳8.02 Cr |

---

## Source Data

**`Apex_Core_Database.xlsx`** — two sheets:
- `Master File`: one row per account (12,229 rows). Key fields: Registration No, Mobile No, Fund Name, Investment Type (SIP / NON SIP), Activity Status, Current Installment Amount, Tenor in Month, First Purchase Date, Closing/Discontinuation Date, Introducer RM CIF, Service RM CIF.
- `RM List`: 16 relationship managers with CIF codes and names.

**`Apex_Transaction_Ledger.xlsx`** — sheet `Transection` (231,254 rows). Fields: Account Number, Type of Transaction (Purchase / Surrender / Dividend), Purchase/Surrender Date, Total (BDT amount).

**Key definitions locked at project start:**
- Customer identity = Mobile No (~8,570 unique)
- Strict churn = Closed + Discontinued (4,178 accounts, 34.2% of 12,227 excluding 2 suspended)
- Broad churn = adds Inactive (5,302 accounts) — reported as sensitivity only
- Net flow = sum(Purchase) − sum(Surrender); dividends excluded
- Snapshot date: 2026-05-31

---

## Findings Summary

### Finding 1 — Balanced Opportunity Fund in net decumulation
Composite score **18.3 / 100** (vs Fixed Income 98.8). Book multiple **0.86×** — the only fund where AUM is below capital deployed. Customers have withdrawn more than they invested net. Requires a 30-day diagnostic sprint and a redesign or consolidation decision.

### Finding 2 — Capital Growth: biggest fund, highest churn
**47.2% strict churn** on 3,779 accounts. 36-month cohort survival only 54.2% vs Fixed Income's 77.2%. Book multiple is the highest (3.45×), meaning capital grows while being gathered — then it leaves. Win-back and RM redeployment are the fastest fixes.

### Finding 3 — 68% of AUM concentrated in the top 10% of customers
857 customers hold an estimated ৳205 Cr. No differentiated service tier exists. A single cluster of high-value churners would constitute an outsized balance-sheet event.

### Finding 4 — RM incentives reward sign-ups, not retention
Two high-volume RMs (Mohammad Jasim Ahmed, Jannatul Islam) sit above median volume but below median 1-year retention. Best performer MST. Sonia Sheikh achieves 91.8% 1-year retention on 296 accounts vs platform average 86.2%. The gap is incentive design, not individual capability.

### Finding 5 — ৳8.02 Cr in cross-sell sits in existing relationships
Three plays: (1) single → second-fund for 4,251 active customers — ৳5.1 Cr; (2) Non-SIP → SIP migration for 348 lump-sum customers — ৳2.9 Cr/yr recurring; (3) high-value singles under cross-capable RMs (2,273 customers) — ৳2.7 Cr. Zero acquisition cost — all via existing RM relationships.

---

## Customer Segments (K-Means, k=4, silhouette 0.42)

| Segment | Customers | Median Age | Median AUM | Multi-fund % |
|---------|-----------|------------|------------|--------------|
| Senior High-Ticket | 2,129 | 45 | ৳3.12L | 34.5% |
| Lump-sum Legacy | 909 | 47 | ৳0 (fully withdrawn) | 9.9% |
| Core SIP | 5,167 | 33 | ৳36K | 13.4% |
| Long-horizon SIP | 330 | 34 | ৳57.6K | 18.8% |

Lump-sum Legacy (909 customers, ৳0 AUM) are dormant re-engagement targets with known investment capacity, not lost customers.

---

## Prioritised Actions

| # | Action | Owner | Timeline |
|---|--------|-------|----------|
| 1 | Diagnose Balanced Opp. Fund — exit survey + fee audit | Head of Funds / PM | 30 days |
| 2 | Win-back Capital Growth closed accounts (<24 months) | Head of Sales / Ops | 2 weeks |
| 3 | Coach flagged RMs; tie incentive to 1-yr retention gate | Sales Manager | 2 weeks |
| 4 | Auto-flag first missed SIP → save-the-SIP call same day | Head of Retention / Ops | 30 days |
| 5 | Pre-empt post-dividend surrenders with reinvest offer | Marketing + PM | 1 month |
| 6 | Launch Senior High-Ticket coverage (857 customers) | Head of Sales / Wealth | 30 days |
| 7 | Second-fund campaign to 4,251 single-fund customers | Head of Sales | 60 days |
| 8 | Non-SIP → SIP migration for 348 lump-sum customers | Head of Sales | 60 days |

---

## Deliverables

**`apex_analysis_final.ipynb`** — Primary deliverable. Self-contained notebook covering data loading, cleaning, all three analytical sections, and synthesis. Open in Jupyter or VS Code. No external dependencies beyond the source files in `raw/`.

**`apex_dashboard.html`** — Open in any browser. Five tabs: Overview, Funds, Customers, RM Performance, 5 Findings. All charts are interactive (Chart.js). No server required — single file, fully self-contained.

**`apex_presentation.html`** — Open in any browser. 10-slide deck with speaker notes. Navigate with arrow keys or the bottom nav bar. Print-to-PDF supported (`@media print` outputs one slide per page).

---

## Methodology Notes

- **SIP persistency ≠ retention.** Persistency measures whether installments are paid. A customer can maintain 100% persistency and still close their account (Capital Growth demonstrates this: 88.6% persistency, 47.2% churn). Do not substitute one metric for the other.
- **Book multiple = AUM ÷ onboarding capital.** Measures capital retention over time, not investment performance. No NAV data was available.
- **Churn = strict** (closed + discontinued) unless marked otherwise. Inactive accounts are excluded from the headline rate but reported as sensitivity. Suspended (2 accounts) excluded from all denominators.
- **2026 data is partial** (Jan–May only, through the 2026-05-31 snapshot). All 2026 totals understate the full year; 2025 is the latest complete year.
- **Customer key = Mobile No** per the case brief. Shared or changed numbers may cause ~1–3% count inaccuracy.
