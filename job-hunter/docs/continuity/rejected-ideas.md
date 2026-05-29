# Rejected Ideas, job-hunter family (orchestrator-owned shared stack)

Approaches we considered and decided against, with the reason and a reconsider-if trigger.
Recording these prevents future sessions from re-litigating settled debates and re-spending
effort on paths that already turned out badly. This is the shared rejected-ideas log for the
whole family (orchestrator + 5 members). Entries below were recorded on the v5.2.0 monolith and
its v4 ancestor; they remain settled for the family (e.g. the rejection of letter grades, the
hardcoded portal list, and Playwright PDF rendering still hold for the **job-search** /
**resume-tailor** members).

## 2026-05-18 (v4), Bundle Playwright + Chromium for per-application PDF rendering

**Rejected:** Adopting career-ops's approach of rendering CV PDFs via Playwright with
bespoke typography (Space Grotesk + DM Sans).

**Why rejected:** Bundling a 200MB+ Chromium dependency into the skill is heavy and
fragile across OS/architectures. job-hunter's DOCX-first approach (with PDF as an
optional sibling-skill output) is ATS-equivalent for the keyword-matching purpose, more
portable, and runs without an install step. The typography polish doesn't change ATS
scoring.

**Reconsider if:** A real-user signal emerges that DOCX export is breaking ATS parsing,
or that visual polish materially affects callback rates for at least one professional
category (designers, executives, etc.). Could ship as a separate, opt-in sibling skill
rather than folding into job-hunter core.

## 2026-05-18 (v4), Go + Bubble Tea TUI dashboard

**Rejected:** Adopting career-ops's Bubble Tea + Catppuccin Mocha TUI for pipeline
browsing.

**Why rejected:** Requires a Go binary install. job-hunter's HTML tracker renders the
same data with no install, opens in any browser, emails portably, works on
phones/tablets. The interactive sort/filter UI added in v4 step 3 closes most of the
TUI's UX advantage anyway.

**Reconsider if:** A user explicitly wants a terminal-native workflow AND the HTML
tracker's interactive controls turn out to be a regression for power users.

## 2026-05-18 (v4), Hardcoded portal list (45 companies via portals.yml)

**Rejected:** Maintaining a registry of 45+ AI-tier companies (Anthropic, OpenAI,
Mistral, ElevenLabs, etc.) with `enabled` flags and ATS endpoints.

**Why rejected:** Breaks the generalist scope. job-hunter is designed to work for
nurses, teachers, welders, lawyers, designers, not just AI engineers. A hardcoded list
becomes stale within months (companies change ATS providers, get acquired, change URL
schemes) and biases the skill's recommendations toward whatever's on the list. The
tier-1-through-4 web search already covers any role; users with target companies pass
them via `--companies` on the query builder.

**Reconsider if:** A signal emerges that users want repeated scanning of the SAME set of
companies (i.e., a watch list, not a search). This would be a feature add, not a
replacement for the existing search behavior.

## 2026-05-18 (v4), Slash-command UX (`/career-ops scan`, `/career-ops batch`)

**Rejected:** Adopting career-ops's slash-command-driven UX.

**Why rejected:** Per the harness's section §1 (pick-the-primitive), Agent Skills and
slash commands are different primitives. job-hunter is correctly an Agent Skill,
auto-activates on natural-language queries via the description's Use-when clause. Slash
commands are for deterministic shortcuts where the user knows exactly what they want;
job-hunter's interactive 4-phase workflow is the opposite shape.

**Reconsider if:** Never. This is a primitive-choice question, not a feature one.

## 2026-05-18 (v4), Interview prep Phase 5 (STAR+R story bank)

**Deferred (not rejected):** Adding career-ops's audience-aware STAR+R story bank as a
Phase 5 after submission.

**Why deferred:** The trigger surface would need to gain "interview", "STAR",
"behavioral", "prep" keywords. CL36 documents the ~93% sibling-collision ceiling for
proactive/reactive sibling pairs in the same domain. Other interview-prep skills exist
in the catalog; adding these to job-hunter's description would compete for activation.
The deferred-not-rejected status is because the UX argument FOR it is real (the data
needed for STAR+R generation, CV + JD + tailored bullets, already lives in
job-hunter's workflow).

**Reconsider if:** Real-user signals show users repeatedly asking job-hunter for
interview prep after Phase 4. If signal is strong, the right answer is probably a new
skill that takes job-hunter's tracker.json as input rather than a Phase 5 inside
job-hunter.

## 2026-05-18 (v4), Letter-grade rendering (A through F)

**Rejected:** Adopting career-ops's A-F letter-grade rendering for the weighted-global
score.

**Why rejected:** career-ops's A-F is purely cosmetic; internally they compute a 1-5
score with the same "below 4.0 = recommend against" semantics we adopted directly. The
letter grades add a rendering layer without adding information. Numeric scores are also
more legible when sorted, filtered, and aggregated (which is what the v4 tracker UI
does).

**Reconsider if:** A user explicitly asks for letter grades, in which case it's a
2-line CSS + render change.

## 2026-05-11, Edit the plugin-managed original directly

**Rejected:** Modifying
`C:\Users\Owner\AppData\Roaming\Claude\local-agent-mode-sessions\skills-plugin\...\skills\job-hunter\SKILL.md`
in place.

**Why rejected:** The plugin directory is managed by Claude's plugin system. Edits get
silently overwritten on next plugin sync, producing zero durable change but feeling like
progress. Worse, plugin integrity hashes might break.

**Reconsider if:** Anthropic publishes documented support for in-place plugin overrides AND
the user explicitly authorizes the risk. Otherwise: never.

## 2026-05-11, Per-version git commits when intermediate states aren't preserved

**Rejected:** Faking 22 per-version commits in `E:\Git\skill-builder\` for v1.16 → v1.37.

**Why rejected:** The intermediate file states for v1.16 through v1.36 were never written to
disk, only the final v1.37 state existed in the working tree. The only ways to fake
per-version commits would be: (a) reconstruct each intermediate state from the CHANGELOG
(impossible, diffs aren't published), or (b) use the same final state across all 22 commits
(dishonest history; future bisect would lie).

**Reconsider if:** Future iterations preserve intermediate snapshots (e.g., a script that
auto-commits after each successful eval pass). Then per-version commits become natural rather
than fabricated.

## 2026-05-11, Auto-generated trigger evals as starter content

**Rejected:** Shipping the auto-synthesized evals from `retrofit_existing.py` without manual
review.

**Why rejected:** v1 job-hunter had no `## When to use` section, so the retrofit synthesizer
fell back to placeholder mode. Output: queries like `"Please help with End-to-end job hunting
assistant."` that test nothing about the actual skill. Mock-running those would produce
meaningless "scores."

**Reconsider if:** The source skill has `## When to use` with quoted examples (v3 now does)
or has an `evals/*eval_cases*.md` file with real Prompt/Pass-criteria blocks. In those cases
the auto-synthesis pulls real queries and is acceptable as a starter.

## 2026-05-11, Description tightening by removing the broad natural-language vocabulary

**Rejected:** v3 take 1's description rewrite that replaced v2's broad Use-when clause
("Use whenever the user mentions job searching, finding jobs…") with a narrow phrase-template
list ("Trigger on 'find me [role] jobs', 'tailor my resume for [role] at [company]'…").

**Why rejected:** Caused regression (66.7% → 58.3%) because the mock runner uses
keyword-overlap, and phrase templates have less surface area than broad natural-language
vocabulary. The fix was to MERGE the broad and specific patterns inside the Use-when clause,
not replace one with the other.

**Reconsider if:** A future Claude-runner pass (vs. mock) demonstrates that real Claude
triggers correctly on narrow phrase patterns alone. The mock-runner constraint may not bind
real behavior.

## 2026-05-11, Keep red-flag detection + match-scoring inline in SKILL.md

**Rejected:** Leaving the 14 lines of red-flag detection guidance and the 8 lines of match-
scoring rubric inline in Phase 2 of SKILL.md.

**Why rejected:** They added ~25 lines that load on every skill activation but are only used
when the agent is making a borderline judgment call about a posting. Per the skill-authoring
"body discipline" principle (SKILL.md section 5: "Challenge each paragraph: does this justify
its token cost?"), this content belonged in a reference loaded on demand.

**Reconsider if:** Token economics change such that the cost of an extra reference-file load
exceeds the cost of always-loaded inline content. (Unlikely in current Claude pricing.)

## 2026-05-11, Drop `extract_ats_keywords.py` because it has a punctuation bug

**Considered briefly, then rejected:** When the punctuation-stripping bug surfaced during
v2 dogfooding (`terraform.`, `learning.`, etc. showing up as missing keywords), one option
was to mark the script unreliable and remove it from the SKILL.md wiring.

**Why rejected:** The script's *core logic* (adjacency-map matching, three-category
breakdown, top-N keyword scoring) was correct, only the tokenizer needed a one-line fix.
Removing the script would lose the deterministic keyword-gap capability the skill needs.

**Reconsider if:** A more fundamental flaw surfaces, e.g., the adjacency map produces
materially wrong classifications on real resumes. (Not the case as of v3.)

## 2026-05-11, Install v3 to the global skills directory in this session

**Rejected:** Copying `E:\Git\skill-builder-workdir\job-hunter\` to
`C:\Users\Owner\.claude\skills\job-hunter\` (or `~/.agents/skills/`) without explicit user
authorization.

**Why rejected:** Two reasons. (1) Risk: shadowing or replacing the plugin-managed
`anthropic-skills:job-hunter` has consequences (plugin updates may complain, user expectations
may differ) that need explicit user choice. (2) Scope: user asked us to refine the skill, that
work is complete. Install is a separate, explicit action.

**Reconsider if:** User explicitly requests global install AND specifies the install target
(`~/.claude/skills/`, `~/.agents/skills/`, or both). Then proceed with backup + verification
just like we did for self-improving-skills.
