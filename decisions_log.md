# Decisions Log — Apex Asset Management Case Study

Every judgment call that affects results goes here, with rationale and date.
Append-only. Newest at the bottom.

---

## 2026-06-16 — Churn / Activity Status treatment  [OWNER: Lead]

**Context:** Source `Activity Status` has 5 values, not the 3 in the data dictionary:
Active 6,925 | Closed 3,500 | Inactive 1,124 | Discontinue 678 | Suspended 2.
"Inactive" and "Suspended" are undocumented. This choice moves every churn number,
so it is locked before Agent 1 runs.

**Decision:**
- **Headline churn = strict = Closed + Discontinued.**
  - Closed = account terminated -> unambiguous loss.
  - Discontinue = SIP stopped paying -> for a SIP-first business this IS the core
    leakage event; the case formulas separate Discontinuation Rate from Closure Rate,
    confirming the business treats both as real loss types.
- **Inactive (1,124) = separate "at-risk" tier, reported as broad-churn sensitivity.**
  - Undocumented; likely dormant-but-recoverable, not confirmed lost. Folding into the
    headline would overstate loss; ignoring it would hide soft-churn. Reporting it as a
    distinct tier is honest AND yields a recommendation (reactivation play).
  - Note: Inactive (1,124) > Discontinue (678), so its treatment visibly moves the
    story -- to be surfaced explicitly in the writeup/interview.
- **Suspended (2) = excluded from all rate denominators, logged.**
  - Too small to matter; ambiguous (likely admin/compliance hold, not customer behavior).

**Encoded in:** definitions.yaml -> status.churn_strict / churn_broad /
primary_churn: churn_strict / exclude_from_rates: [suspended]. No file change needed;
this entry confirms the default is deliberate, not unreviewed.

---

## 2026-06-16 — Agent 1 data-engineering judgment calls  [OWNER: Agent 1]

All of the following are decisions made while building `clean/` tables. None alter
business rules in `definitions.yaml`. Validation numbers handed to QA gate below.

1. **Orphan ledger accounts (3 / 6 rows).** `ABF-002091`, `IIF-SIP-000267-wr`,
   `ISF-SIP-001766-Wrong` exist in the ledger but not in master. The latter two carry
   `-wr`/`-Wrong` suffixes (clear data-entry errors). Quarantined to `clean/orphans.csv`
   and excluded from `transactions_clean` and `monthly_flows`. 0 master accounts lose rows.
   (3 orphans = exactly the expected count.)

2. **RM List has names only, no CIF.** Built a canonical CIF↔name map from the union of
   master Service+Introducer (CIF, name) pairs: 42 distinct CIFs, all 1:1 (no CIF maps to
   >1 name). All 16 official RM List names resolve to a CIF. Canonical RM name = name from
   CIF where available, else the raw trimmed name. Did NOT invent CIFs for off-list RMs.

3. **Off-list RMs flagged, not dropped.** 6 Service RM names (9 accounts) and 172 Introducer
   names are not in the 16-name RM List. These are legacy/external introducers and a few
   service RMs without CIFs. Kept all rows; added `service_in_rmlist` / `introducer_in_rmlist`
   and `*_cif_missing` flags. Note: `Introducer RM CIF` is null on exactly the same 1,983
   rows where `Onboarding Department` is null (non-official-RM onboarding channel).

4. **Mobile↔Customer No. not perfectly 1:1.** 2 Mobiles map to >1 Customer No.; 3 Customer
   No. map to >1 Mobile. Per `definitions.keys`, Mobile is the customer key; Customer No.
   kept only as cross-check (`customer_no_primary` = first seen in `customers`). Did not
   attempt to merge/reconcile identities.

5. **`tenure_to_date_months` end-date choice.** Open accounts measured to AS_OF
   (2026-05-31); closed accounts measured to their closing date (capped at AS_OF). This is
   a derived tenure field for downstream use only — no churn/retention computed here.

6. **`monthly_flows` is sparse** (account×month only where a transaction exists; 212,796
   rows). Documented in the field dictionary; downstream cohort/persistency work should
   reindex onto a full month spine if a dense panel is required. (Did not build the dense
   spine — that is an analysis decision for Agent 2.)

7. **Quality anomalies flagged, never dropped:** Age 57 blank + 2 below-18 (both = 9);
   1 SIP account with tenor 0 (`AGF-SIP-002441`, closed); 3 Closed accounts missing a
   closing date; 1 Discontinued account missing a discontinuation date. All carry boolean
   flag columns in `accounts_clean`.

8. **Sentinel cleaning** applied per `definitions.null_sentinels` before any parsing.
   Post-clean residual sentinel count = 0 in all date and amount columns.

**Validation numbers for QA gate (all PASS):** Registration No 12,229 unique;
Mobile 8,570 unique; multi-account 2,352; orphans = 3 accounts (6 rows), 0 master dropped;
status sum 12,229 (6925/3500/1124/678/2); churn_strict 4,178; churn_broad 5,302;
NON SIP installment==0 for all 1,801; date-ordering violations all 0;
Purchase 5,219,456,433.47 / Surrender 2,726,818,228.83 / Dividend 249,886,432.00
reconcile exactly between transactions_clean and monthly_flows.

---

## 2026-06-16 — Agent 2 analysis judgment calls  [OWNER: Agent 2]

All consume ONLY `clean/` tables; none alter `definitions.yaml` business rules. Each is
encoded in the `analysis/` notebooks and persisted to `analysis/<section>/_metrics.json`.

1. **Point-in-time status reconstruction for all cohort/retention metrics.** `accounts_clean.status`
   is a *current* snapshot (as of AS_OF 2026-05-31). Measuring retention at an earlier date from the
   current snapshot would be wrong. For every cohort metric we reconstruct whether an account had
   strict-churned (closed OR discontinued) *by the measurement date* using the dated event columns
   `account_closing_date` / `sip_discontinuation_date` (`_common.churned_strict_by`). Consequence,
   surfaced explicitly: the case cohort (2024-05 → 2025-05) is **115/136 = 84.6% retained
   point-in-time**, vs 93/136 active in the *current* snapshot — the difference is accounts that
   churned only *after* May-2025, which a snapshot would wrongly count against the 1-yr number.

2. **SIP persistency = paid ÷ expected installments.** Per SIP account, paid = distinct months with a
   purchase in `monthly_flows`; expected = calendar months from onboarding to min(closing,
   discontinuation, AS_OF), capped at planned `tenor_in_month`, floored at 1. Ratio clipped to ≤1.0.
   Persistency-decay denominator at month k = SIP accounts whose expected window reaches k (avoids
   penalising young accounts that simply haven't aged into month k yet).

3. **Kaplan–Meier survival:** event = strict churn; duration = months (days/30.44) from first purchase
   to the matching dated event (closure for closed, discontinuation for discontinued), else censored
   at `tenure_to_date_months`. The 3 closed-without-date + 1 discontinued-without-date accounts (flagged
   by Agent 1) are **censored** at their tenure rather than dropped (event date unknowable). Suspended
   (2) excluded.

4. **Net flow reported value- AND account-weighted.** Value-weighted = Σ(purchase − surrender) in Taka
   from `monthly_flows` (dividends excluded, per `transactions.net_flow`); account-weighted =
   net_flow ÷ accounts in the fund. Headline uses value-weighted.

5. **Composite fund ranking weights (Section 1):** net-flow value 0.30, 36-mo cohort survival 0.25,
   SIP persistency 0.20, AUM scale 0.15, low strict-churn 0.10; each min-max normalised across the 4
   funds. Weights deliberately favour *durable growth* over raw size — justified inline in the notebook.

6. **Clustering deviations from `definitions.clustering` (logged, not silent):**
   (a) **k=2 rejected despite max silhouette (0.56).** It is the trivial SIP-vs-Non-SIP split (driven
   by the zero-installment mass) that we already capture via the `type_seg` field. We select the most
   informative k in [3,5] → **k=4** (silhouette 0.42, ARI=1.0 across seeds 42/7/123).
   (b) **Monetary features log1p-transformed before standardising.** `onboarding_amount` and
   `current_installment_amount` are heavily right-skewed; `definitions` says "standardize_numeric", so
   we standardise — but on log1p of the two monetary features so a handful of jumbo accounts don't
   dominate Euclidean distance. Age and tenor standardised as-is.
   (c) **Categorical features (`investment_type`, `fund`) used for cluster *profiling/mapping*, not as
   k-prototypes inputs.** `fund` is the target we map segments *to*; `investment_type` is collinear with
   installment. KMeans on the standardised numerics gives interpretable silhouettes; the categoricals
   enter via the cluster×fund and segment cross-tabs.

7. **Cross-sell Taka sizing is count × explicit per-customer ticket** (reproducible for Gate 2):
   second-fund ticket = median account onboarding amount (৳12,000); SIP annual = median SIP installment
   × 12 (৳84,000). Headline latent wallet = Play 1 + Play 3 only (Play 2 is a high-confidence subset of
   Play 1 — not added, to avoid double-counting).

8. **RM metrics attributed on Introducer (acquisition) role only**, restricted to the 16 official RMs
   (`introducer_in_rmlist`). Per-RM 1-yr retention uses only accounts onboarded ≤ AS_OF−12m (so the
   12-month outcome is observable); RMs with no such cohort are absent from the retention table (11 of
   16 have an observable 1-yr cohort). HHI = Σ(fund shareᵢ²)×10,000.

---

## 2026-06-16 — Phase 3 assembly judgment calls  [OWNER: Lead]

Building the two deliverables from the Gate-2-validated `analysis/` artifacts. No business
rule changed; nothing recomputed against new rules (that would bypass Gate 2).

1. **Stitched notebook reuses the section code verbatim, not a rewrite.**
   `deliverables/make_deliverable.py` reads the four executed section notebooks
   (`section1/2/3/synthesis`), strips their outputs, and concatenates the cells into the
   8-part ORCHESTRATOR structure with Lead-authored framing (Part 1 exec summary, Part 2
   data/quality from Agent 1, Part 3 data-prep & metric definitions, Part 8 consolidated
   recommendations + appendix). The analytical cells are unchanged, so the deliverable
   reproduces the exact Gate-2 numbers.

2. **Writes redirected to keep `analysis/` pristine.** A bootstrap cell repoints
   `_common.ANALYSIS` to `deliverables/_assembled_outputs/` so the stitched section code
   regenerates its figures/tables/`_metrics.json` into a deliverable-local sandbox rather
   than overwriting the QA-validated `analysis/` artifacts. All INPUTS still load only from
   `clean/` (Agent 1) via `_common`'s absolute paths. Verified after a fresh-`apex`-kernel
   `nbconvert --execute`: **0 error outputs across 42 code cells**, and the sandbox metrics
   match the canonical `analysis/` metrics exactly (overall 1-yr retention 0.8622, SIP
   persistency 0.8795, cross-sell wallet ৳80,244,000). The synthesis section reads the
   section metrics from the sandbox written earlier in the same run, so the notebook is
   self-contained and runs top-to-bottom with no hidden state.

3. **Mandatory Section-1 caveat preserved.** The "no NAV → performance = flow/retention/
   engagement, not investment return" caveat is kept intact in Section 1's header and is
   restated in the Part-1 exec summary, Part-3 definitions, the appendix, and on the deck's
   methodology and closing slides.

4. **Deck = exactly 10 slides, figures reused not redrawn.** `deliverables/make_deck.py`
   (python-pptx, 16:9) embeds the existing PNGs from `analysis/.../figures/` and pulls every
   headline number from the canonical `analysis/<section>/_metrics.json` (no retyped or
   conflicting values). One point per slide, business implication first, each number tied to
   an owner-assigned action. The point-in-time-retention assumption (84.6% vs 93/136
   snapshot) is called out explicitly on the methodology slide. Slide ceiling enforced and
   verified (10/10, no off-canvas shapes).

---

## (append further decisions below)
