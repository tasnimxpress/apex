# AGENT 2 — ANALYSIS

## Your one job
Answer the 3 case sections with depth, consuming ONLY Agent 1's `clean/` tables.
Produce metrics, figures, and a findings log. **You do not clean data and you do not
re-define business rules** — if a clean table looks wrong, raise it; don't patch it.
Every analysis must end in a *business statement*, not just a number.

## Read first
- `definitions.yaml`
- Agent 1's `derived_field_dictionary.md`
- Gate 1 sign-off in `qa/qa_report.md` (do not start until it passes)

## Guiding principle (this is what separates strong from average)
For every metric ask: "what does this mean for AUM, and for the decision the manager
makes Monday?" Always report VALUE-weighted alongside count-weighted. Use cohorts,
not just snapshots. Treat SIP persistency — not SIP acquisition — as the core asset.

## Stage A — Section 1: Fund Performance → `analysis/section1/`
- Fund scorecard: account growth, status mix, AUM (Investment Value at Market), net flow (account- AND value-weighted), discontinuation rate, closure rate.
- **SIP persistency**: installments actually paid vs. expected (from `monthly_flows` cadence); persistency-decay curve by fund and by onboarding vintage.
- **Cohort/vintage survival** by onboarding year (retention curves; Kaplan-Meier if feasible).
- AUM-vs-invested-capital gain multiple per fund; surrender-timing vs. dividend-distribution pattern (do surrenders spike after dividends / near maturity?).
- Composite fund ranking (define weights, justify them) + per-fund recommendation.

## Stage B — Section 2: Acquisition & Segmentation → `analysis/section2/`
- Customer-level demographic & financial profiling (use `customers` table).
- **Clustering** per `definitions.yaml clustering`: standardize, search k, validate with elbow + silhouette, profile each cluster, map clusters → funds. Recommend target segment per fund.
- Cross-sell sizing **in Taka**: multi-fund penetration; high-value single-fund customers serviced by RMs who already sell other funds; SIP↔Non-SIP migration candidates. Quantify the latent wallet.

## Stage C — Section 3: RM Productivity → `analysis/section3/`
- RM scorecard: unique customers onboarded, avg installment, AUM introduced (on Introducer).
- **Per-RM 1-year cohort retention** (acquisition quality) — the high-volume / low-quality flag.
- Volume × value quadrant; fund-specialization via HHI.
- Team year-over-year: onboarding, retention, net-flow trajectory. Systemic vs. individual diagnosis + actions (coaching / allocation / incentive).

## Stage D — Synthesis → `analysis/synthesis/`
- Cross-cut fund × segment × RM. Convert each finding to a SPECIFIC, owner-assigned recommendation tied to a number.

## Outputs
- Metric tables (CSV) + figures (PNG/SVG, clean labels, presentation-ready) under each section folder
- `findings_log.md` — one headline insight per analysis, each phrased as a decision

## Mandatory caveat to state
There is NO NAV/return series. "Fund performance" here = flow, retention, engagement —
NOT investment return. Say this explicitly.

## Done when
Agent 3 Gate 2 passes (every metric independently reproduced, rates bound-checked,
clustering stable, cohort denominators correct).
