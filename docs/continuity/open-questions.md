# Open Questions, job-hunter

Unresolved questions that the current state can't answer. Each entry lists what we'd need to
answer it. Move to "Closed" with the answer + date once resolved.

## Active (v4-era)

### Should we delete the v3 install now that v4 ships?

**Status:** v4 installed at `~/.claude/skills/job-hunter-v4/` (+ codex + agents paths). v3
install at `~/.claude/skills/job-hunter-v3/` is still present alongside. Both score the same
audit (15/15) and respond to the same trigger surface; v4 supersedes.

**To answer:** Check whether any active skill mention, slash command, or other tooling
references `job-hunter-v3` by literal name. If clean, delete the three v3 install paths in
one pass and update `session-state.md` to record the cleanup.

### Does the mock-runner 100% trigger accuracy hold under real Claude invocation for the v4 outcome evals?

**Status:** v4 added 4 outcome evals (#9 ghost-job, #10 full-scoring, #11 first-run profile,
#12 second-run profile) that encode multi-step interactions the mock runner can't fully
exercise. Mock confirms the description still triggers correctly; outcome quality on these
specific scenarios is untested under live Claude.

**To answer:** Run `run_evals.py --skill ... --runner claude --out-dir ...` (requires API
credentials). If outcome assertions fail at runtime, either the SKILL.md instructions need
tightening or the eval assertions need refinement against observed real behavior.

### When can `references/posting-quality-rubric.md` (the stub) be deleted?

**Status:** v4 step 2 split it into `match-quality-rubric.md` + `posting-legitimacy-rubric.md`
and kept the old filename as a stub redirector for backward compat. Stub will be safe to
delete once one full iteration has passed with nothing referencing the old path.

**To answer:** In v5, grep the entire skill for `posting-quality-rubric` references; if only
the stub itself shows up, delete the stub and remove the historical references from continuity
docs as a cleanup pass.

### Should the profile feed into score_posting.py directly, or stay as a soft re-rank?

**Status:** v4 ships with the profile as a soft re-rank applied by the agent, not as a hard
input to `score_posting.py`. The script doesn't read the profile file. Deal-breakers from the
profile become `red_flags_penalty: 1.0` on matching postings, but the agent applies this, not
the script.

**To answer:** Wait for signals. If users repeatedly say "I told the skill X but it still
recommended postings violating X," promote the profile to a script input. Until then, the soft
re-rank gives more flexibility for nuanced cases.

## Active (carried over from v3)

### Does the mock-runner 100% trigger accuracy hold under real Claude invocation?

**Status:** Untested. Mock uses keyword-overlap; real Claude uses description comprehension
+ context inference. They can diverge.

**To answer:** Run `run_evals.py --skill ... --runner claude --out-dir ...` (requires API
credentials and incurs per-call cost). Then compare against the mock-runner baseline. If
real-Claude accuracy is materially lower, the description needs another tuning pass against
real behavior, not the mock proxy.

### Does `parse_resume.py` work end-to-end on real DOCX and PDF inputs?

**Status:** Smoke-tested with text and HTML only this session. The PEP 723 dependency
declarations should let `uv run` fetch python-docx and pypdf, but that path wasn't exercised.

**To answer:** Get a sample DOCX resume + sample PDF resume; run `uv run scripts/parse_resume.py
<path> --json` against each; verify text extraction and section detection. If either fails,
fix and update the script.

### Are the state workforce commission URLs in `state-workforce-commissions.md` still live?

**Status:** Reference says "verify-portal-is-live" maintenance is recommended. Last verified:
the date this reference was authored (unclear, not recorded in the file). Some state portals
rebrand and redomain frequently.

**To answer:** Quarterly maintenance task. Spot-check 5 random state portal URLs; if any 404
or redirect to "we've moved" pages, update the table. Add this to `maintenance.md`.

### Should the skill auto-detect ATS systems from posting URLs?

**Status:** `references/ats-formatting-guide.md` mentions specific ATS products (Workday,
Greenhouse, Lever, Ashby) but the skill doesn't auto-detect which ATS a posting uses, even
though the URL often gives it away (`*.greenhouse.io/...`, `*.lever.co/...`,
`*.workday.com/...`, `*.ashbyhq.com/...`).

**To answer:** If we want this, it's a small `detect_ats.py` helper. Open question is whether
it's worth the script weight, the agent can infer ATS from URL with no helper. Punt unless a
specific user case demands it.

### What's the right outcome-eval grading mechanism?

**Status (v4 update):** Still unresolved. v3 had 8 outcome evals with 3-6 assertions each;
v4 expanded to 12 (added #9-#12 for ghost-job, full-scoring, and 2 profile scenarios). All
still record as "manual review required" in `run_evals.py`. No automated grading.

**To answer:** Either (a) hand-grade against a real invocation pass, highest fidelity but
doesn't scale; (b) build an LLM-as-judge grader, out of scope for this skill, properly
belongs in `self-improving-skills` harness. For now, manual review on demand is acceptable;
the trigger evals + 69 unit tests + frozen cohorts carry most of the regression-detection
value.

### Should freelance/contract job search use different sources than full-time?

**Status:** Currently the search tiers are identical for full-time, freelance, contract. But
freelance has its own well-known sources (Upwork, Toptal, Contra, Fiverr Pro) not in the
current niche-boards reference.

**To answer:** If a real user request makes this surface, add a freelance-specific row to
`niche-boards-by-industry.md` and/or add `--employment-type freelance` flag to
`build_search_queries.py`. Not blocking; speculative until requested.

## Closed

### (2026-05-18, v4 ship) Where should v3 be installed for global use?

**Resolution:** Installed across all three paths (`~/.claude/skills/job-hunter-v3/`,
`~/.codex/skills/job-hunter-v3/`, `~/.agents/skills/job-hunter-v3/`) via `.install.ps1`.
v4 followed the same pattern at `~/.claude/skills/job-hunter-v4/` etc. The three-path
install gives Claude Code, Codex, and cross-vendor `.agents/skills/` coverage without
forcing a choice. Plugin-managed original at `anthropic-skills:job-hunter` remains
untouched. Whether to delete the v3 paths now that v4 ships is tracked as a separate
Active question above.
