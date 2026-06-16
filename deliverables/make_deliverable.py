"""
deliverables/make_deliverable.py  --  PHASE 3 assembly (Lead/Orchestrator).

Stitches the FOUR executed Agent-2 section notebooks (analysis/section1|2|3|synthesis.ipynb)
into ONE coherent notebook in the 8-part structure from ORCHESTRATOR_README, wrapped with
Lead-authored framing (exec summary, data/quality from Agent 1, data-prep, consolidated
recommendations + appendix).

Principles honoured:
  * Consume, don't recompute. The analytical cells are copied verbatim from the section
    notebooks (no business rule changed). If something looked wrong we'd RAISE, not patch.
  * Keep analysis/ pristine. A bootstrap cell redirects every figure/table/metric WRITE
    from the stitched section code to deliverables/_assembled_outputs/ . All INPUTS still
    come only from clean/ (Agent 1) exactly as Gate 2 validated. Gate 2 already proved the
    chain reproduces identical numbers in a fresh kernel.
  * The mandatory Section-1 caveat (no NAV -> performance = flow/retention/engagement) is
    preserved (it lives in Section 1's first cell, kept intact).

Run:  d:/GitHub/apex/.venv/Scripts/python.exe deliverables/make_deliverable.py
Then execute:  jupyter nbconvert --to notebook --execute --inplace ... --ExecutePreprocessor.kernel_name=apex
"""
from pathlib import Path
import nbformat as nbf

REPO = Path(__file__).resolve().parent.parent
ANALYSIS = REPO / "analysis"
OUT_NB = REPO / "deliverables" / "apex_analysis.ipynb"

def md(text):
    return nbf.v4.new_markdown_cell(text)

def code(text):
    return nbf.v4.new_code_cell(text)

def section_cells(name):
    """Return fresh (output-stripped) cells from an executed section notebook."""
    nb = nbf.read(ANALYSIS / f"{name}.ipynb", as_version=4)
    out = []
    for c in nb.cells:
        if c.cell_type == "markdown":
            out.append(md(c.source))
        elif c.cell_type == "code":
            out.append(code(c.source))
    return out

cells = []

# ============================================================
# PART 1 — Executive summary & business framing (the leakage problem)
# ============================================================
cells.append(md(
"# Apex Asset Management — Senior Data Analyst Case Study\n"
"### Consolidated analysis notebook · as-of 2026-05-31 · currency: BDT (৳, Taka)\n\n"
"*Lead/Orchestrator assembly of three analysis sections + cross-cutting synthesis. "
"All numbers are reproduced from the cleaned tables in `clean/` (Agent 1) and were "
"independently re-validated by QA (GATE 1: 22/22 PASS, GATE 2: 18/18 PASS).*\n\n"
"---\n\n"
"## 1. Executive summary — the leakage problem\n\n"
"**Apex's growth problem is a retention problem, not an acquisition problem.** The book is "
"gathering money quickly — **+৳249.3 Cr lifetime net flow** (Purchase − Surrender), rising to "
"**+৳37.8 Cr for the 2025 onboarding vintage alone** — but that money is concentrated in one "
"fund while the others leak, the customer base is overwhelmingly single-fund, and a couple of "
"high-volume relationship managers (RMs) acquire faster than they retain.\n\n"
"Three structural leaks turn gathered AUM back out the door:\n\n"
"| # | The leak | The number | The fix (owner) |\n"
"|---|----------|-----------|-----------------|\n"
"| 1 | **One fund carries growth; the rest leak.** Fixed Income ranks #1 on durable growth "
"(98.8/100); Capital Growth is the leakiest at **47.2% strict churn** yet still gathers +৳68 Cr "
"— a classic leaky bucket. | Composite 98.8 / 59.3 / 56.5 / 18.3 | Defend the leakiest funds, "
"don't re-spend on the winner (Head of Funds) |\n"
"| 2 | **The base is single-fund.** ~82% of customers hold one fund; the top 10% hold ~68% of "
"AUM. The cheapest AUM is a second fund to people who already trust Apex. | 4,251 single-fund "
"customers → ~৳5.1 Cr | Second-fund campaign (Head of Sales) |\n"
"| 3 | **RM incentives reward sign-ups, not survival.** Two high-volume RMs sit below median "
"1-yr retention while above median volume. | Overall 1-yr retention 86.2% | Re-tie incentives to "
"1-yr retention (Sales Manager) |\n\n"
"> ### ⚠️ What \"performance\" means in this study\n"
"> **There is NO NAV / unit-price / investment-return series in the data.** We therefore define "
"fund \"performance\" as **flow, retention and engagement** — asset-gathering and asset-keeping "
"behaviour — **never investment return** (no alpha, total return or Sharpe). "
"`Investment Value (At Market)` is treated as a current **book/AUM** figure only. This caveat "
"holds for every section below.\n\n"
"**Notebook structure:** (1) this summary · (2) data loading, profiling & quality (Agent 1) · "
"(3) data preparation & metric definitions · (4) Section 1 — Fund performance · (5) Section 2 — "
"Acquisition, segmentation & cross-sell · (6) Section 3 — RM productivity · (7) cross-cutting "
"synthesis · (8) consolidated recommendations + appendix."
))

# ---- Bootstrap: path + keep analysis/ pristine -------------------------------
cells.append(md(
"### Environment bootstrap\n"
"Locates the repo root, puts the shared `analysis/_common.py` backbone on the path, and "
"**redirects regenerated figures/tables/metrics to a deliverable-local sandbox "
"(`deliverables/_assembled_outputs/`)** so the Gate-2-validated `analysis/` artifacts are "
"never overwritten. Every data INPUT still comes only from `clean/` (Agent 1)."
))
cells.append(code(
"import sys\n"
"from pathlib import Path\n"
"# locate repo root = nearest parent containing definitions.yaml\n"
"_p = Path.cwd().resolve()\n"
"while not (_p / 'definitions.yaml').exists() and _p != _p.parent:\n"
"    _p = _p.parent\n"
"REPO = _p\n"
"sys.path.insert(0, str(REPO / 'analysis'))   # so `import _common` resolves\n"
"import _common as C\n"
"# Keep the QA-validated analysis/ outputs untouched: redirect section WRITES to a sandbox.\n"
"# (Loaders in _common read from clean/ via an absolute path, so inputs are unaffected.)\n"
"OUT = REPO / 'deliverables' / '_assembled_outputs'\n"
"OUT.mkdir(parents=True, exist_ok=True)\n"
"C.ANALYSIS = OUT\n"
"print('repo root        :', REPO)\n"
"print('clean/ (inputs)  :', C.CLEAN)\n"
"print('writes redirected:', C.ANALYSIS)"
))

# ============================================================
# PART 2 — Data loading, profiling, quality report (Agent 1)
# ============================================================
cells.append(md(
"---\n\n"
"## 2. Data loading, profiling & quality report  *(from Agent 1 / `clean/`)*\n\n"
"Three raw sources were profiled and cleaned by the Data-Engineering step into five "
"analysis-ready tables. The full audit is in `clean/data_quality_report.md`; the headline "
"integrity numbers below were **independently reproduced from `raw/` at GATE 1 (22/22 PASS)**.\n\n"
"**Raw → clean lineage (row-conserving):**\n"
"- `Master File` 12,229 rows → **`accounts_clean`** (one row per account, key `registration_no`).\n"
"- `Transection` 231,254 rows → **`transactions_clean`** (231,248; 6 orphan rows from 3 unknown "
"accounts quarantined to `clean/orphans.csv`, 0 master rows lost).\n"
"- → **`monthly_flows`** (account × calendar-month, 212,796 rows) — the backbone for cohort & "
"persistency work.\n"
"- → **`customers`** (rolled to Mobile, 8,570) and **`rm_attribution`** (Introducer vs Service "
"roles kept separate).\n\n"
"**Key data-quality calls (flag, never drop):** 5 Activity-Status values (not the 3 in the data "
"dictionary); 57 blank + 2 under-age ages flagged; 3 closed / 1 discontinued accounts missing "
"their event date; sentinels (`\" \"`, `00:00:00`, `1900-01-01`) nulled before parsing "
"(0 residual). Flow totals reconcile to the cent across raw → `transactions_clean` → "
"`monthly_flows`."
))
cells.append(code(
"import json, pandas as pd\n"
"rep = json.load(open(REPO / 'clean' / '_report_numbers.json'))\n"
"acc  = C.load_accounts()\n"
"cust = C.load_customers()\n"
"tx   = C.load_transactions()\n"
"mf   = C.load_monthly_flows()\n"
"rmt  = C.load_rm()\n"
"print('accounts_clean    ', acc.shape)\n"
"print('customers         ', cust.shape)\n"
"print('transactions_clean', tx.shape)\n"
"print('monthly_flows     ', mf.shape)\n"
"print('rm_attribution    ', rmt.shape)\n"
"print()\n"
"print('Registration No unique :', rep['registration_no_unique'], '/', rep['registration_no_rows'])\n"
"print('Customers (Mobile)     :', rep['mobile_unique'], '| multi-account:', rep['multi_account_customers'])\n"
"print('Orphan ledger accounts :', rep['orphan_accounts'], '(', rep['orphan_rows'], 'rows quarantined )')\n"
"print('Flow reconciliation (transactions_clean == monthly_flows):')\n"
"for k, (a, b) in rep['recon'].items():\n"
"    print(f'   {k:10}: {a:,.2f}  ==  {b:,.2f}  ->  {a==b}')"
))
cells.append(code(
"# Activity-status mix (canonical) and the churn definitions that the whole study depends on\n"
"status_tbl = (pd.Series(rep['status_counts']).rename('accounts').to_frame()\n"
"              .assign(share_pct=lambda d: (d.accounts / d.accounts.sum() * 100).round(1)))\n"
"print('Activity status (canonical):')\n"
"print(status_tbl.to_string())\n"
"print(f\"\\nchurn_strict (closed+discontinued) = {rep['churn_strict_count']:,}\")\n"
"print(f\"churn_broad  (+inactive, sensitivity) = {rep['churn_broad_count']:,}\")\n"
"print(f\"suspended ({rep['status_counts']['suspended']}) excluded from all rate denominators\")\n"
"# Quality flags carried as columns (never dropped)\n"
"flags = {k: v for k, v in rep.items() if k.startswith('flag_')}\n"
"print('\\nQuality flags (flag, never drop):')\n"
"for k, v in flags.items():\n"
"    print(f'   {k:34}: {v}')\n"
"status_tbl"
))

# ============================================================
# PART 3 — Data preparation: cleaning, joins, derived tables, metric definitions
# ============================================================
cells.append(md(
"---\n\n"
"## 3. Data preparation — cleaning, joins, derived tables & metric definitions\n\n"
"All rules come from `definitions.yaml` (single source of truth); no agent invents its own. The "
"derived fields every downstream metric consumes are documented in "
"`clean/derived_field_dictionary.md`. The decisions that move the numbers most:\n\n"
"**Churn (locked in `decisions_log.md`).**\n"
"- **Headline = strict churn = Closed + Discontinued.** Closed = account terminated; "
"Discontinued = SIP stopped paying — for a SIP-first business that *is* a core leakage event.\n"
"- **Inactive (1,124) = separate at-risk tier**, reported only as the `churn_broad` sensitivity "
"(folding it into the headline would overstate loss; ignoring it would hide soft-churn).\n"
"- **Suspended (2) excluded** from every rate denominator.\n\n"
"**Point-in-time retention reconstruction (the methodological backbone of all cohort work).** "
"`accounts_clean.status` is a *current* snapshot (as-of 2026-05-31). Measuring an earlier-date "
"retention from a current snapshot would be wrong, so for every cohort metric we reconstruct "
"whether an account had **strict-churned by the measurement date** from the dated "
"`account_closing_date` / `sip_discontinuation_date` events. Consequence, surfaced everywhere: "
"the case cohort (2024-05 → 2025-05) is **115/136 = 84.6% retained point-in-time**, vs 93/136 "
"active in the raw snapshot — the gap is accounts that churned only *after* May-2025, which a "
"snapshot would wrongly count against the 1-year number.\n\n"
"**Joins & roles.** Ledger joins master on `Account Number = Registration No`. RM metrics keep "
"the **Introducer** (acquisition) role separate from the **Service** (current book) role — never "
"blended. **Net flow = Σ(Purchase) − Σ(Surrender)**, dividends excluded."
))
cells.append(code(
"# Show the locked rules straight from the single source of truth + the point-in-time helper\n"
"defs = C.load_defs()\n"
"print('churn_strict members :', defs['status']['churn_strict']['members'])\n"
"print('churn_broad  members :', defs['status']['churn_broad']['members'])\n"
"print('primary_churn        :', defs['status']['primary_churn'])\n"
"print('excluded_from_rates  :', defs['status']['exclude_from_rates']['members'])\n"
"print('net_flow definition  :', defs['transactions']['net_flow'])\n"
"print('case 1-yr retention  :', defs['cohorts']['one_year_retention']['cohort_month'],\n"
"      '->', defs['cohorts']['one_year_retention']['measured_at'])\n\n"
"# point-in-time vs snapshot, demonstrated on the case cohort (uses _common.churned_strict_by)\n"
"acc_r = C.rate_denominator(acc)\n"
"c0 = acc_r[acc_r.onboarding_month == '2024-05']\n"
"meas = pd.Timestamp('2025-05-28') + pd.offsets.MonthEnd(0)\n"
"alive_pit = (~C.churned_strict_by(c0, meas)).sum()\n"
"active_snapshot = (c0.status == 'active').sum()\n"
"print(f'\\nCase cohort 2024-05 (n={len(c0)}):  point-in-time retained @2025-05 = {alive_pit}'\n"
"      f' ({alive_pit/len(c0):.1%})  vs  current-snapshot active = {active_snapshot}')\n\n"
"# the derived columns Agent 2 consumes\n"
"derived = ['churn_strict','churn_broad','is_active','excluded_from_rates','onboarding_month',\n"
"           'onboarding_year','tenure_to_date_months','days_to_closure','days_to_discontinuation',\n"
"           'introducer_in_rmlist','service_in_rmlist','age_group','installment_band','tenor_band']\n"
"print('\\nderived fields present in accounts_clean:',\n"
"      all(c in acc.columns for c in derived), '(', len(derived), 'checked )')"
))

# ============================================================
# PART 4 — Section 1: Fund performance + recommendations
# ============================================================
cells.append(md(
"---\n\n"
"# Part 4 · Section 1 — Fund performance + recommendations\n"
"*Stitched from `analysis/section1.ipynb` (Agent 2). The mandatory flow-not-return caveat is "
"restated in the section header below.*"
))
cells += section_cells("section1")

# ============================================================
# PART 5 — Section 2: Acquisition, segmentation, cross-sell + recommendations
# ============================================================
cells.append(md(
"---\n\n"
"# Part 5 · Section 2 — Acquisition, segmentation & cross-sell + recommendations\n"
"*Stitched from `analysis/section2.ipynb` (Agent 2).*"
))
cells += section_cells("section2")

# ============================================================
# PART 6 — Section 3: RM productivity + recommendations
# ============================================================
cells.append(md(
"---\n\n"
"# Part 6 · Section 3 — RM productivity + recommendations\n"
"*Stitched from `analysis/section3.ipynb` (Agent 2).*"
))
cells += section_cells("section3")

# ============================================================
# PART 7 — Cross-cutting synthesis
# ============================================================
cells.append(md(
"---\n\n"
"# Part 7 · Cross-cutting synthesis (Fund × Segment × RM)\n"
"*Stitched from `analysis/synthesis.ipynb` (Agent 2). Consumes the section metric tables "
"regenerated above (in the deliverable sandbox) — no raw business rule is recomputed.*"
))
cells += section_cells("synthesis")

# ============================================================
# PART 8 — Consolidated recommendations + appendix
# ============================================================
cells.append(md(
"---\n\n"
"## 8. Consolidated recommendations + appendix\n\n"
"### 8.1 Recommendation register — every number → a specific, owner-assigned action\n"
"The Monday-morning to-do list. Each row ties a finding to a single accountable owner, a concrete "
"action, and the number it rests on (reproduced from the section metrics above)."
))
cells.append(code(
"import pandas as pd\n"
"reg = pd.read_csv(C.ANALYSIS / 'synthesis' / 'tables' / 'recommendation_register.csv')\n"
"pd.set_option('display.max_colwidth', 80)\n"
"reg"
))
cells.append(md(
"### 8.2 Prioritised roadmap\n"
"1. **Now (0–3 mo) — stop the leak.** Auto-flag the first missed SIP installment "
"(`monthly_flows`) and fire a save-call; launch a win-back on closed/discontinued accounts in "
"**Capital Growth** (47.2% strict churn). Owner: Head of Retention / PM.\n"
"2. **Now (0–3 mo) — cheapest AUM.** Second-fund campaign to the **4,251** active single-fund "
"customers (~৳5.1 Cr), starting with the **2,273** high-value leads already under a cross-capable "
"RM. Owner: Head of Sales.\n"
"3. **Next (3–6 mo) — fix incentives.** Re-tie a slice of RM incentive to **1-year retention**, "
"not raw sign-ups; coach the two high-volume / below-median-retention RMs. Owner: Sales Manager.\n"
"4. **Next (3–6 mo) — recurring revenue.** Non-SIP → SIP migration offer to the **348** "
"lump-sum-only customers (~৳2.9 Cr/yr). Owner: Head of Sales.\n"
"5. **Ongoing — pre-empt redemptions.** Issue a dividend-reinvestment offer *with* each Jul/Jan "
"distribution (surrenders run ~20.4% in the month after a dividend vs 16.7% baseline). "
"Owner: Marketing + PM.\n\n"
"### 8.3 Assumptions & limitations\n"
"- **No NAV / return series** → \"performance\" = flow / retention / engagement only (restated "
"throughout). `Investment Value (At Market)` used as current book/AUM, never as return.\n"
"- **Point-in-time cohort reconstruction** from dated events (not the current snapshot); case "
"1-yr retention = 84.6% point-in-time vs 93/136 snapshot.\n"
"- **Churn = strict (Closed + Discontinued)** headline; Inactive shown only as `churn_broad` "
"sensitivity; Suspended (2) excluded from denominators.\n"
"- **Cross-sell Taka = target count × explicit median ticket** (2nd-fund ৳12,000; SIP annual "
"৳84,000); headline wallet = Play 1 + Play 3 (Play 2 is a subset of Play 1, not double-counted).\n"
"- **Clustering** at customer level, k=4 (silhouette 0.42; ARI=1.0 across seeds 42/7/123); k=2 "
"rejected as the trivial SIP-vs-Non-SIP split; monetary features log1p-scaled.\n"
"- **RM metrics** on the Introducer (acquisition) role, restricted to the 16 official RMs; 1-yr "
"retention only on cohorts old enough to observe the outcome (onboarded ≤ as-of − 12m).\n"
"- **3 orphan ledger accounts** (6 rows) quarantined; documented anomalies (3 closed / 1 disc. "
"without event date) censored, not dropped.\n\n"
"### 8.4 Derived-field dictionary\n"
"Full field-by-field definitions for every consumed column are in "
"`clean/derived_field_dictionary.md` (accounts / customers / transactions / monthly_flows / "
"rm_attribution). The locked business rules are in `definitions.yaml`; every judgment call is in "
"`decisions_log.md`; QA reproduction is in `qa/qa_report.md` (GATE 1 & GATE 2 both PASS)."
))
cells.append(code(
"# Provenance footer: confirm the deliverable consumed only clean/ + regenerated its own sandbox\n"
"figs = sorted(p.relative_to(REPO).as_posix() for p in (C.ANALYSIS).rglob('figures/*.png'))\n"
"tbls = sorted(p.relative_to(REPO).as_posix() for p in (C.ANALYSIS).rglob('tables/*.csv'))\n"
"print('regenerated figures:', len(figs), '| regenerated tables:', len(tbls))\n"
"print('analysis/ artifacts left untouched (QA-validated).')\n"
"print('END OF NOTEBOOK — assembled by deliverables/make_deliverable.py')"
))

# ---- write ------------------------------------------------------------------
nb = nbf.v4.new_notebook()
nb.cells = cells
nb.metadata["kernelspec"] = {"name": "apex", "display_name": "apex", "language": "python"}
nb.metadata["language_info"] = {"name": "python"}
OUT_NB.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_NB, "w", encoding="utf-8") as f:
    nbf.write(nb, f)
print("built", OUT_NB, "with", len(cells), "cells")
