# Open Questions, job-hunter

Unresolved questions that the current state can't answer. Each entry lists what we'd need to
answer it. Move to "Closed" with the answer + date once resolved.

## Active (2026-10-18)

### Live routing check for interview-prep not run (CLI not logged in)

**Status:** `run_routing_evals.py --ids 62,63,73-86` failed on every call with "Not logged
in - Please run /login". Only the proxy check exists (18/18,
`docs/evals/interview-prep-proxy-2026-10-18/`). Needed: `claude` CLI logged in, then re-run
those ids (~$0.4-0.9 per query). Since `24eea6a` the runner exits 1 and lists errored
calls instead of scoring them, and a rerun of the same `--out-dir` retries them.

### Three copies of the gate

**Status:** `verify_no_fabrication.py` is now bundled in resume-tailor (canonical),
cover-letter and interview-prep; any ruff fix to it must be made in resume-tailor and
re-copied to both (parity tests in each).

### ruff debt (18 findings) and gate phrase-run noise

**Status:** `ruff check .` reports 18 pre-existing findings (unused imports including
`Counter` in both copies of `verify_no_fabrication.py` and in `extract_ats_keywords.py`;
unused variables; one E741). CI does not run ruff although CONTRIBUTING.md says it should
pass. Fixing the gate copies needs both edited together (byte-identical test). Separately,
the gate's `new_phrase_runs` joins lines, so reordered or adjacent lines produce many false
runs (14 on a truthful revised draft in the 2026-10-18 trial).

### Installer copies untracked caches

**Status:** `install.ps1` copies the member working tree and strips only `tests/` and
`docs/superpowers/`, so gitignored `.pytest_cache/` reaches installs (12 files before the
2026-10-18 deploy). Cleaned by hand; fix = strip `.pytest_cache` and `__pycache__` in both
installers, with an install test.

### Reviewer pass not yet exercised end to end in a harness

**Status:** outcome evals resume-tailor #6 and cover-letter #4 are written but not run; the
no-subagent fallback and the second round are untested live. Needs a real `claude -p` run
(see `tools/run_routing_evals.py` for the runner pattern).

## Active (2026-10-11)

### Retire E:\Git\skills\job-hunter entirely?

**Status:** it is now inert for Q sync (skip-listed), but still a second v4 copy beside the frozen
`E:\Git\skill-builder-workdir\job-hunter`. Deleting it is destructive and user-gated; the skip-list
makes it optional.

**Note on the v4-era items below:** "delete the v3 install" was resolved 2026-05-28 (all v3/v4
installs removed; see session-state.md). The others are still open but now apply per member
(e.g. `parse_resume.py` lives in career-profile, the rubric stub in job-search).

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

**Status (2026-10-12, ANSWERED - partly no; FIXED 2026-10-13 in career-profile v1.1.0, see
its CHANGELOG and tests/test_parse_resume.py):** tested
(`career-profile/scripts/parse_resume.py`) via `uv run ... --json` on 11 Word-authored files:
5 synthetic resumes (fictional person) built with python-docx, re-saved by Microsoft Word, and
exported to PDF by Word, plus an image-only "scanned" PDF. Harness + fixtures: `E:\tmp\jh-resume\`
(`gen/make_fixtures.py`, `gen/word_roundtrip.ps1`, `gen/score_parse.py`, `results.json`).
- PDF (Word export): 12/12 facts on all 5 layouts, including the 2-column table; section detection OK.
- DOCX bugs: (1) page-header content dropped (name/email/phone lost); (2) text-box content
  dropped (same); (3) tables are appended after ALL paragraphs, so reading order breaks and an
  experience table lands under the CERTIFICATIONS section; (4) horizontally merged cells repeat
  their text once per grid column (bullets tripled); (5) a heading inside a table cell is joined
  with " | " so the 2-column layout loses its "experience" section.
- Scanned PDF: exit 0 with empty text and no warning (silent failure).
- Docs: `career-profile/SKILL.md` showed plain `python scripts/parse_resume.py`, which needs
  python-docx/pypdf installed. CORRECTION 2026-10-13: on this machine they ARE installed (user
  site-packages), so plain python works here; the earlier "not installed" failure came from
  testing with `python -I`, which ignores user site-packages. Docs now lead with `uv run`.

**Next:** fix in document order (walk body XML incl. tables; add headers + text boxes; dedupe merged
cells), fail loudly on empty PDF text, fix the docs, and turn the fixtures into regression tests.

### Are the state workforce commission URLs in `state-workforce-commissions.md` still live?

**Status (2026-10-13, ANSWERED - no; FIXED in job-search v1.0.1, commit `46b585e`):** all 51
checked. 13 replaced (7 no DNS: AL KY LA MA NJ NY OR; GA's employgeorgia.com hijacked by an
online-poker site; MT/OK/PA failed or retired; NH pointed at a non-job page; RI pointed at the
agency homepage), 7 moved to their .gov redirect target. The same dead domains were in
`build_search_queries.py` STATE_PORTALS (NY MA PA GA OR). Spot-checking 5 would likely have missed
the hijack: check ALL rows and read page titles, not just status codes.

**Ongoing:** quarterly, run `python tools/check_state_portals.py`; confirm 403/reset/timeout rows
in a real browser (AZ, NH, DC block scripts; FL/SC/TN/TX reset under repeated hits) before calling
them dead; confirm replacements against the agency's own .gov page. `tools/test_state_portals.py`
keeps the script in sync with the table and blocks retired domains. Next due: 2027-01-13.

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

### (2026-10-18) Routing runner scores CLI errors as "(none)"

**Resolution:** fixed in `24eea6a`. A `result` event with `is_error: true` (the auth
failure arrives as subtype "success") now marks the case `errored`: excluded from strict,
lenient and negative scores, listed in an "Errored" report section with the error text,
run exit code 1, and retried on rerun instead of reused. Two tests replay the real
not-logged-in stream through `main()`; both failed on the old runner. CI command: 367 passed.

### (2026-10-12) Republish Q:\skills\job-hunter from this repo?

**Resolution:** user approved; done. Rollback zip `E:\Git\job-hunter-q-catalog-pre-2026-10-11.zip`;
28 rebuilt member zips + plugin + family installer on Q, all byte-verified against source; catalog
shows v6.0.0 in-sync. Pipeline guard `E:\Git\skills` `e6993da` prevents a repeat.

### (2026-05-18, v4 ship) Where should v3 be installed for global use?

**Resolution:** Installed across all three paths (`~/.claude/skills/job-hunter-v3/`,
`~/.codex/skills/job-hunter-v3/`, `~/.agents/skills/job-hunter-v3/`) via `.install.ps1`.
v4 followed the same pattern at `~/.claude/skills/job-hunter-v4/` etc. The three-path
install gives Claude Code, Codex, and cross-vendor `.agents/skills/` coverage without
forcing a choice. Plugin-managed original at `anthropic-skills:job-hunter` remains
untouched. Whether to delete the v3 paths now that v4 ships is tracked as a separate
Active question above.
