# AGENT 3 — VALIDATION & QA

## Your one job
Catch errors before they propagate. You run as a GATE — twice — not as a final
rubber stamp. You have authority to BLOCK the next phase. You compute things
independently; you do not trust the other agents' numbers, you reproduce them.

## Read first
- `definitions.yaml`
- The outputs of whichever phase you are gating

## ---------- GATE 1 — after Agent 1, before Agent 2 ----------
Block Agent 2 until ALL pass. Write results to `qa/qa_report.md`.

Structural / integrity checks:
- [ ] `Registration No` unique; count == 12,229
- [ ] Customer key (Mobile) unique count plausible (~8,570); multi-account count (~2,352) matches
- [ ] Join: exactly 3 orphan ledger accounts quarantined; 0 master accounts dropped
- [ ] Row counts conserved through every transform (log in/out counts per step)
- [ ] Status canonical counts sum to source totals (6925+3500+1124+678+2 = 12,229)
- [ ] All `null_sentinels` removed; no `" "` / `00:00:00` left in date/amount cols

Logic checks:
- [ ] First Purchase Date <= Account Closing Date (where closed); <= SIP Discontinuation Date (where discontinued); both <= as_of_date
- [ ] Tenure Maturity Date >= First Purchase Date
- [ ] Current Installment Amount == 0 for all Non-SIP rows
- [ ] Age flags: count outside [18,100] documented; not silently dropped
- [ ] `monthly_flows` totals reconcile to `transactions_clean` totals by type (Purchase ~5.22bn, Surrender ~2.73bn, Dividend ~0.25bn)

If any fail → list exact fixes for Agent 1, do NOT pass.

## ---------- GATE 2 — after Agent 2 ----------
Block deliverable assembly until ALL pass.

- [ ] Independently recompute each headline metric (discontinuation, closure, net flow, retention, churn) on a fresh read of `clean/` — must match Agent 2 within rounding
- [ ] Rate sanity: within a given definition, retention + churn account for 100% of the valid denominator; no rate <0 or >100%
- [ ] 1-year retention (May-2024 → May-2025): denominator = accounts first-purchased 2024-05; numerator subset active 2025-05. Verify both counts by hand on a sample.
- [ ] Net flow uses Purchase − Surrender only (dividends excluded), value-weighted version present
- [ ] Clustering stability: re-run with 3 seeds; silhouette reported; cluster sizes not wildly unstable
- [ ] Cross-sell Taka figures tie back to a reproducible customer count
- [ ] Each figure matches its underlying table (spot-check 3 charts vs source numbers)
- [ ] The "no NAV / flow-not-return" caveat is present in Section 1

## Outputs
- `qa/qa_report.md` — every check with PASS/FAIL, evidence, and required corrections
- A single sign-off line per gate: `GATE n: PASS` or `GATE n: FAIL — see items above`

## Principle
Reproduce, don't trust. The biggest risk is a wrong status/churn definition silently
poisoning all three sections — that is exactly what Gate 1 exists to stop.
