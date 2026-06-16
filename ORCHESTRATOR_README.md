# ORCHESTRATOR — Apex Case Study Run Guide

Hand this whole folder to Claude Code. This file tells the lead/orchestrator session
how to run the three agents and assemble deliverables.

## The model
Sequential phases with QA gates — NOT three agents in parallel (Agent 2 can't start
until Agent 1's tables exist; parallel agents would race on the same files).

```
You/Lead: finalize definitions.yaml + folder contract   (highest-leverage step)
        │
   Agent 1 (Data Engineering)  ──►  Agent 3 GATE 1  ──► fix loop until PASS
        │
   Agent 2 (Analysis: A→B→C→D) ──►  Agent 3 GATE 2  ──► fix loop until PASS
        │
   Lead: assemble notebook + 10-slide deck
```

## Setup before any agent runs
1. Create folders: raw/ clean/ analysis/ qa/ deliverables/
2. Put the 3 source files in raw/ (read-only).
3. Review `definitions.yaml` — especially the **Inactive/Suspended churn treatment**
   (default: strict churn = Closed+Discontinued; broad adds Inactive as sensitivity;
   Suspended excluded, only 2 rows). Change here if the business disagrees, then never
   change it again mid-run.

## Running in Claude Code
- Spawn each agent as a **subagent** given ONLY its `AGENT_N_BRIEF.md`, a fixed input
  folder, and a fixed output folder. Scoped prompts stop agents wandering into each
  other's job.
- Block on the QA gate between phases. Do not proceed on FAIL.
- All agents read `definitions.yaml`; all decisions append to `decisions_log.md`.

## After Gate 2 passes — Lead assembles deliverables

### Notebook (`deliverables/apex_analysis.ipynb`)
1. Executive summary & business framing (the leakage problem)
2. Data loading, profiling, quality report  (from Agent 1)
3. Data preparation: cleaning, joins, derived tables, metric definitions
4. Section 1 — Fund performance + recommendations
5. Section 2 — Acquisition, segmentation, cross-sell + recommendations
6. Section 3 — RM productivity + recommendations
7. Cross-cutting synthesis
8. Consolidated recommendations + appendix (assumptions, limitations, derived-field dictionary)

### Deck (`deliverables/apex_deck.pptx`, max 10 slides)
1. Title & context
2. Executive summary — leakage in one chart
3. Methodology & data overview (+ key assumptions)
4. Fund ranking & scorecard
5. Fund deep-dive: leakage / cohorts / SIP persistency
6. Customer segments & targeting map
7. Cross-sell opportunity (sized in Taka)
8. RM performance quadrant & scorecard
9. Team trend & systemic findings
10. Prioritized recommendations & roadmap

## Success criteria (from the case rubric)
- Analytical depth: cohorts, persistency, clustering, RM acquisition-quality — beyond the 4 given formulas
- Business insight: every number → a specific, owner-assigned action
- Communication: coherent story for non-technical leadership; flow-not-return caveat stated

## Submission deadline: June 20, 2026
```
