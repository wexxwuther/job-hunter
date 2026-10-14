# Changelog - job-search

## v1.0.1 (2026-10-13)

State workforce portal registry re-verified (all 51 entries, 2026-10-13):

- 13 entries replaced: 7 domains no longer resolve (AL, KY, LA, MA, NJ, NY, OR), Georgia's
  employgeorgia.com now serves an online-poker site, MT/OK/PA portals failed or were retired,
  NH pointed at a non-job-board page, RI pointed at the agency homepage instead of EmployRI.
- 7 entries moved to the .gov host they already redirect to (CO, IA, MN, NM, NV, WY, NC www).
- `scripts/build_search_queries.py` STATE_PORTALS used 5 of the dead domains (NY, MA, PA, GA,
  OR); now matches the table. Guarded by `tools/test_state_portals.py`.

## v1.0.0 (2026-05-28)

Established as the **search** member of the job-hunter family (v6.0.0 split of
the former job-hunter monolith). This member owns its phase's scripts + evals
and is routed by the `job-hunter` orchestrator; it also works standalone.
Reads/writes the shared `.job-hunter/` workspace per
`job-hunter/references/workspace-contract.md` and degrades gracefully when
run alone. See the family continuity stack at `job-hunter/docs/continuity/`.
