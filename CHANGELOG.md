# Changelog

One entry per accepted iteration. Lead with the *signal* that motivated the change, not just the change itself.

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
