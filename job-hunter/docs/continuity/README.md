# Continuity Docs - job-hunter family (orchestrator-owned shared stack)

This is the **single shared continuity stack for the whole job-hunter family** (the
orchestrator `job-hunter/` plus the five members: `career-profile/`, `job-search/`,
`resume-tailor/`, `application-tracker/`, `outcome-learning/`). The members are
co-developed, so they share ONE continuity stack rather than carrying 6x duplication.
Each member has a one-line stub at `<member>/docs/continuity/README.md` that points back
here.

Read these files at the start of a new session before changing behavior, scripts, evals,
routing, the workspace contract, or public docs. Update only the files touched by the work;
keep entries short, dated, and evidence linked.

Reload order: `session-state.md`, `compaction-handoff.md`, `reload-protocol.md`,
`decisions.md`, `rejected-ideas.md`, `lessons.md`, `memory.md`, `discovery-log.md`,
`open-questions.md`, `maintenance.md`.

Rules:

- Keep entries source-backed and dated.
- Update `compaction-handoff.md` before handoff or compaction.
- Promote durable notes into the specific continuity file.
- Promote chain-wide truths (apply to >1 skill) to `_designs/CHAIN_LESSONS.md` in addition
  to the family-local `lessons.md`.
- Do not store secrets, credentials, private user data, or raw transcripts here.
