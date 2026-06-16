# KICKOFF PROMPT — paste this into Claude Code at the repo root

You are the Lead/Orchestrator for the Apex Asset Management case study. The repo is
already set up. Read these first, in order:
1. ORCHESTRATOR_README.md   (the run model + final deliverable structure)
2. definitions.yaml         (single source of truth — never override it in code)
3. decisions_log.md         (locked decisions; the churn rule is already settled)

## Operating rules
- Run SEQUENTIAL phases with QA gates. Never run agents in parallel — Agent 2 depends
  on Agent 1's clean tables.
- Spawn each agent as a scoped subagent given ONLY its brief + fixed input/output folders:
    Agent 1 -> AGENT_1_BRIEF.md  (reads raw/, writes clean/)
    Agent 2 -> AGENT_2_BRIEF.md  (reads clean/, writes analysis/)
    Agent 3 -> AGENT_3_BRIEF.md  (validation gate; reads the phase output, writes qa/)
- Every agent reads definitions.yaml. Every judgment call appends to decisions_log.md.
- BLOCK on each gate. On FAIL, run the fix loop and re-gate before proceeding.

## Sequence to execute
1. Phase 1: run Agent 1. Then run Agent 3 GATE 1. Loop until `GATE 1: PASS`.
2. Phase 2: run Agent 2 (stages A->B->C->D). Then run Agent 3 GATE 2. Loop until `GATE 2: PASS`.
3. Phase 3 (Lead): assemble deliverables/
     - apex_analysis.ipynb  (8-section structure in ORCHESTRATOR_README)
     - apex_deck.pptx        (max 10 slides, structure in ORCHESTRATOR_README)
   Use the pptx and ipynb skills. Every figure must trace to an analysis/ table.

## Environment notes (Windows)
- Environment is bootstrapped by `run.ps1` (PowerShell). The venv lives at
  `.venv\Scripts\python.exe`. Use THAT interpreter for all code execution.
- Libs already installed: pandas, numpy, openpyxl, scikit-learn, matplotlib,
  python-pptx, pyarrow, lifelines (survival), kmodes (k-prototypes), pyyaml.
- Use Windows-style relative paths under the repo root; keep everything inside the repo.
- Reproducibility: use random_seed from definitions.yaml everywhere it matters.

## Success bar (case rubric — keep checking against it)
- Analytical depth beyond the 4 given formulas: cohorts, SIP persistency, clustering,
  per-RM acquisition-quality.
- Every number ends in a specific, owner-assigned recommendation.
- Coherent business story for non-technical leadership.
- State the "no NAV / flow-not-return" caveat in Section 1.

Begin with Phase 1, Agent 1. Report back after GATE 1 before continuing.
