# Cross-member collision check for the three 2/3 drafts (live claude -p, 2026-10-18)

Drafts under test: career-profile (v1, then v2), job-search v1, outcome-learning v1, all in
one temp clone outside the repo (`E:\tmp\jh-2of3\draft-repo`, base `ca6b381`). "current" =
the repo as committed (no draft). `tools/run_trigger_probe.py --family-only`, turn 1 only,
21 skills listed, model claude-opus-4-8[1m], user hooks off. Earlier = the family-only
3-sample runs in `docs/evals/trigger-2026-10-18-<member>/`.

## Expected skill loaded / samples

| case | earlier | current (this session) | drafts with career-profile v1 | drafts with career-profile v2 |
|---|---|---|---|---|
| job-search 1 (find roles + "Here's my resume") | 3/3 | 6/6 | 7/9 (career-profile 2) | 5/6 (job-hunter 1) |
| job-hunter 2 (find jobs + tailor top match) | 3/3 | 6/6 | 2/3 (job-search 1) | 6/6 |
| job-hunter 1, 3, 5 | 0/9 (member direct) | - | 0/9 (same members) | - |
| job-hunter 4 | 3/3 | - | 3/3 | - |
| resume-tailor 1-4, 6 | 15/15 | - | 15/15 | 12/12 (1, 2, 3, 6) |
| resume-tailor 5 (cover-letter ask) | 0/3 (cover-letter) | - | 0/3 (cover-letter) | - |
| cover-letter 1-4 | 3/3, 3/3, 1/3, 3/3 (pre-1.2.0) | - | 12/12 | 6/6 (1, 4) |
| application-tracker 1-3 | 9/9 | - | 9/9 | - |
| interview-prep 1, 3-6 | 1.1.0 family: 3/3 each | - | 15/15 | - |
| interview-prep 2 (Looker, "make me sound like I have") | 1.1.0 draft v2: 3/3 | **0/6** | 0/3 | 1/6 |

- The only collision caused by a draft was career-profile v1 on job-search case 1; v2 removes
  it (0 of 6 career-profile). The one v2 job-hunter load is still family-routed (the
  orchestrator routes search to job-search).
- job-hunter case 2's 2/3 under v1 was noise: 6/6 under both current and v2.
- interview-prep case 2 is a separate finding, not caused by these drafts: 0/6 on the
  current committed descriptions (1.1.0 measured 3/3 family-only before it shipped). Every
  miss answered with no tool call and refused to script fake Looker experience, so nothing
  fabricated reached the user, but the family gate did not run. Logged in
  `docs/continuity/open-questions.md`.

## Cost

CLI-reported floor for the whole re-measure (219 calls; calls stopped at a Skill call
report none): $5.73. Baselines about $2.70, interview-prep case 2 misses about $3.02, everything
else $0.00. Auth: claude.ai Max subscription.

## Files

`report-<run>.md` / `results-<run>.json` for each run in the table: `v1-<member>` (all cases
x3, or `v1-job-search-case1` x6), `v2-*`, `current-*`.
