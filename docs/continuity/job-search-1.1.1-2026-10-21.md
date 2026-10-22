# job-search 1.1.1 - 2026-10-21

Written as a separate file because another session had uncommitted edits to
`session-state.md` and `compaction-handoff.md` in the main checkout at the time.
Fold this into those docs at the next continuity pass.

## What landed

- `719c263` job-search 1.1.1: `expand_role_synonyms.py` no longer lists PMP, PgM
  (project manager) or CPA (accountant) as job titles; adds construction project
  manager and construction manager synonyms and adjacent roles; apostrophes are
  optional when matching ("Owners Representative"). `build_search_queries.py`
  accepts `--industry construction` (ConstructionJobs.com, iHireConstruction,
  AGC Construction Careers, CMAA CareerHQ). 18 new tests (15 failed before the
  fix); 13/13 mutants killed.
- `234dc12` docs: new `job-search/references/board-access-notes.md` (LinkedIn's
  logged-out view ignores the salary and remote filters; Indeed, Glassdoor and
  ZipRecruiter block fetches; SimplyHired posting pages load; public ATS feeds
  confirm pay). Construction listed among the Tier 2 industries in SKILL.md.
- Signal: a live construction-PM search (Benton Harbor, MI, $120k+).

## Verification

- Full CI command on 234dc12: 473 passed.
- Added lines all ASCII.
- Pushed as a fast-forward `b1d3431..234dc12` to GitHub main. Local main in
  `E:\Git\job-hunter-public` still sits on the other session's unpushed `070a49c`
  (built on b1d3431), so that session must rebase onto origin/main before pushing.
- Deployed: 312 files across 24 installs byte-checked at 234dc12; Q catalog
  re-shipped (775 zip entries byte-identical, 68 zips); post-deploy gate checks
  `problems: []`; installed `expand_role_synonyms.py "project manager"` returns
  only program manager / project coordinator in .claude, .agents and .hermes;
  `--industry construction` emits all 4 boards in each.
- Rollback archives: `E:\Git\job-hunter-installs-pre-234dc12.zip`,
  `E:\Git\job-hunter-q-catalog-pre-234dc12.zip` (plus the `-pre-070a49c` installs
  archive from the mis-deploy below).

## Lesson: deploy-src tracks the LOCAL repo

`E:\tmp\jh-gate114\deploy-src` is a clone whose `origin` is the local
`E:\Git\job-hunter-public`, not GitHub. `git checkout origin/main` there picks up
unpushed local commits. On 2026-10-21 the first deploy run installed `070a49c`
(another session's unpushed commit, which edits `job-hunter/SKILL.md`) to all
24 installs. Caught by the script's own "checked N files at <sha>" line and
corrected minutes later by re-deploying 234dc12 fetched straight from
`https://github.com/wexxwuther/job-hunter.git`. Always deploy a SHA fetched from
GitHub and confirm the "at <sha>" line before the Q re-ship.

## Not done

- `update-catalog.py` warns that the `job-hunter` and `social-media-plugin`
  catalog hashes are stale; not addressed here (pre-existing, outside this change).
