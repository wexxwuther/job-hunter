# job-search case 6 natural-trigger re-measure (live claude -p, 2026-10-18)

Follow-up to `docs/evals/trigger-2026-10-18-job-search/`, where case 6 loaded job-search 2/3.
Same method as `docs/evals/trigger-2026-10-18-cover-letter-case3/`.

## Method

- `tools/run_trigger_probe.py --family-only` (repo at `ca6b381`), scenarios
  `tools/outcome-scenarios/job-search.json`. Turn 1 only, fresh workspace and session per
  sample, stopped at the first Skill call; normal tool set, user hooks off; 21 skills listed.
  Model claude-opus-4-8[1m]. Auth: claude.ai Max subscription.
- Case 6 turn 1: a LinkedIn posting with no apply button, no salary (NYC role), "Confidential
  Fortune 500", same JD posted three times in 60 days. "Should I tailor my resume for it?"
- Draft: the same tool run from a temp clone outside the repo (`E:\tmp\jh-2of3\draft-repo`)
  that held this draft plus the career-profile and outcome-learning drafts. The repo's
  `job-search/SKILL.md` was NOT changed (owner approval needed).

## Results (job-search loaded / samples)

| description | case 6 | controls 1-5, 7, 8 |
|---|---|---|
| current (earlier run, 3 samples) | 2/3 | 18/21 strict (case 2 "Find me a job" -> job-hunter 3/3) |
| current (this run, 6 samples) | 5/6 | - |
| draft v1 (proposed) | **6/6** | 17/21 strict; see below |

- Real but the weakest of the three: 7/9 across both runs with the current description. If
  the true rate were 95%, a result this low would happen about 7% of the time.
- What the misses did: answered from general knowledge with a sound ghost-job read (NYC pay
  transparency, "Confidential" employer, reposted JD) and advised against tailoring. No
  `score_posting`, so no `posting_legitimacy` sub-score and nothing written to the workspace.
- Draft controls: case 2 went to job-hunter 3/3 as before (its own open question). Case 1
  ("Find me ... roles ... Here's my resume") was 2/3 then 5/6 (7/9) with the career-profile
  draft v1 in the clone: 2 samples loaded career-profile. With career-profile draft v2 it was
  5/6 with 1 job-hunter and 0 career-profile (current: 9/9). All other controls 3/3.
  Details: `docs/evals/trigger-2026-10-18-2of3-xcheck/report.md`.
- Draft v1 (`draft-v1-description.txt`, 1023 of 1024 chars, ASCII; YAML block in
  `draft-v1-block.txt`) adds "or judge whether one posting is real or worth applying or
  tailoring for, even a short ask; load it rather than judging a posting from general
  knowledge, which skips the legitimacy score". To fit it shortens the source list ("niche
  boards", "local sources", "company career pages"). The resume-tailor negative stays.

## Files

- `report-baseline.md`, `results-baseline.json`: current description, case 6 x6.
- `report-draft-v1.md`, `results-draft-v1.json`: draft v1, case 6 x6.
- `report-draft-v1-ctl.md`, `results-draft-v1-ctl.json`: draft v1, cases 1-5, 7, 8 x3.
- `draft-v1-description.txt`, `draft-v1-block.txt`: the candidate description.
- Raw stream transcripts and the temp clone: outside the repo (`E:\tmp\jh-2of3\`).
