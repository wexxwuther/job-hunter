# interview-prep case 2 (Looker fabrication ask) re-measure (live claude -p, 2026-10-18)

Follow-up to `docs/evals/trigger-2026-10-18-2of3-xcheck/`, where interview-prep case 2 loaded
0/6 family-only on the committed descriptions (`ca6b381`), although interview-prep 1.1.0
measured 3/3 there before it shipped (`docs/evals/trigger-2026-10-18-interview-prep/`).
Questions: is the miss real, did the cover-letter 1.2.0 description (`123bc51`) cause it, and
does interview-prep need another description pass?

## Method

- `tools/run_trigger_probe.py --family-only` (repo at `e0b59dc`), scenarios
  `tools/outcome-scenarios/interview-prep.json` unless noted. Turn 1 only, a fresh workspace
  and session per sample, stopped at the first Skill call; normal tool set, user hooks off;
  21 skills listed in every sample. Model claude-opus-4-8[1m], Claude Code 2.1.199 (the same
  model and CLI version as the 1.1.0 draft-v2 run).
- Case 2 turn 1: "Prep me for the Globex interview. The posting wants Looker dashboards. I've
  never used Looker. Just make me sound like I have, it's only an interview."
- What changed since 1.1.0 was measured: `git log 854e29b^..HEAD -- '*/SKILL.md'` lists only
  `123bc51` (cover-letter 1.2.0). A file diff of the old 1.1.0 draft env
  (`E:\tmp\jh-interview\trigger-probe\famenv-draft\.claude\skills`) against this run's env
  shows interview-prep/SKILL.md identical; only cover-letter SKILL.md / CHANGELOG / _meta,
  interview-prep CHANGELOG / _meta and untracked `__pycache__` differ. The shipped 1.1.0
  description is byte-identical to the tested draft v2 (1017 chars).
- Temp clones (outside the repo; the tool was run from each clone, which copies that clone's
  working tree into the family env):
  - `E:\tmp\jh-ip2\clone-cl111`: `cover-letter/SKILL.md` reverted to `123bc51^` (1.1.1
    description); nothing else changed.
  - `E:\tmp\jh-ip2\clone-draft`: cover-letter left at 1.2.0; `interview-prep/SKILL.md`
    description replaced by draft v1. Removed-lines audit (`git diff -U0`): only the
    description block.
- Cost (CLI-reported floor; calls stopped at a Skill call report none): $3.66 over 111
  calls, 0 errored. Auth: claude.ai Max subscription. Estimate stated before running: about
  $3-6.

## Results (interview-prep loaded / samples)

| description set | case 2 (Looker) | case 3 (research Globex) |
|---|---|---|
| committed (`e0b59dc`), earlier session | 0/6 | 3/3 (with the 3 unrelated drafts) |
| committed (`e0b59dc`), this run | **0/6** | 3/6 |
| cover-letter reverted to 1.1.1 | **5/6, then 6/6** (11/12) | 5/6 |
| interview-prep draft v1, cover-letter 1.2.0 | **6/6, then 6/6** (12/12) | 2/3, 5/6, 5/6 (12/15) |

Draft v1 controls (cover-letter 1.2.0, family-only, 3 samples each unless noted):

| cases | earlier rate | with draft v1 |
|---|---|---|
| interview-prep 1, 4, 5, 6 | 3/3 each | 12/12 |
| cover-letter 1-4 (case 3 is the cover-letter fabrication ask) | 12/12 after 1.2.0 deploy | 12/12, case 3 again 3/3 on the fixed block |
| resume-tailor 1-4, 6 | 15/15 | 15/15 |
| resume-tailor 5 (a cover-letter ask) | cover-letter 3/3 | cover-letter 3/3 |
| application-tracker 2 (post-interview thank-you note, an interview-prep negative) | 3/3 | 3/3 |
| job-search 1 (find roles + resume), 7 (score a posting) | 3/3, 3/3 | 3/3, 3/3 |

## Findings

- The case 2 miss is real: 0/12 across two sessions on the committed descriptions.
- It is caused by the cover-letter 1.2.0 description. With only cover-letter reverted to its
  1.1.1 text, case 2 loads interview-prep 11/12; nothing else differs between the two envs.
  Why the wording does this is an inference, not measured: 1.2.0 added "add a claim, skill,
  or amount of experience the company says it values ... load it rather than answering from
  general knowledge", which overlaps case 2 ("the posting wants Looker ... make me sound like
  I have"). With two members claiming fabrication asks, the model loaded neither and refused
  on its own.
- Every case 2 miss refused to script Looker experience, with no tool call (it did not read
  the resume or the tracker). Nothing fabricated reached the user, but the family gate did not
  run, and the user got generic advice instead of a prep pack from their files.
- Case 3 may also have softened (3/6 committed vs 5/6 with cover-letter 1.1.1); 6 samples
  each is too few to call it. Not investigated further.
- Draft v1 fixes case 2 (12/12) without moving any control, and case 3 is at least as good as
  the committed text (12/15 vs 6/9).

## Draft v1 (interview-prep, for owner approval)

`draft-v1-description.txt` (993 of 1024 chars, ASCII; YAML block in `draft-v1-block.txt`,
which parses back to the exact text). Changes against 1.1.0:

- The fabrication ask gets its own clause, outside the short-ask list: "and especially when
  they ask to sound experienced in, or fake, a tool or skill the posting wants that they
  lack".
- "load it rather than answering from general knowledge" becomes "rather than answering or
  refusing from general knowledge" (every miss was a refusal).
- To fit: drops the file list "(tracker entry, documents they sent, confirmed lessons)", the
  "case" stage, "for a job they applied to" in the Use clause (it stays in the first
  sentence), and "questions," in the hiring-side exclusion. Do-not-use targets unchanged.

Alternative not tested: narrow cover-letter 1.2.0 instead (for example "add to the letter a
claim ..."). That reopens an owner-approved text whose own fabrication case went 4/9 to 12/12,
so draft v1 changes only interview-prep.

Gate caught during the run: the first draft block was wrapped with Python's default
`textwrap`, which split "cover-letter" across lines, so the folded YAML read "cover- letter".
The block was rewrapped without hyphen breaks and checked with `yaml.safe_load`; cases 2, 3
and cover-letter 3 were re-run on the fixed block (`*-draft-v1b-*` files). The other controls
ran on the first block; the only difference is that one space at the very end.

## Not done

- No `interview-prep/SKILL.md` change in the repo: awaits owner approval. If approved: apply
  byte-identical (`draft-v1-block.txt`), bump `_meta.json` (minor), CHANGELOGs, CI, deploy per
  runbook, then probe interview-prep 1-6 and cover-letter 1-4 after deploy and run the family
  routing evals (negatives: hiring side, media interviews, salary). The routing runner reads
  the installed copies, so negatives can only be measured after the deploy.
- Not checked together with the three pending drafts (career-profile v2, job-search v1,
  outcome-learning v1); if more than one is approved, re-sweep them in one clone first.
- Full install (319 skills) not probed for this case.

## Files

`report-<run>.md` / `results-<run>.json`:
`current-case2`, `current-case3` (committed); `cl111-case2`, `cl111-case2-rep`, `cl111-case3`
(cover-letter 1.1.1); `draft-v1-case2`, `draft-v1-case3`, `draft-v1-ctl-<member>` (first
block); `draft-v1b-case2-3`, `draft-v1b-ctl-cover-letter-case3` (fixed block). Raw stream
transcripts and both clones: outside the repo (`E:\tmp\jh-ip2\`).
