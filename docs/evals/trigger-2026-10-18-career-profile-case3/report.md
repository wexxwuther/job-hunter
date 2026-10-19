# career-profile case 3 natural-trigger re-measure (live claude -p, 2026-10-18)

Follow-up to `docs/evals/trigger-2026-10-18-career-profile/`, where case 3 loaded
career-profile 2/3. Same method as `docs/evals/trigger-2026-10-18-cover-letter-case3/`.

## Method

- `tools/run_trigger_probe.py --family-only` (repo at `ca6b381`), scenarios
  `tools/outcome-scenarios/career-profile.json`. Turn 1 only, fresh workspace and session per
  sample, stopped at the first Skill call; normal tool set, user hooks off; 21 skills listed.
  Model claude-opus-4-8[1m]. Auth: claude.ai Max subscription.
- Case 3 turn 1: "Here's my resume (resume.md). Read it and pull out the key facts so we can
  use it later."
- Drafts: the same tool run from a temp clone outside the repo (`E:\tmp\jh-2of3\draft-repo`)
  whose `career-profile/SKILL.md` held the candidate text. The clone also held the
  job-search and outcome-learning drafts (see those folders). The repo's
  `career-profile/SKILL.md` was NOT changed (owner approval needed).

## Results (career-profile loaded / samples)

| description | case 3 | cases 1, 2 (strict) | cases 1, 2 routed to job-hunter |
|---|---|---|---|
| current (earlier run, 3 samples) | 2/3 | 1/6 | 5/6 |
| current (this run, 6 samples) | 4/6 | - | - |
| draft v1 | 6/6 | 0/6 | 6/6 |
| draft v2 (proposed) | **6/6** | 0/6 | 6/6 |

- Real miss, not noise: 6/9 across both runs with the current description.
- What the misses did: read `resume.md` and summarised it accurately in chat; no
  `.job-hunter-profile.md`, no parsed-resume text, `parse_resume.py` not used. One miss
  offered to run career-profile afterwards. No fabrication; the cost is lost state for later
  steps.
- Cases 1 and 2 name "job-hunter" in the prompt and load the orchestrator, which routes
  profile setup here. That is the existing open question on eval expectations, unchanged by
  either draft.
- Draft v1 ("whenever they share a resume file ... to read, parse, or pull key facts from for
  later use") collided: job-search case 1 ("Find me ... roles ... Here's my resume") loaded
  career-profile in 2 of 9 samples (current description: 9/9 job-search). Draft v2 narrows it
  to "shares a resume file ... only to have it read, parsed, or summarized into key facts for
  later": job-search case 1 then 5/6 job-search, 1/6 job-hunter, 0/6 career-profile.
  Details: `docs/evals/trigger-2026-10-18-2of3-xcheck/report.md`.
- Draft v2 (`draft-v2-description.txt`, 1014 of 1024 chars, ASCII; YAML block in
  `draft-v2-block.txt`) uses the cover-letter 1.2.0 pattern ("Use whenever ... even a short
  ask; load it rather than summarizing the file yourself, which saves no profile for later
  steps"). To fit it shortens the North-Star list and drops "capture who they are beyond
  their resume" ("tell the assistant about themselves" stays) and "from a previous session".

## Files

- `report-baseline.md`, `results-baseline.json`: current description, case 3 x6.
- `report-draft-v1.md`, `results-draft-v1.json`, `report-draft-v1-ctl.md`,
  `results-draft-v1-ctl.json`: draft v1, case 3 x6 and cases 1, 2 x3.
- `report-draft-v2.md`, `results-draft-v2.json`, `report-draft-v2-ctl.md`,
  `results-draft-v2-ctl.json`: draft v2, same.
- `draft-v1-description.txt`, `draft-v1-block.txt` (superseded), `draft-v2-description.txt`,
  `draft-v2-block.txt` (proposed).
- Raw stream transcripts and the temp clone: outside the repo (`E:\tmp\jh-2of3\`).
