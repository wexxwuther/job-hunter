# Changelog - outcome-learning

## v1.1.0 (2026-10-20)

- Description only (owner-approved 2026-10-20). Signal: "Summarize what you'd tell job-search to do differently for me" loaded outcome-learning 5/9 in a family-only install; misses skipped the cold-start guard and the confirm step. Draft v1: case 3 6/6, other cases 12/12; joint sweep 15/15 (+3/3). Evidence: docs/evals/trigger-2026-10-18-outcome-learning-case3/.
- Joint family-only sweep with all four 2026-10-20 description changes applied together: all 40 outcome-eval turn-1 cases x3 match the earlier per-member probes except job-search case 1 (7/9, the 2 misses routed to the job-hunter orchestrator; 9/9 before).

## v1.0.0 (2026-05-28)

Established as the **learning-loop** member of the job-hunter family (v6.0.0 split of
the former job-hunter monolith). This member owns its phase's scripts + evals
and is routed by the `job-hunter` orchestrator; it also works standalone.
Reads/writes the shared `.job-hunter/` workspace per
`job-hunter/references/workspace-contract.md` and degrades gracefully when
run alone. See the family continuity stack at `job-hunter/docs/continuity/`.
