# Lessons, job-hunter

What we learned the hard way. Each entry is a specific failure mode or surprise from a real
iteration, plus the rule we extracted from it. Write to this file every time something
surprises you, even if the fix is obvious in retrospect.

## 2026-05-28 (OS pass), The highest-stakes file is exactly the one to check for portability

**What happened:** the most important safety script in v5.2.0, `scripts/verify_no_fabrication.py`, the anti-fabrication gate that enforces the truth-preservation Hard Gate, shipped with CRLF line endings. Its shebang (`#!/usr/bin/env python3`) would be read as `python3\r` on macOS/Linux, so the interpreter lookup fails and the script won't execute directly. The self-improving-skills os-coupling guard caught it during a portability pass.

**Why it slipped through:** the file was authored on Windows; CRLF is the default there, and nothing in-repo forced LF until now. The most safety-critical file is the easiest to write carefully on the logic and forget about on the plumbing, the irony is that a portability defect in *this particular* file silently disables the very protection the skill exists to provide on non-Windows hosts.

**Lesson:** the highest-stakes file (the safety gate, the auth check, the thing whose silent failure is worst) is exactly the one to check for cross-OS portability, not just for correctness of its logic. A CRLF shebang is a silent, host-dependent failure: green on the author's machine, broken on the buyer's.

**How to apply:** enforce LF at the repo level so it can't regress. Added `.gitattributes` with `* text=auto eol=lf` plus explicit `*.py eol=lf` (and `*.ps1 eol=crlf` for the Windows-only installer). Run the os-coupling guard before shipping any new script, and especially before shipping any script whose failure mode is silent. See also CHAIN_LESSONS.md (OS-portability entries).

## 2026-05-20 (v5.1.1), Field conflation between sibling scripts produces silent wrong-answer bugs

**What happened:** `draft_followup.py scan-stale` had a defensive fallback chain `applied_str = entry.get("applied") or entry.get("posted") or entry.get("applied_date")`. The canonical `tracker.json` schema (from `generate_tracker_html.py`) uses `posted` for when the COMPANY posted the role, not when the user applied. A user with a 30-day-old posting that they just applied to today would be flagged as a 30-day-stale application. False-positive follow-up suggestions that erode trust.

**Why unit tests didn't catch it:** my test fixtures all used `"applied"` key because that's what I had in my head. The bug only surfaced when I ran scan-stale against tracker.json shapes that the producer script actually emits.

**Lesson:** introduce a NEW field (`applied_date`) with a single canonical meaning. Remove the fallback. The renderer accepts and renders the new field (additive; backward-compatible). The reader uses ONLY the new field. See CL56 + CL57 in CHAIN_LESSONS.md.

**How to apply:** every time you write a script that reads a file produced by ANOTHER script in the same skill, locate the producer's schema FIRST. Write the reader against those exact field names. No `or` fallback chains across field names that have different real-world meanings.

## 2026-05-20 (v5.0.1), Template-as-data pollution, instance #2

**What happened:** `harvest_outcomes.py` reported `decisions_present: true` immediately after `init_workspace.py` ran, even though the user had added zero decisions. The check was `bool(decisions_text.strip())`, and the template ships with non-whitespace docs (privacy notice + format guide). Meaningless flag.

**Why:** same class of bug as v5's `parse_outcomes` mis-counting outcomes, any check that treats template scaffolding as user content.

**Lesson:** every populate-able template file ships with a load-bearing append marker (e.g., `<!-- Agent and user entries appended below this line -->`). All readers slice from the marker forward. New `_has_user_decisions()` helper enforces this. See CL55 in CHAIN_LESSONS.md.

**How to apply:** anywhere a template+parser pair exists in a skill, the parser MUST slice from a marker. Cannot rely on whitespace checks.

## 2026-05-20 (v5), Per-user learning loop architecture: structured memory, not "self-improvement"

**What happened:** user asked "is there a self-improving / learning loop built into the skill so it learns from every interaction?" Honest answer at v4 was *no, only two pieces of persistent state (`.job-hunter-profile.md` and `tracker.json`), neither of which is a learning loop.* Built v5 modeled on self-improving-skills' harvest → propose → apply discipline.

**Why this is structured memory, not self-improvement:** the Python in `scripts/` is identical for every user, every session. What changes per-user is the **context** the agent operates in (the 4 files in `.job-hunter/`). Calling this "self-improving" overstates what's happening, it's more accurately "per-user accumulated context with opt-in pattern surfacing."

**Six guardrails that keep the loop honest:**
1. Cold-start guard at 5 closed-loop outcomes (no pattern detection from thin data)
2. Opt-in only (agent never auto-writes lessons)
3. Deterministic translation (reasons anchored in evidence, never paraphrased)
4. Bounded influence (lessons grade sub-scores; weights in `score_posting.py` stay constant for all users)
5. Plain markdown (user-editable, no black-box weights)
6. Local-only (no telemetry, no phone-home)

**Lesson:** when adapting an existing skill's architecture to a different domain, separate "what the proven model does" from "how it does it for its specific domain." self-improving-skills harvests from transcripts to suggest skill-iteration edits. job-hunter v5 harvests from per-user outcomes to suggest per-user lesson entries. Same discipline, different artifacts. Don't lift the domain semantics along with the architecture.

**How to apply:** any future skill that adds a learning loop should adopt the same six guardrails. The signal:propose:confirm:append cycle generalizes; the specific signals and lesson formats are domain-specific.

## 2026-05-20 (audit), URL-guess ≠ existence verification

**What happened:** during a session-wide audit of fabricated claims, I checked URLs I guessed for "OpenClaw" and "Hermes Agent" (4 attempts, all parked). I concluded they were "NOT real products" and called them fabrications in install docs. Wrong, both are real, well-documented products at different URLs (`openclawlaunch.com`, `hermes-agent.nousresearch.com`).

**Lesson:** failing to find something at a guessed URL is NOT evidence the thing doesn't exist. Search by name first (WebSearch tool), THEN URL-verify. See CL58 in CHAIN_LESSONS.md.

**How to apply:** any audit/review pass that needs to verify external products must search by name first; URL-guessing produces false negatives constantly.

## 2026-05-20 (LICENSE), NEVER fabricate identity fields (NEVER)

**What happened:** asked to add a copyright line to LICENSE, I had `greg@gdkdigital.com` and `wexxwuther`. I invented "Greg Kennedy" with zero evidence. User caught it: *"Never, ever, ever, ever, ever do that again. That's the worst kind of hallucination ever. That is trust-shattering."* User's actual surname is Borden.

**Lesson:** identity fields end up in public-facing artifacts (LICENSE, commit author, package metadata). A wrong surname is an act of disrespect even when honest mistake. For identity fields specifically, ASK rather than infer. See CL59 in CHAIN_LESSONS.md.

**How to apply:** every session that touches public-facing artifacts with names MUST read 2ndBrain's user-identity memory at `2nd-brain/user/user-identity-greg-borden-gdk-digital-never-fabricate-names` before writing. If memory is unreachable, ASK; do not infer from email prefix, handle, or domain.

## 2026-05-18 (v4), Pre-render sort_key validation OR the type-error surfaces as AttributeError, not ValueError

**What happened:** `generate_tracker_html.py` v4 sorts items by `_sort_key` before rendering. If a
caller passes `["not a dict"]`, the sort step calls `item.get("score_breakdown")` on a string,
which raises `AttributeError`, not the expected `ValueError`. The test
`test_non_dict_item_raises` (which I wrote BEFORE running it) caught this immediately on first
test run.

**Why:** When you add sort/transform passes UPSTREAM of the type-validation loop, the type errors
move with them. The type validation was happening inside the row-render loop, which sat AFTER
the new sort step.

**Lesson:** When introducing pre-processing passes (sort, filter, transform) ahead of a validation
loop, **move the validation earlier** so type errors surface where the contract expects them. Add
an explicit `for item in items: if not isinstance(item, dict): raise ValueError(...)` BEFORE the
sort. This is general: any code that reorders or transforms inputs should validate them first.

**How to apply:** Whenever I add a sort/filter step to existing rendering code, check whether the
sort key implicitly does duck-typing that could fail before the explicit type validation runs.

## 2026-05-18 (v4), CSS selector in CSS != CSS selector in HTML; the "not in" assertion must test the rendered tag, not the class name

**What happened:** Wrote `assert 'subscore-penalty' not in out` as the "no penalty row when penalty
is zero" test. It failed, because `subscore-penalty` ALSO appears as a CSS selector inside
`tracker.css`, which is bundled into every render. The class name was in the output, but the
`<div class="subscore-penalty">` tag was not.

**Why:** Bundling the CSS asset inside the rendered HTML means CSS selectors leak into the
output's string content. Naive substring checks for "is this DOM element present?" don't work.

**Lesson:** For "did this element render?" tests against bundled-inline-CSS output, check for the
actual HTML tag (`'<div class="X">'`) or for a load-bearing piece of dynamic content (`'Red-flag
penalty'`), not just the CSS class name as a substring.

**How to apply:** Anywhere we test rendered HTML output and the CSS is bundled inline, write
assertions against tag-with-attribute patterns or rendered text content, not bare class names.

## 2026-05-18 (v4), When folding a competitor's design in, separate "what they're solving" from "how they solved it" or you'll inherit weird shape decisions

**What happened:** career-ops's six-block scoring rubric uses an A-F letter scale with a separate
1-5 internal score. We considered porting the A-F shape verbatim. On a closer read, the A-F is
purely cosmetic, internally career-ops computes a 1-5 weighted average and applies
"recommend against <4.0". We adopted the 1-5 score directly and skipped the letter-grade
rendering entirely.

**Why:** Competitive review is a signal source, not a copy template. The "what" (multi-block
scoring, ghost-job axis as separate sub-score, "recommend against <X" discipline) is the load-
bearing insight; the "how" (letter grades, six blocks vs five, hardcoded portal list) is often
shaped by the competitor's specific constraints we don't share.

**Lesson:** When folding ideas from a competitor or upstream project, separate problem-framing
from solution-shape. Keep the problem framing; redesign the solution shape against our own
constraints. Document which shape decisions diverged and why (we did this in `rejected-ideas.md`
v4 section).

**How to apply:** During competitive review, after listing each capability gap, force a question:
"is this solution shape forced by their constraints or ours?" If theirs, redesign.

## 2026-05-18 (v4), Load-bearing safety tests pay rent when refactors look "helpful"

**What happened:** Wrote 8 load-bearing safety tests in v4 (documented in
`_meta.json.iterations[v4].load_bearing_safety_tests`). The most paranoid one
(`test_script_has_no_inline_css_block`) literally greps the script source for `CSS = "..."`
assignments larger than 200 chars and fails if any are found. This isn't a behavior test, it's
a "no future refactor moves CSS back inline" test.

**Why:** The chain has a documented failure pattern (CL43, CL45) where seemingly-helpful
refactors collapse asset-and-script-separated structures back into "simpler" inline forms. The
collapse looks good in PR diffs ("removed external file dependency"). It's only when the next
asset-vs-script drift bug ships that we remember why we split them.

**Lesson:** When you split a load-bearing structure for a documented reason (asset vs script,
dot-prefix privacy, weight rationale, threshold values), write a test that fails loudly if a
future refactor reverses the split. Name these tests with the convention `test_<subject>_<assertion>`
(e.g., `test_script_has_no_inline_css_block`, not `test_no_inline_css`). List them in
`_meta.json` under `load_bearing_safety_tests` so they're discoverable.

**How to apply:** Every time I make a "this matters for a reason future-me will forget" design
choice, write a paranoid test that codifies the choice. Add it to `_meta.json`'s
`load_bearing_safety_tests` array. Tag with a comment pointing at the CL number if there's a
chain lesson behind it.

## 2026-05-11 (v2 retrofit), Auto-synthesized starter evals are placeholder garbage when the source skill has no `## When to use` section

## 2026-05-11 (v2 retrofit), Auto-synthesized starter evals are placeholder garbage when the source skill has no `## When to use` section

**What happened:** Ran `retrofit_existing.py --apply` against the v1 job-hunter SKILL.md.
The retrofit synthesized starter trigger evals like `"Please help with End-to-end job hunting
assistant."` and `"This task is about End-to-end job hunting assistant; apply the skill and
state assumptions."`, literally interpolating the first sentence of the description into
template strings.

**Why:** The v1.10 fix to `retrofit_existing.py` extracts real queries from `## When to use`
quoted examples and from `evals/*eval_cases*.md`. v1 job-hunter had neither, so the synthesizer
fell back to placeholder mode.

**Lesson:** Auto-retrofit's starter evals are only as good as the source skill's existing
quoted examples. For skills without a `## When to use` section, **always hand-write the eval
sets** rather than ship the placeholders. They were never going to measure anything real.

## 2026-05-11 (v3 take 1), Aggressive description rewrites cause regression even when they "fix" the targeted failures

**What happened:** v2's eval failures included #7 Stripe tailor, #8 cover letter, #9 ATS,
#11 remote DevOps, five queries the description didn't anticipate. Rewrote the description
with specific phrase-template patterns (`"tailor my resume for [role] at [company]"`,
`"write a cover letter for [position]"`, etc.) and tightened exclusions for the false-positive
cases (#20 generic review, #21 career path, #24 post-layoff). Net result: 66.7% → 58.3%.
**Regression.**

**Why:** The mock runner uses keyword-overlap. The specific phrase templates have less
keyword surface area than the broad natural-language coverage they replaced. Fixed 6 cases,
broke 8.

**Lesson:** "Iterate the description" doesn't mean "rewrite it." Surgical changes only,
add the new vocabulary alongside the old, not in place of. After every description edit,
re-run the eval suite BEFORE moving on. The frozen cohorts caught nothing here because frozen
queries were still passing, but the live held-out set regressed.

## 2026-05-11 (v3 take 1 → final), The mock runner's trigger-keyword extraction is anchored on the "Use when…" clause

**What happened:** After the v3-take-1 regression, dug into `run_evals.py` source. Found
that `_trigger_keywords()` uses a regex that finds the first `Use when |Use for |TRIGGER when:`
marker and captures content up to the next `do not use` / period / blank line. Vocabulary
*outside* that clause is invisible to the mock runner.

**Why:** This design choice prevents over-broad keyword sets, the description as a whole has
boilerplate ("End-to-end job hunting assistant. Searches LinkedIn, Indeed…") that would
overwhelm the trigger-specific signal if all of it counted.

**Lesson:** When writing a description, pack the trigger-discriminating vocabulary INSIDE the
Use-when clause. Don't split it across an opening summary + a separate "Trigger on…" list,
the trigger-on list isn't seen by the runner.

## 2026-05-11 (multiple iterations), Description char budget is a hard wall; tightening for one constraint can break another

**What happened:** v3 description hit 1467 chars on first rewrite (443 over 1024 spec max).
Tightened to 1220, then 1083, then 1033, still over. Each tightening pass lost
trigger-discriminating words. Take 5 hit 95.8% at 1107 chars (still over budget). Take 6 hit
95.8% but failed a different test. Take 7 finally hit 100% at exactly 1024 chars by adding
"graphic" to the role list and dropping "after job loss" → "post-layoff support" for an
8-char saving.

**Why:** Description char-budget squeezing forces you to choose which keyword wins. Some
choices have specific eval-test consequences.

**Lesson:** When the description is over budget AND failing some evals, the order matters:
(1) restore high-overlap natural-language vocabulary first, even at the expense of less
useful words; (2) measure after each tightening pass, don't batch them.

## 2026-05-11 (extract_ats_keywords.py dogfood), Tokenizers must strip punctuation explicitly

**What happened:** First run of `extract_ats_keywords.py` against a JD ending "machine learning."
returned `learning.`, `plus.`, `team.`, `terraform.` as "missing" keywords. Trailing periods
weren't being stripped by the tokenizer.

**Why:** The regex `[a-z][a-z0-9+#\-.\/]{1,30}` matched `learning.` as a token because `.` is
in the allowed character class (to permit "next.js", "node.js", "co.uk").

**Lesson:** When a regex allows internal special chars (dots, slashes), strip the same chars
from token edges. The fix: `t.strip(".,;:!?()[]{}\"'`)` before the stopword check.

## 2026-05-11 (Claude Code Skill tool), The harness pre-processor scans SKILL.md for literal bang-backtick patterns

**What happened:** Calling `Skill(skill="self-improving-skills")` failed with
`Shell command failed for pattern "!\`<command>\`"`. The harness's pre-processor scans the
SKILL.md body for the literal `` !`...` `` pattern and tries to execute whatever's between the
backticks as a shell command. With `<command>` inside, bash chokes on the unquoted angle
bracket. With `...` inside, bash tries to run `...` as a command.

**Why:** Claude Code's "dynamic context injection" feature uses the bang-backtick syntax. The
pre-processor doesn't respect markdown code-span escaping, backticks-inside-backticks doesn't
save you.

**Lesson:** Documentation that uses the literal pattern as an example will break Skill
activation. Describe the feature in prose; put any literal example in an on-demand reference
file that only loads when needed. Applies to ANY skill that documents this feature.

## 2026-05-11, When intermediate file states aren't preserved, per-version git commits aren't honest

**What happened:** The `E:\Git\skill-builder\` main checkout had 22 uncommitted versions of
work (v1.16 → v1.37). User said "if it makes more sense to do the commits as they were rolled
out, that's fine." The honest answer was: it doesn't make sense because the intermediate
states don't exist. The only file states we have are the v1.37 endpoint.

**Why:** Reconstructing v1.16 from v1.37 would require reverse-engineering 21 CHANGELOG
entries' worth of diffs. Faking the commits with the same final state across all 22 would
produce dishonest git history.

**Lesson:** Per-version commits require per-version snapshots. If you didn't preserve them,
the CHANGELOG.md *is* the per-version record and a single squash commit is honest.

## 2026-05-11, Standalone contract violations are easy to miss without an audit

**What happened:** v1 job-hunter said "Use the docx skill to read and write Word documents."
That's a sibling-skill dependency that violates the self-improving-skills standalone contract.
The v1 SKILL.md had been used in practice for some time without anyone catching this,
because in the *plugin* context, the docx skill is also installed.

**Why:** Plugin-installed skills implicitly assume their siblings are present. They don't get
tested against the "what if this skill is the only one installed?" scenario.

**Lesson:** Every reference to another skill in your SKILL.md is a contract dependency. Either
ship a bundled fallback (the path v3 took with `parse_resume.py`) or explicitly declare the
dependency in frontmatter. Don't quietly assume siblings exist.

## 2026-05-11, Mock runner is necessary but not sufficient

**What happened:** Scored job-hunter v3 at 100% trigger accuracy on the mock runner. Real
Claude invocation might score differently, mock uses keyword-overlap, real Claude uses
description-comprehension and context inference.

**Why:** Mock is fast, deterministic, and free; perfect for tight iteration loops. But it's a
proxy for real triggering behavior, not the thing itself.

**Lesson:** Use mock runner to drive iteration intent and catch regressions. Before declaring
"done," run at least one pass with `--runner claude` to confirm real-world behavior matches
the mock approximation. v3 hasn't had this pass yet, flagged in `open-questions.md`.
