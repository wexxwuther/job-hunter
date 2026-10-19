# outcome-learning case 3 natural-trigger re-measure (live claude -p, 2026-10-18)

Follow-up to `docs/evals/trigger-2026-10-18-outcome-learning/`, where case 3 loaded
outcome-learning 2/3. Same method as `docs/evals/trigger-2026-10-18-cover-letter-case3/`.

## Method

- `tools/run_trigger_probe.py --family-only` (repo at `ca6b381`), scenarios
  `tools/outcome-scenarios/outcome-learning.json`. Turn 1 only, fresh workspace and session
  per sample, stopped at the first Skill call; normal tool set, user hooks off; 21 skills
  listed. Model claude-opus-4-8[1m]. Auth: claude.ai Max subscription.
- Case 3 turn 1: "Summarize what you'd tell job-search to do differently for me." (fixture:
  9 closed outcomes, 1 confirmed lesson).
- Draft: the same tool run from a temp clone outside the repo (`E:\tmp\jh-2of3\draft-repo`)
  that held this draft plus the career-profile and job-search drafts. The repo's
  `outcome-learning/SKILL.md` was NOT changed (owner approval needed).

## Results (outcome-learning loaded / samples)

| description | case 3 | controls 1, 2, 4, 5 |
|---|---|---|
| current (earlier run, 3 samples) | 2/3 | 12/12 |
| current (this run, 6 samples) | 3/6 | - |
| draft v1 (proposed) | **6/6** | **12/12** (3/3 each) |

- Real miss, the clearest of the three: 5/9 across both runs with the current description.
- What the misses did: listed the workspace, read the four learning-loop files themselves,
  and answered with concrete scoring advice for job-search (for example "penalize large
  companies hard") grounded in the confirmed lesson and the outcomes. No `harvest_outcomes.py`
  or `propose_lessons.py`, so the 5-closed-outcome cold-start guard and the opt-in confirm
  step did not run; the advice went past the one confirmed lesson.
- Draft v1 (`draft-v1-description.txt`, 1014 of 1024 chars, ASCII; YAML block in
  `draft-v1-block.txt`) adds "or what another member (job-search, resume-tailor) should do
  differently for them" and "even a short ask; load it rather than reading those files and
  answering yourself, which skips the 5-closed-outcome cold-start guard and the opt-in
  confirmation step (it never auto-writes)". It replaces the current description's em dash
  with a colon (ASCII rule) and, to fit, drops "surface patterns across closed-loop
  outcomes" and the "Reads ... translates signals into suggested lessons" sentence.
- Collisions on other members: none attributable (see
  `docs/evals/trigger-2026-10-18-2of3-xcheck/report.md`; job-hunter case 5 "Learn from my
  outcomes" still loads outcome-learning 3/3, as before).

## Files

- `report-baseline.md`, `results-baseline.json`: current description, case 3 x6.
- `report-draft-v1.md`, `results-draft-v1.json`: draft v1, case 3 x6.
- `report-draft-v1-ctl.md`, `results-draft-v1-ctl.json`: draft v1, cases 1, 2, 4, 5 x3.
- `draft-v1-description.txt`, `draft-v1-block.txt`: the candidate description.
- Raw stream transcripts and the temp clone: outside the repo (`E:\tmp\jh-2of3\`).
