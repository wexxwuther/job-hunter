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
  was NOT changed: a description change needs owner approval.
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

## Not measured here

- Collisions: no routing run on the draft. Its new "change a cover letter" and "add a
  claim, skill, or amount of experience" wording could pull resume edits or other members'
  prompts. After owner approval, run the family routing evals (positives and negatives) as
  was done for interview-prep (`docs/evals/routing-2026-10-18-interview-prep-desc/`) before
  deploying.
- The full-install environment (this machine's ~319 skills) was not probed.

## Files

- `report-baseline.md`, `results-baseline.json`: current description, case 3 x6.
- `report-draft-v1.md`, `results-draft-v1.json`: draft v1, case 3 x6.
- `report-draft-v1-ctl.md`, `results-draft-v1-ctl.json`: draft v1, cases 1, 2, 4 x3.
- `draft-v1-description.txt`, `draft-v1-block.txt`: the candidate description.
- Raw stream transcripts and the temp clone: outside the repo (`E:\tmp\jh-cl3\`).
