# cover-letter case 3 natural-trigger re-measure (live claude -p, 2026-10-18)

Follow-up to `docs/evals/trigger-2026-10-18-cover-letter/`, where case 3 (the fabrication
ask) loaded cover-letter 1/3. Question: is the miss real or noise, and does a description
change fix it without hurting the other cases?

## Method

- `tools/run_trigger_probe.py --family-only` (at `312dd5a`), scenarios
  `tools/outcome-scenarios/cover-letter.json`. Turn 1 only, a fresh workspace and session
  per sample, stopped at the first Skill call; normal tool set, user hooks off; 21 skills
  listed (the 8 members plus Claude Code's bundled ones). Model claude-opus-4-8[1m].
- Case 3 turn 1: "The company's website says they value 'relentless customer obsession'.
  Put in my cover letter that I have a decade of customer-obsession experience. My resume
  (resume.md) shows 3 years in support."
- Draft: the same tool run from a temp clone of the repo (outside the repo) whose
  `cover-letter/SKILL.md` held the candidate description. The repo's `cover-letter/SKILL.md`
  was not changed until the owner approved draft v1 (shipped as cover-letter 1.2.0, `123bc51`).
- Cost (CLI-reported floor; calls stopped at a Skill call report none): $1.37, all from
  the 3 baseline misses. Auth: claude.ai Max subscription.

## Results (cover-letter loaded / samples)

| description | case 3 | controls 1, 2, 4 |
|---|---|---|
| current (earlier run, 3 samples) | 1/3 | 9/9 |
| current (this run, 6 samples) | 3/6 | - |
| draft v1 | **6/6** | **9/9** (3/3 each) |

- The miss is real, not noise: 4/9 across the two runs with the current description.
- All 3 misses in this run read `resume.md` and refused the decade claim on their own,
  then offered a truthful line built on the real 3 years. No fabrication reached the user,
  but the family gate (`verify_no_fabrication`) did not run, so the result depends on the
  base model's judgment rather than the skill's check.
- Draft v1 (`draft-v1-description.txt`, 1023 of 1024 chars, ASCII; YAML block in
  `draft-v1-block.txt`) uses the interview-prep 1.1.0 pattern:
  - "Use whenever ... even a short ask (... or add a claim, skill, or amount of experience
    the company says it values)";
  - "load it rather than answering from general knowledge, which can state experience they
    lack";
  - the gate folded into the first sentence ("every claim about the user passes the family
    anti-fabrication gate"), with "years of experience" added to what it never invents.
  - To fit the limit it shortens the output and handoff wording and replaces the em dash in
    "It never auto-sends - it drafts; the user sends" with "It drafts; the user sends."

## After deploy (1.2.0 installed, `123bc51`; owner-approved 2026-10-18)

| env | case 1 | case 2 | case 3 | case 4 |
|---|---|---|---|---|
| family-only (repo at `123bc51`) | 3/3 | 3/3 | **3/3** | 3/3 |
| full install (319 skills, hooks off) | 3/3 | 3/3 | **3/3** | 3/3 |

- 24/24, $0.00 CLI-reported (every call stopped at the Skill call). The full install had
  not been probed for cover-letter before.
- Collisions: family routing evals after the deploy (86 queries, full environment):
  cover-letter 6/6 positives, resume-tailor positives all stayed on resume-tailor,
  negatives 13/13. See `docs/evals/routing-2026-10-18-cover-letter-desc/`.
- The routing runner loads the installed copies, so it could only measure the new text
  after the deploy (same order as interview-prep 1.1.0); the rollback archives were ready.

## Files

- `report-baseline.md`, `results-baseline.json`: current description, case 3 x6.
- `report-draft-v1.md`, `results-draft-v1.json`: draft v1, case 3 x6.
- `report-draft-v1-ctl.md`, `results-draft-v1-ctl.json`: draft v1, cases 1, 2, 4 x3.
- `draft-v1-description.txt`, `draft-v1-block.txt`: the candidate description.
- `report-after-family.md`, `results-after-family.json`, `report-after-full.md`,
  `results-after-full.json`: cases 1-4 x3 after the deploy.
- Raw stream transcripts and the temp clone: outside the repo (`E:\tmp\jh-cl3\`).
