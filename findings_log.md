# Findings Log — Apex Asset Management (Agent 2, Analysis)

**As-of:** 2026-05-31 · One headline per analysis, phrased as a **decision the manager makes Monday**.
All figures are *flow / retention / engagement* — **NOT investment return** (no NAV series exists).
Every number below is reproduced from `clean/` by the notebooks in `analysis/` and persisted to each
section's `_metrics.json` for Gate 2.

---

## Section 1 — Fund Performance

1. **Defend Fixed Income's lead by fixing the others, don't re-allocate growth spend to it.**
   Composite durable-growth ranking: **Fixed Income 98.8 / Shariah 59.3 / Capital Growth 56.5 /
   Balanced Opportunity 18.3** (0–100). Fixed Income wins on every pillar; the gap is a retention
   gap in the other three, not a sales gap.

2. **Capital Growth is the leakiest fund — put a win-back team on it.**
   Strict churn (closed+discontinued) is highest in **Capital Growth (47.2%)**; its 36-month cohort
   survival is only ~54% vs **Fixed Income ~77%**. It still posts +৳68 Cr lifetime net flow, so the
   money is being gathered and then lost — a classic leaky bucket.

3. **SIP persistency is high but front-loaded — wire a save-call to the first missed installment.**
   Overall **87.9%** of expected installments are actually paid; persistency is similar across funds
   (~88%, Balanced Opportunity lowest at ~84%). The decay curve shows attrition concentrates in the
   early months, so the cheapest retention win is an automated flag the first month an installment
   stops arriving (detectable in `monthly_flows`).

4. **Surrenders spike the month *after* a dividend, not during it — issue a reinvest offer with the
   distribution.** Surrenders run **~20.4%** of volume in the month following the Jul/Jan dividend
   distributions vs a **16.7%** uniform baseline. Pre-empt the redemption with a dividend-reinvestment
   offer mailed *with* each distribution.

## Section 2 — Acquisition & Segmentation

5. **Grow AUM by selling a second fund to existing customers — it's the cheapest AUM available.**
   **~82%** of customers hold a single fund and the **top 10% of customers hold ~68% of book AUM**.
   Four stable segments (k=4; silhouette 0.42; **ARI = 1.0 across 3 seeds**) separate a high-value
   lump-sum tier, committed SIP savers, the young small-ticket mass, and a dormant non-SIP group.

6. **Run two sized cross-sell plays now.** Single→second-fund for **4,251** active single-fund
   customers (~**৳5.1 Cr** at the median onboarding ticket) and Non-SIP→SIP migration for **348**
   lump-sum-only customers (~**৳2.9 Cr/yr** recurring). Warm-lead subset: **2,273** high-value
   single-fund customers already serviced by a cross-capable RM — start there.

## Section 3 — RM Productivity

7. **Re-tie RM incentives to 1-year retention, not raw sign-ups.** Overall 1-yr cohort retention of
   the official-RM book is **86.2%**; the case cohort (May-2024 → May-2025, reconstructed
   point-in-time) is **84.6% (115/136)**. Two high-volume RMs — **MOHAMMAD JASIM AHMED** and
   **JANNATUL ISLAM** — sit below median retention while above median volume: coach, don't celebrate.

8. **Deploy high-retention specialists onto the leakiest fund.** RM fund-specialisation (HHI) shows
   several near single-fund specialists; pair the highest-retention specialists with **Capital Growth**
   (the highest-leakage fund) instead of retraining them. Team 1-yr retention dipped across the
   2021→2023 vintages (≈90%→84%) before recovering — a mild *systemic* signal, while the two flagged
   RMs are *individual* cases.

## Synthesis

9. **Apex's growth problem is a retention problem, not an acquisition problem.** Net flow is strongly
   positive and growing (to **+৳37.8 Cr** for the 2025 vintage; **+৳249 Cr** lifetime) but is
   concentrated in one fund while the others leak, the base is overwhelmingly single-fund, and a
   couple of RMs acquire faster than they retain. The three highest-leverage, owner-assigned moves:
   (1) defend the leakiest fund + fix SIP persistency at first missed installment; (2) second-fund
   campaign to single-fund holders; (3) re-tie RM incentives to 1-year retention. Full owner-assigned
   list: `analysis/synthesis/tables/recommendation_register.csv`.
