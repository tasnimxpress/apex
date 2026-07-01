# Apex / IDLC — Senior Data Analyst Interview Prep

> Live coaching handoff file. This travels with the repo (git), so it opens on any device.
> Case: 1-on-1 in-person case-study presentation. Deliverables = `apex_analysis.ipynb`,
> `apex_presentation.html` (the slides), `apex_dashboard.html`.

---

## ⏩ HOW TO RESUME COACHING ON ANOTHER DEVICE

This chat session is stored **locally on the office machine** and does NOT sync across devices.
To continue the mock-interview coaching on your personal device:

1. Clone or pull this repo on the personal device.
2. Open it in Claude Code (VS Code extension or CLI).
3. Paste the **RESUME PROMPT** below into a fresh Claude session.

### RESUME PROMPT (copy-paste this)

```
You are my interview coach and mock examiner for a Senior Data Analyst case-study
interview at Apex / IDLC Asset Management. Read deliverables/interview_prep.md first —
it has my polished opening, the fact table, the coaching so far, and where we stopped.
Also read deliverables/apex_presentation.html (my slides + speaker notes) and README.md
for grounding. Treat me as a beginner being made ready for a senior role. This is a PREP
session, not a bug hunt — assume the analysis is final.

We were on STEP 2 (Section-by-Section Teach-Back), about to do Section 1 (Fund Performance).
Pick up exactly there. Run one question at a time, wait for my answer, then critique:
what worked, what to cut, and a crisp model answer. Session plan is in the prep file.
```

---

## SESSION PLAN (6 steps)

1. **Warm-up** — 60-second opening pitch, then critique. ✅ DONE (see polished opening below)
2. **Section teach-backs** — for each of 3 sections: finding → method → recommendation. ⬅️ WE ARE HERE (Section 1 next)
3. **Number drill** — quiz the fact table until instant recall.
4. **Mock panel Q&A** — rotating skeptics (non-technical Head of Distribution / data-savvy analyst / CIO). One question at a time, scored 1–5, model answer each time.
5. **Curveballs** — the hard ones (see list at bottom).
6. **Delivery coaching** — explain net flow, book multiple, churn in one plain sentence each; jargon flags; pacing for a ~10-min deck.

---

## ✅ MY POLISHED 60-SECOND OPENING (rehearse out loud 5–6×)

Three moves: (1) lead with the LEAK, not the AUM inventory; (2) prove it with "1 in 3";
(3) no hedging — no "so far", no "I wonder". Stay at altitude (the system), save per-fund
detail for the walkthrough. Short sentences.

> "Apex looks healthy on the surface — we manage ৳276 crore, over 8,000 customers, a book
> that's still growing. But underneath there's a leak: on average, one in three accounts we
> open, we lose. And the problems aren't separate — they feed each other. We pay RMs to sign
> customers up, not to keep them, so our biggest fund fills up with people who leave. Meanwhile
> most of our money sits with a small group of big customers nobody is really looking after —
> so the risk piles up at the wrong end. The upside: there's around ৳8 crore of sales we can
> get from customers we already have, with no new spending. Let me walk you through the funds,
> the customers, and the RMs — the through-line is simple: stop the leak, protect the top,
> and sell deeper into who we've got."

**Coaching notes on delivery:**
- Under pressure, grammar slips ("we has", "operates 276 crore"). Fix by shortening: "We manage ৳276 crore."
- Don't pose your open questions to the panel in the opening — it reads as you not knowing.
- Authenticity = knowing the story so well you can say it 5 different ways. Not a memorized script.

---

## 📊 CORE FACT TABLE (must be instant recall)

**Top line**
- ৳276.0 Cr AUM (book value, NOT market return) · ৳249.3 Cr cumulative net flow
- 12,229 accounts · 8,570 customers (key = mobile no.) · 16 RMs
- Net flow peaked ~৳60 Cr (2022–23); compressed to ৳28–38 Cr by 2024–25 as surrenders rose (~৳65 Cr)

**Churn**
- Strict (Closed + Discontinued) = 34.2% pooled / 33.6% avg-of-funds
- Broad (+ Inactive) = 43.4% (sensitivity only)
- Suspended (2 accounts) excluded from all denominators

**Per fund** (composite weights: churn 35 / book-multiple 30 / KM-survival 20 / persistency 15)

| Rank | Fund | Accounts | AUM | Book mult | 3yr surv | Persistency | Churn | Composite |
|---|---|---|---|---|---|---|---|---|
| #1 | Fixed Income | 3,221 | ৳98.4 Cr | 1.11× | 77.5% | 85.0% | 16.0% | 74.6 |
| #2 | Shariah Growth | 3,086 | ৳69.2 Cr | 2.09× | 52.5% | 74.9% (97.6%*) | 37.5% | 33.9 |
| #3 | Capital Growth | 3,779 | ৳74.9 Cr | 2.97× | 53.8% | 70.0% | 47.2% | 31.1 |
| #4 | Balanced Opportunity | 2,143 | ৳33.4 Cr | 0.78× | 65.8% | 72.9% | 33.7% | 28.8 |

*Shariah persistency is quoted two ways in materials (74.9% table / 97.6% speaker note) — reconcile which one you cite.
Balanced Opportunity is the ONLY fund below 1.0× book multiple (net decumulation).

**Customers**
- SIP persistency 75.2% overall (left-skewed: median ~96%)
- Top 10% customers hold 68% of AUM (857 customers · ৳205 Cr)
- 81.5% of customers single-fund
- Cross-sell ~৳8.02 Cr/yr ceiling = Play1 second-fund ৳5.10 + Play3 non-SIP→SIP ৳2.92.
  (Play2 high-value ৳1.62 is a SUBSET of Play1, NOT additive.)
  Realistic first-year at 25–30% take-up ≈ ৳2–3 Cr.

**Segments** (StandardScaler + k-means, k=4, silhouette 0.41)
- Young Core SIP: 5,350 (age 33, ৳42K bal, 11.4% multi-fund)
- Older Mass-Market: 2,296 (age 49)
- High-Value Multi-fund: 848 (age 40, ৳3.42L bal, 75.5% multi-fund)
- Ultra-Wealthy Whales: 41 (~৳96L each, 65.9% multi-fund)

**RMs**
- 1-yr retention: team avg 87.8% (all matured cohorts); brief's May-2024 cohort = 84.6% (115/136)
- Best: Sonia Sheikh 91.8% (296 accts). Watch: Mohammad Jasim Ahmed 83.4% (consistently below avg),
  Shibani Datta 86.3% (declining 92.0→90.5→85.0→79.6). Emerging watch: Most. Sumaya Siddique 74.5% (thin record).
- Biggest book: Shanta Sheikh 1,730 accts / ৳52.7 Cr but 41.0% churn.
- HHI ~0.27 (mild concentration) BUT top-two-fund share ~60–77%. Cite the right one — don't conflate.
- Volume×Value quadrant medians: 785 accounts, ৳18.7 Cr AUM.

**TWO CONCEPTUAL SPINES (memorize cold):**
1. **PERSISTENCY ≠ RETENTION** — pay installments on time yet still close the account.
2. **FLOW ≠ RETURN** — no NAV data exists; all figures are capital in/out, not investment performance.

---

## 🎯 CURVEBALLS TO PREPARE (Step 5 — we'll drill these)

- "There's an 'Investment Value (At Market)' column — so which fund invests best?"
  → point-in-time snapshot ≠ NAV time series; can't compute return without a series of dated NAVs.
- "How do you know the 2 flagged RMs are the problem and not the segment/fund they were handed?"
  → confounding / attribution — NOT controlled for. Honest answer + how you'd test it.
- "Composite weights are subjective — does the ranking survive different weights?"
  → sensitivity: Fixed Income #1 and Balanced #4 are robust; #2/#3 (Shariah/Capital) can swap.
- "Silhouette 0.41 is weak — how much do you trust the segments? Why not log-transform skewed AUM?"
- "Is a 41-person cluster statistically meaningful?"
- "Give me a realistic cross-sell number, not the ৳8 Cr ceiling." → ~৳2–3 Cr at 25–30% take-up.
- "You excluded Inactive from churn — what if they're really gone?" → broad = 43.4%.
- "The brief's closure-rate formula divides by Total ACTIVE; you divided by total accounts — why?"
- "If I fund only ONE recommendation, which and why?"
- "What would make you wrong? Which number are you least sure of?"

---

## COACHING LOG (running)

- **Step 1 (opening):** First attempt was list-like and tentative ("what I've learned so far",
  "I wonder if we have a strategy"). Fixed: lead with leak, prove with 1-in-3, cut hedges,
  stay at altitude. Final polished version above. Grammar tightens under pressure — use short sentences.
