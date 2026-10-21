# Changelog

One entry per accepted iteration. Lead with the *signal* that motivated the change, not just the change itself.

## Gate: UTF-8 stdin, ASCII stdout JSON (2026-10-20, family v6.0.0 line)

Signal: reading the gate's printed report through a Windows pipe failed with
`UnicodeDecodeError: 'utf-8' codec can't decode byte 0x97` (an em dash in a context string,
encoded in the console code page cp1252); a check mark crashed the script outright. Piped
input had the mirror problem: UTF-8 read as cp1252 mojibake.

What shipped (`verify_no_fabrication.py`, canonical in resume-tailor, byte-identical in
cover-letter and interview-prep):
- `--original-stdin` / `--proposed-stdin` read UTF-8 bytes, like the file inputs.
- The printed JSON is pure ASCII (`\u` escapes that any JSON parser restores); the `--out`
  file stays UTF-8 with the real characters.
- 4 tests simulate a cp1252 pipe (`PYTHONIOENCODING=cp1252`); 3 failed before the fix, 1
  guard (the `--out` file). 5 mutants killed. resume-tailor 1.1.6, cover-letter 1.2.5,
  interview-prep 1.2.3.

## Gate: whole-word proper nouns (iOS / vCard noise) (2026-10-20, family v6.0.0 line)

Signal: finalizing the owner's resume, the 1.1.4 gate flagged `OS` (from "iOS") and `Card`
(from "vCard") as new proper nouns. The scan matched a capital letter anywhere, even inside a
word, so a lowercase-first brand gave a fragment the source never has.

What shipped (`verify_no_fabrication.py`, canonical in resume-tailor, byte-identical in
cover-letter and interview-prep):
- Candidates are whole words. A lowercase-first word with an inner capital (iOS, vCard, eBay,
  iPhone) is checked as a whole and is never skipped as a sentence start, so a new one still
  flags, now under its real name. Hyphen parts are still checked one by one ("non-GAAP" gives
  "GAAP"; "mid-May" stays quiet).
- 7 tests on invented fixtures; 4 failed before the fix, 3 guards pin old behavior. 7 mutants
  killed. On the owner's real edit: `OS`, `Card` -> `iOS`, `vCard`. resume-tailor 1.1.5,
  cover-letter 1.2.4, interview-prep 1.2.2.

## Gate: DOCX headings and markerless bullets (2026-10-20, family v6.0.0 line)

Signal: the owner's resume reassessment (2026-10-20) ran the installed resume-tailor 1.1.1
gate on DOCX text (python-docx paragraph text: no bullet markers, headings as plain Title
Case lines). It reported 41 flags, 17 of them proper nouns the resume already had, and did
not report a new `Earlier Experience` heading. The proper-noun noise and the "20" context
bug were already fixed in 1.1.2 (26d7738) but never deployed. Two gaps were still open:

What shipped (`verify_no_fabrication.py`, canonical in resume-tailor, byte-identical in
cover-letter and interview-prep):
- A short Title Case line (1-5 words, optional colon) with a resume-section word counts as
  a heading, and is new only if no source line has the same text in any case. Job-title,
  employer and skill lines are not headings. A heading with no section word is still missed.
- `new_bullets`: when either document has no markers, every non-blank line under a heading
  counts in both. Lines before the first heading do not, so a headingless cover letter or
  interview claims list stays quiet.
- 13 new tests on an invented DOCX-shaped fixture; 7 failed before the fix. One guard (a
  headingless letter gives no bullets) was added after a first version of the fix counted
  a letter's lines as bullets; it failed on that version. 10 mutants killed. On
  the owner's real resume pair (counts only): 17 proper nouns to 1 (a confirmed new word),
  `Earlier Experience` now reported, its 11 moved lines counted; 41 flags to 37.
  resume-tailor 1.1.4, cover-letter 1.2.3, interview-prep 1.2.1.

## Four description fixes for natural-trigger misses (2026-10-20, family v6.0.0 line)

Signal: family-only natural-trigger probes (normal tool set, hooks off) found four in-domain
asks that did not load their member: interview-prep's "make me sound like I know Looker"
(0/12, caused by the cover-letter 1.2.0 description), career-profile's "read my resume and
pull out the key facts" (6/9), job-search's possible ghost-job posting (7/9) and
outcome-learning's "what you'd tell job-search to do differently" (5/9).

What shipped (descriptions only, owner-approved 2026-10-20; do-not-use clauses kept):
- **interview-prep 1.2.0**, **career-profile 1.2.0**, **job-search 1.1.0**,
  **outcome-learning 1.1.0**.
- Swept together in one clone before shipping (`docs/evals/trigger-2026-10-20-joint-sweep/`):
  every target case 6/6; the other members unchanged except job-search case 1, 7/9 with both
  misses routed to the job-hunter orchestrator (9/9 before).

## Gate: catch a new word on its own line (2026-10-19, family v6.0.0 line)

Signal: while verifying the 26d7738 reformat fix, a pre-existing safety gap turned up. The
gate skipped any capitalized word after a line break as a "sentence start", so a new tool
added as a bare line in a one-per-line list (`SKILLS` / `Budgeting` / `Scheduling` /
`Salesforce`) gave verdict `clean`: no proper noun, and too few words for a phrase run.
Bullet lines (`- X`) and mid-line words were already caught.

What shipped (`verify_no_fabrication.py`, canonical in resume-tailor, byte-identical in
cover-letter and interview-prep):
- A word that starts a line, the first line included, is now a proper-noun candidate unless
  the text before it (across blank lines) ends with . ! or ?. Sentence starts, such as a
  cover-letter paragraph after a full stop, stay skipped.
- Since 26d7738 a candidate flags only if the source has it nowhere, in any case, so the
  reformat fixture still gives zero new proper nouns.
- 7 new tests on invented fixtures (new list item, CRLF list item, new job-title line, new
  name line, new first line; reordered list and sentence starts stay quiet); 5 failed
  before the fix. Mutation-checked (6 mutants killed). resume-tailor 1.1.3, cover-letter
  1.2.2, interview-prep 1.1.2. Not deployed to installs yet.

## Gate: fewer false flags on a tighten-only reformat (2026-10-19, family v6.0.0 line)

Signal: the owner ran resume-tailor Mode A (tighten only, no new claims) on their real
resume, 9 pages down to about 3.5. The gate returned review_required with 14-19
new_proper_nouns that were all words already in the resume, plus a new number "20". Every
flag was a formatting artifact or a fact the owner confirmed, but the list was long and hard
to read.

What shipped (`verify_no_fabrication.py`, canonical in resume-tailor, byte-identical in
cover-letter and interview-prep):
- **Proper nouns:** a capitalized word in the proposed text is new only if the source does
  not contain it anywhere, in any case. Joining a one-per-line competency list with " | "
  no longer flags Budgeting, Sales, Team and the like.
- **Numbers:** a unit letter (k, M, b) counts only when no letter follows it, so "20
  Mechanics" and a wrapped "20" / "Mechanics" are both "20", not "20 M". The context
  snippet now comes from a whole-token match, so a new "20" no longer shows the context of
  "200+". ("200+" was already one token; the split seen in the report came from the
  context lookup.)
- 7 new tests on an invented resume; one is load-bearing (a new tool, employer and number
  added to the same reformat must still flag). resume-tailor 1.1.2, cover-letter 1.2.1,
  interview-prep 1.1.1. Not deployed to installs yet.

## cover-letter description: trigger on the fabrication ask (2026-10-18, family v6.0.0 line)

Signal: the family-only trigger probe loaded cover-letter for case 3 ("put a decade of
customer-obsession experience in my cover letter; my resume shows 3 years") 1/3, then 3/6 on
a 6-sample re-run (4/9). The base model refused the claim on its own, but the
`verify_no_fabrication` gate never ran.

What shipped:
- **cover-letter 1.2.0** (description only, owner-approved): "Use whenever ... even a short
  ask (... add a claim, skill, or amount of experience the company says it values); load it
  rather than answering from general knowledge, which can state experience they lack". The
  gate is in the first sentence. Do-not-use clauses unchanged; 1023 chars, ASCII (the old
  em dash is gone).
- Result in the family-only probe: case 3 6/6 (was 4/9), cases 1, 2, 4 9/9. Evidence:
  `docs/evals/trigger-2026-10-18-cover-letter-case3/`.

## Outcome scenarios and natural-trigger rates for the other 7 members (2026-10-18, family v6.0.0 line)

Signal: only interview-prep had a scenarios file, so `tools/run_trigger_probe.py` could not
measure any other member's description.

What shipped:
- `tools/outcome-scenarios/<member>.json` for job-hunter, career-profile, job-search,
  resume-tailor, cover-letter, application-tracker and outcome-learning: fictional
  fixtures plus turn-1 prompts for all 34 outcome evals, keyed by eval id. Text files
  stand in where an eval names a DOCX/PDF. A parametrized test per file checks it covers
  every eval id, matches the skill name and is ASCII (2 mutants killed). CI command 404
  passed.
- Family-only probe, 3 samples per case (`docs/evals/trigger-2026-10-18-<member>/`):
  strict hits 77/102. Most misses loaded the family-correct member (single-member asks
  went straight to that member; "job-hunter" or "find me a job" prompts loaded the
  orchestrator). Only 5/102 answered with no skill, with cover-letter's
  anti-fabrication case worst at 2/3. No SKILL.md changed.

## Natural-trigger probe promoted to a tested tool (2026-10-18, family v6.0.0 line)

Signal: the probe that measured interview-prep's real trigger rate (1/9, then 9/9) was an
untested evidence script with hard-coded paths; `run_routing_evals.py` allows only the
Skill tool and overstates triggering, so other members had no honest way to be measured.

What shipped:
- **`tools/run_trigger_probe.py`**: turn 1 of each outcome case, `--samples N` fresh
  sessions, normal tool set of `run_outcome_evals.py`, user hooks off, stream read until
  the first Skill call. `--family-only` runs with `--setting-sources project` in a temp
  folder whose `.claude/skills` holds only the 8 git-tracked members (no tests/), and
  errors out if user skills or plugins leak into the listing. Outcomes: skill (hit or
  other skill), answered, capped (max turns), errored (not scored, exit 1, retried on
  rerun). `--dry-run` makes no calls and writes nothing.
- `tools/test_run_trigger_probe.py` + `tools/trigger-fixtures/` (Skill hit, direct
  answer, errored streams): 14 tests, 22/22 mutants killed. CI command 397 passed.
- Live smoke (family-only, interview-prep cases 2-4, 1 sample each): 3/3, 21 skills
  listed, matching the evidence probe.

## interview-prep description: trigger on research, mock and "sound experienced" asks (2026-10-18, family v6.0.0 line)

Signal: the live outcome run showed natural routing missing 3/6 in-domain prompts. A
trigger probe with the normal tool set and user hooks off (3 samples each) confirmed it
was stable: 1/9 loads in both a full install (319 skills) and a family-only install, and
the base model scripted unverified experience for the user ("I've built dashboards in
[tool]") without reading the resume.

What shipped:
- **interview-prep 1.1.0** (description only, owner-approved): names company research,
  practice answers, mock interviews and "sounding experienced in a skill they lack", and
  says to load the skill rather than answer from general knowledge. Do-not-use clauses
  unchanged; 1017 chars.
- Result in the family-only probe: 9/9 (was 1/9), controls 3/3. Evidence:
  `docs/evals/trigger-2026-10-18-interview-prep/`.

## Live outcome evals + gate comma fix (2026-10-18, family v6.0.0 line)

Signal: no family outcome eval had ever run in a real harness; interview-prep's 6 were
the first (`docs/evals/outcome-2026-10-18-interview-prep/`).

What shipped:
- **`tools/run_outcome_evals.py`** + `tools/outcome-scenarios/interview-prep.json`: runs
  each outcome eval through `claude -p` in a fresh fictional workspace (multi-turn via
  --resume, user hooks disabled), grades the eval's assertions over the assistant's text
  and tool inputs, and merges a manual verdict per case. `--invoke-skill` measures the
  skill once loaded when natural routing misses.
- **Gate fix** (resume-tailor 1.1.1, cover-letter 1.1.1, interview-prep 1.0.1): a comma
  after a number made a known year or number look new ("In 2023, ..."). Found live.
- interview-prep eval 3: the fee assertion no longer fails a warning that quotes the
  injected line.
- Result: with the skill loaded 6/6 meet expected_output; natural routing loaded it in
  3/6 (open question: description vs. answering directly).

## interview-prep member (2026-10-18, family v6.0.0 line)

Signal: a competitive review of MadsLorentzen/ai-job-search (2026-10-18) ranked its
`/interview` command as the most useful idea left after the reviewer pass, and interview
prep had been a deferred candidate since v4 (sibling-collision risk with generic interview
skills).

What shipped:
- **`interview-prep`, the 8th family skill.** It reads one tracked application (the
  tracker entry plus the resume and cover letter that were actually sent) and the user's
  confirmed lessons, and builds a stage-specific prep pack: likely questions mapped to the
  user's real lines as STAR scaffolds, gap bridges that never claim missing experience,
  questions to ask, and research that must carry a source the agent found itself (links
  inside the posting are rejected). Optional mock interview. Every answer line goes through
  the bundled `verify_no_fabrication.py` (byte-identical to resume-tailor's).
- Description written for the candidate side only, with do-not-use clauses for hiring-side
  interview plans, media interviews, thank-you notes, salary negotiation, resumes, and cover
  letters; 12 trigger evals (5 positive, 7 negative incl. those collisions), 6 outcome evals.
- Wired in: orchestrator routing and description, all siblings' `sister_skills`, the
  workspace contract (re-synced into every member, now guarded by a byte-equality test),
  application-tracker's do-not-use clause, both installers, `build_plugin.py`, the plugin
  manifests, the routing-eval tooling, CI, and the README (which also gained the missing
  cover-letter row).

## v6.0.0 (2026-05-28)

The big one: job-hunter is now a **skill family**, not a single monolith.

Why: as the skill grew (Phases 0-5, 16 scripts, a 681-line SKILL.md), a single coarse trigger surface meant "just tighten my resume" loaded the whole job-hunt machine, and the file was getting hard to evolve. The fix is the orchestrator-template pattern proven by other skill families: one **orchestrator** (`job-hunter`) that reads your request and routes to the right **member skills**, each a focused job-to-be-done that also works standalone.

What shipped:
- **6 skills:** `job-hunter` (orchestrator — owns the `.job-hunter/` workspace + routing + the anti-fabrication invariant) + `career-profile` (profile-intake), `job-search` (search), `resume-tailor` (resume-tailor), `application-tracker` (tracker), `outcome-learning` (learning-loop).
- **Typed artifact hand-offs:** members read/write the shared `.job-hunter/` workspace per `job-hunter/references/workspace-contract.md`; each degrades gracefully when run alone.
- **The anti-fabrication gate moved intact:** `verify_no_fabrication.py` lives in `resume-tailor` with all 5 of its load-bearing safety tests preserved, and the orchestrator enforces it as a family-wide invariant (no member writes resume/profile content without passing through it). The v5.2.0 fabrication fix is fully retained.
- **Family installer:** `install/install.sh` + `install/install.ps1` install all 6 members across `~/.claude`, `~/.agents` (Codex + OpenClaw), and `~/.hermes`, cross-OS.
- **No behavior regression:** the combined family test suite is **226 tests** (up from 201 in the monolith), all green.

Breaking change (hence the major bump): the install shape changed. Re-install with the family installer; the orchestrator triggers on the same job-search intents as before, and routes to the focused members underneath.

## v5.2.0 (2026-05-21)

This one is a correctness fix, not a feature release. A real user ran the resume optimizer on their actual resume and the skill added things that weren't there. Specific tools the user had never mentioned (Pinecone, Weaviate, LangChain). Numbers the user never gave (team sizes, project counts). Job title changes the user never asked for (Sole Developer to Lead Developer). Content pulled from the user's company website and merged into their resume without confirmation. Sections restructured without permission.

Every one of those is a fabrication. The whole point of the tailor flow is that the output represents the user honestly. If the skill invents experience, the user can't trust any of it.

**What broke and why**

Phase 3 of the SKILL.md was written with the truth-preservation rule listed as a Key Principle near the bottom of the document. The actual phase instructions said things like "push for numbers and outcomes" and "quantify wherever possible" with the truth guardrail tucked in as a parenthetical. When an LLM reads a long instruction document, the active and vivid instructions dominate the passive guardrails. The agent did exactly what the dominant instructions said and exactly what the buried guardrails forbade.

**What changed**

Phase 3 now splits into two explicit modes:

- **Mode A (Tighten / Copyedit):** zero-fabrication contract. The skill may improve how the resume reads, not what it says. Adding numbers, changing job titles, moving content between sections, and pulling from external websites are all explicitly forbidden. If the user wants quantification added, the skill asks for the numbers; it does not invent them.
- **Mode B (Tailor for a specific posting):** the existing flow, but with a mandatory verification gate before any DOCX is written.

The verification gate is a new script: `scripts/verify_no_fabrication.py`. Given the original resume and the proposed tailored version, it surfaces every new proper noun, every new number, every new section heading, every new bullet, and every new 5-word phrase run. The agent then has to walk the user through each item and get explicit per-claim confirmation before writing the file. The script never auto-approves anything. A load-bearing test asserts the script's output always has `auto_approved: false`.

A new rule explicitly addresses websites: if the user mentions their own site, LinkedIn profile, or company URL, the skill may fetch it for context but **may not merge its content into the resume without per-claim user confirmation**. The user's website is marketing copy. The user is the only source of truth about what they actually built.

**Other changes**

- Truth-preservation moved from a Key Principle at the bottom of SKILL.md to a Hard Gate at the top of Phase 3. The wording is now imperative ("you may not change what it says") rather than passive ("preserve truth").
- 3 new outcome evals (#22 tighten-not-tailor, #23 web-content-untrusted, #24 keyword-gap-fabrication-prevention).
- 24 new unit tests for `verify_no_fabrication.py`, including 3 load-bearing safety tests that prove the script can never auto-approve.

**Tests**

201 passing (177 from v5.1.1 plus 24 for the new script).

**Acknowledgment**

This fix exists because a real user noticed the bug and called it out clearly. That's worth more than any automated test. If you hit a similar issue with this skill, open an issue.

## v5.1.1 (2026-05-20)

A patch release. Running the v5.1.0 follow-up flow against a real tracker.json surfaced one annoying bug.

**Fixed**

The `scan-stale` helper that finds applications worth following up on was treating two different dates as if they were the same thing. The tracker stores `posted` (when the company put the role up) and now also `applied_date` (when you actually submitted). If only `posted` was set, scan-stale was treating a 30-day-old posting you'd just applied to as a 30-day-stale application, false positive, annoying suggestion to send a follow-up that wasn't actually overdue.

The fix is small and additive: tracker entries should now include `applied_date`, and `scan-stale` reads only that field. Existing trackers without it still render fine, they just won't show up in stale-checks, which is the right default (no signal, no inference). The HTML tracker grew an Applied column to make this visible.

**Other**

Reordered the `_meta.json` iterations array so versions read chronologically. Pure cosmetic.

**Tests:** 177 passing (174 before, plus the regression test that proves this bug doesn't come back, plus three for the new column).

## v5.1.0 (2026-05-20)

Three additions, all internal to the skill rather than spinning up new modes.

**New: follow-up drafting** (`scripts/draft_followup.py`)

When you've applied to something and heard nothing for a week, the skill now offers to draft a polite check-in. After an interview, it'll draft a thank-you. Both templates are short (under 150 words) and leave explicit placeholders for the things you should personalize, a generic "thanks for your time" gets ignored just as fast as silence. There's a `scan-stale` subcommand that reads your tracker.json and tells you which applications are eligible.

The skill never sends the email. It drafts; you copy-paste. That boundary is enforced by a test, the script can't even import an SMTP library without the test failing.

**New: workspace export/import** (`scripts/export_workspace.py` + `import_workspace.py`)

Moving machines, backing up, or sharing your job-search state with a collaborator? Export bundles your profile + the four learning-loop files + tracker.json into a single zip. Import restores it on the other end. A few safety choices worth knowing:

- Export refuses to write the archive into a cloud-sync path (Dropbox, OneDrive, iCloud, Google Drive, Box Sync) without `--allow-cloud`. The default is "don't accidentally upload your private job-search data."
- Import rejects path-traversal payloads (`../../`) and any archive members outside the documented allowlist. You can't be tricked into restoring a malicious zip into `/etc/passwd`.
- The archive includes a `manifest.json` for integrity verification.

**Expanded: non-tech job-board references**

The "Built for every career" promise was thin on the reference side. Added URL-verified entries for:

- **Healthcare:** Vivian Health, AlliedTravelCareers, state board of nursing search patterns
- **Trades:** IBEW/UA local-hall search patterns, SkillBridge for military-to-trades, BLS growth-rate context for electricians/plumbers/HVAC
- **Legal:** Robert Half Legal, BCG Attorney Search, state bar career pages
- **Government:** NEOGOV-hosted municipal portals, state civil-service exam search patterns

Every addition was checked before being added, no fabricated board names.

**Other**

SKILL.md now has a Phase 4.5 for the follow-up flow. README has new FAQ entries for follow-ups, workspace export, non-tech support, and the "we never send the email" boundary.

**Tests:** 173 passing.

**Deliberately not in this release:**
- Auto-sending emails (we don't own the send step)
- LinkedIn message templates (ToS makes automation risky)
- Salary research (deferred to a separate `salary-negotiation` skill if it ever happens)
- Network analysis ("who do I know at X") (needs LinkedIn API or scraping)

## v5.0.1 (2026-05-20)

A small patch.

The `harvest_outcomes` script reports a `decisions_present` flag in its output. After v5.0.0 shipped, that flag was always `true`, even on a fresh workspace where you'd added zero decisions. The check was naive: it asked "is there any non-whitespace content in DECISIONS.md?" Since the template itself ships with format documentation and a privacy notice, the answer was always yes.

Fixed by adding a marker comment in the template (`<!-- Agent and user entries appended below this line -->`) and slicing from that marker before checking. The harvest now correctly distinguishes "user has added decisions" from "the template scaffold exists."

This is the second time we've hit this class of bug, a parser scanning a template file and mistaking the documentation for data. The first time was in `parse_outcomes`, fixed mid-v5. Now there's an explicit pattern (append-marker comment + parser slices from it + a test that asserts the template body after the marker is empty) and it's documented as a chain-wide lesson.

**Tests:** 123 passing.

## v5.0.0 (2026-05-20)

The big one. Per-user learning loop.

Before this release, the skill remembered two things across sessions: your North-Star profile (5 preference questions) and your tracker.json (the list of jobs you'd targeted). That's stateful memory, but it's not really learning, the skill made the same decisions for you in session 50 that it made in session 1.

v5 adds four plain-markdown files in your workspace under `.job-hunter/`:

- **DECISIONS.md**: a running log of choices the agent makes on your behalf (and the reasons you give)
- **LESSONS.md**: patterns about your preferences, but only entries you've explicitly confirmed
- **OUTCOMES.md**: what actually happened to each application (offered / rejected / no response after 21 days)
- **REJECTED_IDEAS.md**: hard constraints you've stated. "No defense contractors." "No commission-only comp." The agent never re-asks.

Plus three new scripts:

- `init_workspace.py` scaffolds the four files on first use
- `harvest_outcomes.py` reads OUTCOMES + DECISIONS and looks for patterns (e.g., "4 of your last 5 rejections cited comp below target")
- `propose_lessons.py` translates those patterns into draft LESSONS.md entries

The agent surfaces a suggestion, you say yes or no, and only confirmed lessons get written. Every time, no exceptions.

**Six guardrails that keep this honest:**

1. **Cold-start guard.** No lessons proposed until you have at least 5 closed-loop outcomes. Pattern detection from thin data is guessing, not learning.
2. **Opt-in only.** The agent never auto-writes to LESSONS.md.
3. **Deterministic translation.** The "reason" line in every suggestion is anchored in observed evidence (counts, percentages), never paraphrased by an LLM.
4. **Bounded influence.** Lessons shape how sub-scores are *graded* for you. They don't change the scoring weights in `score_posting.py`, those stay the same for everyone.
5. **Plain markdown.** Every file is readable, editable, deletable. No black-box weights.
6. **Local-only.** No telemetry. No phone-home. No required API keys. `.job-hunter/` lives in your workspace.

The architecture is adapted from the proven harvest → propose → apply pattern in the `self-improving-skills` builder. Different artifacts (per-user data instead of skill-iteration edits), same discipline.

**SKILL.md changes:**
- New Phase 0: read the four files at the start of every session
- New Phase 5: close the loop, append outcomes, harvest signals, propose lessons, ask for confirmation

**Tests:** 120 passing (69 from v4 plus 51 for the new scripts).

**Deliberately not in this release:**
- Silent learning (every lesson needs explicit user opt-in)
- Per-user weight optimization (the deterministic-weights design from v4 is load-bearing)
- Cross-user learning aggregates (the loop is per-user only)

## v4 (2026-05-18)

This was the iteration that took the skill from "useful" to "defensible." Drove changes from a competitive review of `santifer/career-ops`, an MIT-licensed job-search system built after the author manually processed 740+ job listings. Folded in four of their better ideas, rejected five others.

**New: deterministic 1-5 scoring** (`scripts/score_posting.py`)

Every posting gets graded across five sub-scores: how well your resume matches, how comp compares to your target, cultural signals, posting legitimacy, and a red-flags multiplier. Weights are documented inline with rationale, `cv_match` carries the heaviest (0.35) because it's the single most predictive signal of whether the application reaches a human. Red flags are applied as a multiplier, not added: one severe flag (pays-only-in-equity, SSN pre-offer) can torpedo an otherwise-strong score from 5.0 down toward 1.0. The output is a recommendation: `apply` / `apply_if_specific_reason` / `skip`.

**New: ghost-job detection as its own axis**

Independent 2025 estimates put LinkedIn ghost-job prevalence at around 27% (ResumeUp.AI), with the broader online job market at 18-30% (Greenhouse 2025, Congressional Research Service IF12977). v4 treats ghost-job legitimacy as a separate sub-score (`posting_legitimacy`) on a three-tier scale, High Confidence / Proceed with Caution / Suspicious, using signals like posting age, repost patterns, apply-button quality, employer disclosure, and salary transparency.

**New: visible scoring in the tracker**

The HTML tracker grew a colored score badge per row (green / amber / grey for apply / specific-reason / skip), sortable, with filter controls and a collapsible sub-score breakdown. The CSS moved to a separate asset file so the renderer can be tested without dragging a hardcoded style block around.

**New: North-Star profile** (`scripts/init_profile.py`)

Five questions captured in `.job-hunter-profile.md` in your workspace (not in the skill directory, the dot-prefix is intentional, and the test suite enforces that no sample profile ever lives in the skill installation). The questions are: what archetype of role do you want (IC, tech lead, founding, etc.), deal-breakers, company-size preference, mission-vs-comp priority, and tolerance dimensions (on-call, travel, office days).

On the first session, the agent walks you through them. On subsequent sessions, it reads the profile and only asks "anything changed?" If the profile is more than 90 days old, it'll gently mention that.

**Rejected (and why):**
- Playwright + bundled Chromium PDF rendering, too heavy, fragile across OSes. Our DOCX-first output is ATS-equivalent and far more portable.
- A Go/Bubble Tea TUI dashboard, the HTML tracker is browser-portable with no install.
- A 45-company hardcoded portal list, breaks the generalist scope. This skill is for nurses, teachers, welders, lawyers, and engineers, not just AI engineers.
- Slash-command UX (`/career-ops scan`), Agent Skills auto-activate on natural language; that's the right primitive.
- Interview prep, deferred to a future separate skill rather than baked in, because there are ~12 interview-prep skills already on agentskills.io. The right play is a separate skill that consumes job-hunter's tracker.json.

**Scores:** trigger accuracy 100% (24/24), audit 15/15, skill score 106/106. 69 tests passing.

## v3 (2026-05-11) (eval-driven description rewrite + 4 new scripts + posting-quality rubric)

- **Signal:** Ran v2 evals through `run_evals.py --runner mock`. Result: **66.7% trigger accuracy (16/24)**. `optimize_skill.py` surfaced 5 false negatives (queries that should have triggered but didn't: #1 Seattle backend, #7 Stripe tailor, #8 cover letter, #9 ATS, #11 remote DevOps) and 3 false positives (queries that triggered but shouldn't have: #20 generic resume review, #21 career-path question, #24 post-layoff support). Dogfood inspection of v2 also surfaced 4 capability gaps: (a) resume reading depended on sibling docx/pdf skills, violating the standalone contract; (b) Phase 2 instructed "try synonyms" with no helper; (c) Phase 4 Application Tracker had no generator; (d) salary strings weren't normalized for comp-floor filtering.
- **Changes (each anchored in evidence):**
  - **Description rewrite (single largest leverage point):** Replaced v2's narrow "Trigger on…" phrase list with a Use-when clause packed with high-overlap natural-language vocabulary, `find jobs`, `find a job`, `find openings`, `find work`, `find positions`, `apply`, `tailor`, `optimize`, `search local/remote jobs`, `find companies hiring`, plus specific role types (engineers, managers, nurses, designers, analysts, freelance, contract, backend, frontend, data, product, graphic). Added explicit "Do not use for…" clause that filters career-coaching, generic-review, salary-negotiation, interview-prep, and post-layoff queries. Tuned through 7 iterations (3a–3g) of the mock runner; final description is exactly 1024 chars (spec max). Frozen-v1 cohort (5 trigger entries) **holds at 5/5**, no regression on the immutable held-out set.
  - **New `scripts/parse_resume.py`:** Reads DOCX (python-docx), PDF (pypdf), MD/TXT/HTML (stdlib) into plain text or structured JSON with auto-detected section breakdown (summary/experience/education/skills/certs/projects). Uses PEP 723 inline metadata, runs with `uv run`. Removes sibling-skill dependency for resume parsing, satisfying the standalone contract.
  - **New `scripts/expand_role_synonyms.py`:** 80+ roles across tech, healthcare, finance, marketing, operations, education, trades, legal, and sales with same-job synonyms and (optional) adjacent step-up/step-down roles. Handles bidirectional lookup (input "RN" returns canonical "nurse" + synonyms). Replaces the inlined 8-role table that lived in `build_search_queries.py`.
  - **New `scripts/generate_tracker_html.py`:** Renders Phase 4 Application Tracker from a `tracker.json` file the agent maintains over time. Self-contained inline CSS, color-coded status badges (to-apply/applied/interviewing/offer/rejected/withdrawn) and match-strength tags, totals-by-status pills, sortable table layout. Replaces the "regenerate HTML from scratch every time" pattern flagged as repeated-work.
  - **New `scripts/normalize_salary.py`:** Parses free-text salary strings ("$180k-220k", "USD 95/hour", "180,000 - 220,000 annually", etc.) into structured numeric ranges with currency, period, annualized min/max, and confidence score. Used in Phase 2 to filter postings against the user's stated comp floor and to compute market-median sanity checks against expectation.
  - **Improved `dedupe_postings.py`:** Added URL canonicalization that strips tracking params (utm_*, gclid, fbclid, refId, ref, etc.), normalizes scheme to https, strips `www.` prefix, normalizes trailing slashes, and sorts query params. Duplicates that differed only in tracking noise now correctly collapse. Output includes a `canonical_url` field on every entry.
  - **New `references/posting-quality-rubric.md`:** Deep red-flag detection catalog (10 specific patterns with what-it-looks-like + why-it-matters), match-strength rubric with concrete percentages, when-to-drop-a-posting criteria, salary-vs-market sanity check, freshness threshold guidance. Extracted from inlined SKILL.md content; SKILL.md now references it.
  - **SKILL.md rewiring:** Phase 1 step 1 now points at `parse_resume.py` for any-format resume reading; Phase 2 points at `expand_role_synonyms.py` when results are thin; Phase 2's red-flag/match-scoring paragraphs extracted to `references/posting-quality-rubric.md` and shortened to a one-paragraph pointer; Phase 4 points at `generate_tracker_html.py` for the Application Tracker deliverable; "Reading Different Resume Formats" section rewritten to use `parse_resume.py` first with optional sibling-skill fallback.
- **Audit:** 15/15 (0 findings). **Trigger accuracy: 100% (24/24).** **Frozen-v1: 5/5 (no regression).** Description: 1024 chars (spec max).
- **Files produced:** 4 new scripts + 1 new reference + dedupe_postings.py improvement + SKILL.md description rewrite + SKILL.md wiring updates + _meta.json with full iteration history. Total new bundled resources: 5.
- **What didn't get done in this iteration (deliberate scope discipline per Karpathy "surgical changes"):** outcome evals weren't manually graded (they remain "manual review required"); the eval-runner mock is keyword-overlap based so a real `claude`-runner pass would surface different failures and might require another description tweak.

## v2 (2026-05-11) (drastic improvement: harness + scripts + references + real evals)

- **Signal:** User asked to "use [skill-builder] to audit the job-hunter skill and improve that drastically." Audit scored the v1 baseline at 2/15, a single 18 KB SKILL.md file with no scripts, no references, no evals, no `_meta.json`, no continuity docs. The skill content was actually solid (four-phase workflow, tier strategy, ATS awareness) but the entire harness was missing and the SKILL.md inlined 50+ lines of niche-board/state-portal/ATS guidance that bloated context every invocation.
- **Changes:**
  - **Frontmatter:** added `license: MIT` and `metadata:` block (spec_version, loop_type, score placeholders, review-due date).
  - **Content fix, Phase 3 numbering bug:** the original SKILL.md numbered Phase 3 steps `1, 2, 4, 5, 6` (missing 3). Renumbered to `1-5`.
  - **Content fix, all-caps directive:** rewrote `All job links MUST be presented inside a rendered HTML file` as a reasoned constraint explaining *why* (bare URLs don't auto-link in most chat UIs).
  - **New `## When to use this skill` section:** added 12 quoted trigger-context examples and a "Do not use" list covering the adjacent-but-distinct tasks (career coaching, salary negotiation, interview prep, generic resume review). Improves both the skill's own trigger discipline and makes future `retrofit_existing.py` runs synthesize real evals instead of placeholders.
  - **Real trigger evals (`evals/trigger-evals.json`):** replaced auto-generated placeholders with 24 hand-written cases: 16 should_trigger=true (covering all four phases and natural-language phrasings) and 8 should_trigger=false (the explicit out-of-scope cases). Each entry has an `id`, `rationale`, and tests a specific path through the workflow.
  - **Real outcome evals (`evals/outcome-evals.json`):** replaced auto-generated placeholders with 8 hand-written cases tied to the actual workflow contract: Phase 1 gating, Tier 1-4 coverage, HTML deliverable format, keyword gap categories, cover-letter quality, dedup behavior, red-flag handling, and explicit out-of-scope rejection. Each case has 3-6 assertions traceable to specific SKILL.md commitments.
  - **New references (extracted from inlined SKILL.md content):**
    - `references/niche-boards-by-industry.md`, full registry of Tier 2 boards across 9 industries with strengths/notes per board, plus search-syntax fallback guidance.
    - `references/state-workforce-commissions.md`, 50-state + DC registry of official workforce-commission portal URLs and agency names. Includes "how to verify a portal is still live" maintenance guidance.
    - `references/ats-formatting-guide.md`, comprehensive ATS-compatibility guide covering file type, page setup, structure, common breakers, keyword discipline, and a pre-submit checklist. Mentions specific ATS products (Workday, Greenhouse, Lever, Ashby, iCIMS, Taleo).
  - **New scripts (deterministic, offline, dogfood-tested):**
    - `scripts/build_search_queries.py`, given `--role`, `--location`, optional `--industry`/`--companies`, emits a numbered list of Tier 1-4 queries (and role synonyms). Supports `--json`. Knows 9 industries and 15 US states' workforce portals.
    - `scripts/dedupe_postings.py`, collapses duplicate postings from multi-source collection by normalized (company, title, location). Prefers most-direct URL (company career page > aggregator > LinkedIn). Preserves duplicates as `also_seen_on` so users see source breadth.
    - `scripts/extract_ats_keywords.py`, keyword-gap analysis between a JD and a resume. Emits the three-category breakdown (present / matchable / missing) the SKILL.md Phase 3 specifies. Has an adjacency map so "AWS" matches when the resume says "Amazon Web Services", "Kubernetes" matches "K8s", etc. Punctuation-stripping bug surfaced during dogfooding and fixed in the same iteration.
  - **SKILL.md rewiring:** the inlined Tier 1-4 lists in Phase 2 and the inlined keyword-gap explanation in Phase 3 were replaced with short narrative + pointers to the references and scripts. Net effect: SKILL.md gets shorter, but capability *increases* because the scripts make the agent's behavior deterministic and the references can be loaded on demand.
  - **frozen-v1 cohort snapshotted:** `evals/frozen-v1.json` has 5 trigger + 1 outcome entries from the live set, immutable cross-iteration regression detector.
- **Audit score:** 2/15 → 14/15 (remaining: info-level frozen-v1 finding which is now resolved; will re-audit).
- **Files produced:** 3 references + 3 scripts + frozen-v1.json + updated SKILL.md + this CHANGELOG entry.

## v1 (2026-05-11) (retrofit baseline)

- **Signal:** N/A, retrofit by `self-improving-skills` `retrofit_existing.py`. Added bundled-eval scaffolding so future iterations can be measured against a held-out cohort.
- **Change:** Additive scaffolding only, `evals/trigger-evals.json` (template), `evals/outcome-evals.json` (template), `_meta.json`, this CHANGELOG.md. No edits to the existing SKILL.md beyond an optional `metadata:` block addition (backed up if changed).
- **Scores:** baseline not yet measured. Populate after first eval run.
