# Changelog - job-search

## v1.1.1 (2026-10-21)

Signal: a construction project manager's live search (Benton Harbor, MI, $120k+).
`expand_role_synonyms.py "project manager"` returned PMP (a certification, so the queries
searched for the credential) and PgM (rarely used in postings); there was no entry for
construction project-management titles; `--industry construction` was not recognized, so
Tier 2 fell back to one generic "job board" query.

- `scripts/expand_role_synonyms.py`: removed PMP and PgM from "project manager" and CPA from
  "accountant" (credentials, not titles; the rule is now a comment and a test). Added
  "construction project manager" and "construction manager" synonyms plus adjacent roles for
  construction project manager, using titles seen in live postings on 2026-10-21. Lookup now
  treats typographic and missing apostrophes alike ("Owners Representative").
- `scripts/build_search_queries.py`: new `construction` industry: ConstructionJobs.com,
  iHireConstruction, AGC Construction Careers (careers.agc.org), CMAA CareerHQ
  (careerhq.cmaanet.org), each domain checked live 2026-10-21. `trades` is unchanged.
- `references/niche-boards-by-industry.md`: new Construction / Construction Management table.
- New `references/board-access-notes.md`, linked from SKILL.md: LinkedIn's logged-out search
  ignoring the salary and remote filters, which aggregators block automated fetches, public
  ATS feeds (Workday cxs, Greenhouse, Lever, Ashby) for confirming a posting and its pay, and
  labeling aggregator-only pay with its source.
- Tests: `tests/test_expand_role_synonyms.py` and `tests/test_build_search_queries.py`, 18 new
  (15 failed before the fix); 13/13 mutants killed. No description change.

## v1.1.0 (2026-10-20)

- Description only (owner-approved 2026-10-20). Signal: a possible ghost-job posting (no apply button, no salary) loaded job-search 7/9 in a family-only install; misses answered without the legitimacy score. Draft v1: case 6 6/6; joint sweep 3/3 (+3/3). Evidence: docs/evals/trigger-2026-10-18-job-search-case6/.
- Joint family-only sweep with all four 2026-10-20 description changes applied together: all 40 outcome-eval turn-1 cases x3 match the earlier per-member probes except job-search case 1 (7/9, the 2 misses routed to the job-hunter orchestrator; 9/9 before).

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
