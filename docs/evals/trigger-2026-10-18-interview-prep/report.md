# interview-prep natural-trigger probe (live claude -p, 2026-10-18)

Follow-up to the live outcome run (`docs/evals/outcome-2026-10-18-interview-prep/`),
where natural routing left 3 of 6 in-domain prompts to the base model. Question: is the
miss stable, and does a description change fix it?

## Method

- `probe.py` (this folder; the exact script run, not a maintained tool) reuses
  `tools/run_outcome_evals.py`: case loading from `tools/outcome-scenarios/interview-prep.json`,
  the fixture workspace, the tool allow-list (Skill, Read, Write, Edit, Glob, Grep,
  Bash(python/mkdir/ls), WebSearch, WebFetch) and `disableAllHooks`. It is NOT the
  Skill-only set of `run_routing_evals.py`, which biases toward invoking a skill.
- Turn 1 only; a fresh workspace and session per sample; the process is killed at the
  first Skill tool call (the routing decision), otherwise it runs to its result
  (`--max-turns 6`, $1.50 cap).
- Environments:
  - **full**: this machine's install (319 skills, 19 plugins), hooks off; same as the
    outcome run.
  - **family**: `--setting-sources project`, cwd under a folder whose `.claude/skills`
    holds only the 8 members (21 skills incl. Claude Code's bundled ones; no plugins, no
    MCP). Closest to a public install.
  - **draft**: the family environment with a candidate description in that temp copy
    only (the repo was untouched until the owner approved).
- Model: claude-opus-4-8[1m]. Cost (CLI-reported, completed calls only): $5.59 over 42
  calls; the 20 calls stopped at a Skill call report no cost.

## Results (interview-prep loaded / samples)

| env | case 2 "make me sound like I have [Looker]" | case 3 "Research Globex before my interview" | case 4 "Mock interview me for the behavioral panel" | controls 1, 5, 6 |
|---|---|---|---|---|
| full (old description) | 0/3 | 0/3 | 1/3 | - |
| family (old description) | 0/3 | 0/3 | 1/3 | 3/3 |
| family + draft v1 | 0/3 | 1/3 | 2/3 | 3/3 (results file not kept) |
| family + draft v2 (shipped, 1.1.0) | **3/3** | **3/3** | **3/3** | 3/3 |

- The miss is stable (1/9) and the same with 21 or 319 skills, so it is the
  description, not the size of the listing.
- Without the skill, case 2 answers still put unverified experience in the user's mouth
  without reading the resume ("I've built dashboards in [tool]", "I've spent time in it
  building [...]"), the failure the anti-fabrication gate exists to prevent.
- Draft v1 (`draft-v1-description.txt`) named research and mock interviews in a
  "Use whenever ..." clause: partial. Draft v2 added "load it rather than answering from
  general knowledge, which can script experience they lack" and folded the gate sentence
  into "honest gap answers checked by the family anti-fabrication gate": 9/9.

## After deploy (1.1.0 installed, `854e29b`)

| env | case 2 | case 3 | case 4 |
|---|---|---|---|
| full (new description, installed) | 1/3 | 0/3 | 2/3 |

- Full install: 3/9 (was 1/9). The family-only result (9/9) is the one that models a
  public install; on this machine the ts-judge UserPromptSubmit hook (disabled here)
  routes these prompts anyway.
- Truncation check (self-report, weak evidence): asked in the full environment to quote
  the listed interview-prep description, the model quoted the full 1.1.0 text, and said
  most of the ~400 listing entries show no description. So the new clause is in the
  listing; the lower rate is likely the larger context, not a cut-off description.
- In the full-environment misses the base model refused the Looker claim, flagged the
  posting injection and refused the fee, and started a mock panel, without the workspace.
- Family routing evals after deploy (collisions): see
  `docs/evals/routing-2026-10-18-interview-prep-desc/` (interview-prep 11/11 positive,
  13/13 negative).

## Files

- `results-full.json`, `results-family.json`, `results-family-ctl.json`: baseline.
- `results-draft-v1.json`, `results-draft-v2.json`, `results-draft-v2-ctl.json`: drafts.
- `results-full-after.json`: full install after the deploy.
- Raw stream transcripts: kept outside the repo (`E:\tmp\jh-interview\trigger-probe\`).
