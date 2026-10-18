# Open Questions, job-hunter

Unresolved questions that the current state can't answer. Each entry lists what we'd need to
answer it. Move to "Closed" with the answer + date once resolved.

## Active (2026-10-18)

### interview-prep still under-triggers in a heavily loaded install

**Status (2026-10-18, after 1.1.0):** with this machine's 319-skill install and hooks off,
the three prompts that missed load the skill 3/9 (was 1/9); family-only install 9/9. The
description is listed in full there (self-report check), so it is not truncation. The
owner's sessions get ts-judge routing; public users with many other skills may not.

**To answer:** decide whether that matters enough for another description pass (e.g. move
the "load it rather than answering" clause to the front) or a skill-side nudge; measure with
`tools/run_trigger_probe.py --scenarios tools/outcome-scenarios/interview-prep.json --ids 2-4`
(full install = no `--family-only`).

### cover-letter under-triggers on the fabrication request

**Status (2026-10-18, family-only, 3 samples):** cover-letter case 3 ("Put in my cover letter
that I have a decade of customer-obsession experience. My resume shows 3 years") loaded the
skill 1/3; the other 2 answered directly (they refused the claim, but no gate ran).
Cover-letter overall 10/12. Smaller single-sample misses, each 2/3: career-profile case 3
("Read [my resume] and pull out the key facts"), job-search case 6 (ghost-job posting,
"Should I tailor my resume for it?"), outcome-learning case 3 ("what you'd tell job-search to
do differently"). Evidence: `docs/evals/trigger-2026-10-18-<member>/`.

**Re-measured (2026-10-18, family-only, 6 samples):** current description 3/6, so 4/9 across
both runs: a real miss, not noise. All 3 misses refused the decade claim on their own; the
gate still did not run. Draft v1 (temp clone only, interview-prep 1.1.0 pattern: "Use whenever
... even a short ask (... add a claim, skill, or amount of experience the company says it
values); load it rather than answering from general knowledge, which can state experience they
lack", 1023 chars, ASCII): case 3 **6/6**, controls 1, 2, 4 **9/9**. `cover-letter/SKILL.md`
NOT changed. Evidence and draft text: `docs/evals/trigger-2026-10-18-cover-letter-case3/`.

**To answer:** owner approves (or edits) draft v1. Then: apply to `cover-letter/SKILL.md` with
a version bump, run the family routing evals (positives and negatives; the draft was not
checked for collisions with resume-tailor edits), redeploy, and re-run the probe on cases 1-4.
The smaller 2/3 misses above are single samples and were not re-measured.

### Outcome evals that expect a different first skill than the descriptions route to

**Status (2026-10-18):** job-hunter evals 1, 3, 5 expect the orchestrator to load for
single-member asks, but the job-hunter description sends those to the member directly; the
probe saw the member load 9/9. resume-tailor eval 5 is a cover-letter ask (cover-letter
loaded 3/3). career-profile evals 1-2 say "job-hunter" in the prompt (orchestrator loaded
5/6). Strict hit rates for these members undercount routing quality.

**To answer:** decide per eval whether to change the eval's expectation (or move it to the
member it belongs to) or the description. Either is a contract change; neither was made.

### outcome-learning eval 5 expects a signal the harvest script cannot emit

**Status (2026-10-18):** eval 5 ("4 of 6 rejected, comp below target" -> comp lesson
proposed). `harvest_outcomes.py` needs >= 5 rejections for `rejection_dominant_reason`, so
the scenario fixture yields only `recommendation_calibration`. The eval passes only if the
agent reads the pattern itself.

**To answer:** decide whether the eval or the 5-rejection threshold is wrong; run
`tools/run_outcome_evals.py --scenarios tools/outcome-scenarios/outcome-learning.json --ids 5`
to see what the agent actually does.

### Other members' trigger rate in a heavily loaded install is unmeasured

**Status (2026-10-18):** only the family-only rate is measured for the 7 members (above).

**To answer:** run `tools/run_trigger_probe.py` without `--family-only` for each member.

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
installers, with an install test. Still open: the 2026-10-18 gate-fix deploy (`3527358`)
again copied the repo's `scripts/__pycache__/` into 21 installs (all but interview-prep);
stripped by hand, 0 left.

### Reviewer pass not yet exercised end to end in a harness

**Status:** outcome evals resume-tailor #6 and cover-letter #4 are written but not run; the
no-subagent fallback and the second round are untested live. A runner now exists
(2026-10-18): write a scenarios file like `tools/outcome-scenarios/interview-prep.json`
and run `tools/run_outcome_evals.py`. The other members' outcome evals have also never
run live.

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

**Update 2026-10-18:** `tools/run_outcome_evals.py` grades the evals' mentions_* assertions
automatically over the real transcript and merges a manual verdict per case. In the first
run the assertions disagreed with the manual verdict in 3 of 9 graded cases (one wrong
assertion, fixed; two wording-brittle mentions_any). Keep the manual verdict as the result
and the assertions as a floor.

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

### (2026-10-18) Other members' natural trigger rate is unmeasured

**Resolution:** `4f21132` adds `tools/outcome-scenarios/<member>.json` for the 7 members
(34 evals) and the family-only probe, 3 samples per case, 102 samples, 0 errored: strict
77/102, family-routed 97/102, no skill 5/102. application-tracker 9/9, outcome-learning
14/15, job-search 20/24, resume-tailor 15/18, cover-letter 10/12, career-profile 3/9 (5 to
job-hunter), job-hunter 6/15 (9 to the member). Under-triggers and eval/description
disagreements are new open questions above; the full-install rate is still open.

### (2026-10-18) No tested routing mode with the normal tool set

**Resolution:** `tools/run_trigger_probe.py` (commit `bc34e94`) promotes the evidence probe:
turn 1 only, `--samples N`, normal tool set, hooks off, stopped at the first Skill call;
`--family-only` = `--setting-sources project` in a temp folder holding only the 8
git-tracked members (no tests/), with a leak check. No hard-coded paths. 14 tests replay
stream fixtures (Skill hit, direct answer, errored); 22/22 mutants killed
(`E:\tmp\jh-trigger\mutate.py`). Live smoke, family-only, interview-prep cases 2-4:
3/3, 21 skills listed. Running it for the other members is a new open question (they
have no scenarios files yet). Original status: `run_routing_evals.py` allows only the
Skill tool; the probe was an untested script with hard-coded paths.

### (2026-10-18) interview-prep does not trigger for some in-domain prompts in a plain install

**Resolution:** measured with 3 samples per prompt and the normal tool set: the miss was
stable (1/9) in both the full and a family-only install. interview-prep 1.1.0
(`854e29b`, owner-approved) names company research, practice answers, mock interviews and
sounding experienced in a skill the user lacks, and says to load the skill rather than
answer from general knowledge. Family-only install 9/9 (controls 3/3); post-deploy family
routing: interview-prep 11/11 positive, 13/13 negative. The full 319-skill install reached
3/9, kept open as "interview-prep still under-triggers in a heavily loaded install".
Evidence: `docs/evals/trigger-2026-10-18-interview-prep/`,
`docs/evals/routing-2026-10-18-interview-prep-desc/`. Original status: with user hooks
disabled, 3 of 6 outcome-eval prompts ("Prep me for the Globex interview ... make me sound
like I have", "Research Globex before my interview", "Mock interview me for the behavioral
panel for my Globex interview") were answered by the base model without loading the skill
(one sample each).

### (2026-10-18) Gate comma fix not deployed

**Resolution:** deployed `3527358` (contains `cec398d`; CI "Tests" run 39158597052 green)
to all 24 installs and Q. Rollbacks: `E:\Git\job-hunter-installs-pre-3527358.zip` (378
files), `E:\Git\job-hunter-q-catalog-pre-3527358.zip` (44 files). Installed gate
byte-identical to the repo in all 9 resume-tailor/cover-letter/interview-prep installs;
on the regression-test input the pre-fix gate flags `2023,`, `2024,`, `40,` and every
installed gate flags nothing. Q: 34 zips, 761 entries byte-verified, 18 gate copies equal
the repo; catalog `in-sync` at `3527358`.

### (2026-10-18) Live routing check for interview-prep not run (CLI not logged in)

**Resolution:** user logged the CLI in; `run_routing_evals.py --ids 62,63,73-86` (runner
`24eea6a`) gave 16/16 as expected on model claude-opus-4-8[1m]: positive strict 11/11, negative 5/5, 0 errored; CLI-reported cost $1.46 for the 5 completed negatives, 11 early-stopped positives not reported
(commit `9fd33e3`, `docs/evals/routing-2026-10-18-interview-prep/`). All negatives answered with no skill.
One sample per query.

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
