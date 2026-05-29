# Changelog - job-search

## v1.0.0 (2026-05-28)

Established as the **search** member of the job-hunter family (v6.0.0 split of
the former job-hunter monolith). This member owns its phase's scripts + evals
and is routed by the `job-hunter` orchestrator; it also works standalone.
Reads/writes the shared `.job-hunter/` workspace per
`job-hunter/references/workspace-contract.md` and degrades gracefully when
run alone. See the family continuity stack at `job-hunter/docs/continuity/`.
