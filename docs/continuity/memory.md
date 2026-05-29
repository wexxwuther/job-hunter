# Memory, job-hunter

Stable local project memory for this skill. Durable facts that don't fit into decisions,
rejected-ideas, lessons, or discovery-log specifically. NOT a secrets store. NOT a replacement
for user-level memory (2ndBrain).

## Stable facts about the skill itself

- **Current version:** v6.0.0 (FAMILY split; orchestrator `job-hunter/_meta.json version: 6.0.0`). Active source of truth is THIS repo, `E:/Git/job-hunter-public/`, now a family monorepo (6 member dirs, no root SKILL.md). v5.2.0 was the last monolith (archived at tag `v5.2.0-monolith-archive`).
- **Skill name (canonical):** `job-hunter` (lowercase, hyphenated). As of v6.0.0 "job-hunter" names the FAMILY; `job-hunter/` specifically is the orchestrator member. The 6 members install as separate sibling dirs `~/.<harness>/skills/<member>/`. Legacy versioned installs (`job-hunter-vN/`) have all been removed.
- **License:** MIT
- **Spec version:** `agentskills.io 2025-12-18`
- **Loop type:** human-in-the-loop
- **Description character budget:** 1024 max (spec hard limit). At/near limit; re-check after any description edit.
- **Body line budget:** target ≤ 500 lines (per self-improving-skills section 5). Current SKILL.md body is 659 lines after v5/v5.1/v5.2 additions (over the soft target; validate.py emits a WARN, not a failure). Grew from the v4 ~358-line baseline.

## Stable facts about the workflow

- **Four phases**, in order (v4 added a sub-step 0 to Phase 1 and a sub-step 2.5 inside Phase 2):
  1. Understand the user
     - **Sub-step 0 (v4):** check `.job-hunter-profile.md` in the workspace via `scripts/init_profile.py`; first run drops template and asks 5 North-Star questions, subsequent runs read existing answers
     - Read resume; gather role + location + comp floor, gate; don't proceed without
  2. Search for jobs (Tier 1 major boards → Tier 2 niche by industry → Tier 3 local → Tier 4 direct company pages)
     - **Phase 2.5 (v4):** for each posting, fill in 5 sub-scores and run `scripts/score_posting.py` to compute the weighted global + recommendation
  3. Tailor application materials (fetch JD → keyword gap → pick depth → produce resume → optional cover letter)
  4. Prepare for submission (Application Tracker HTML with optional `score_breakdown` per row + per-position summary package)
- **Phase 1 is a gate.** If role/location/comp aren't all specified or confirmed, the skill asks rather than guesses. The cost of asking once is low; the cost of searching with wrong criteria is high.
- **Scoring axes (v4):** five 1-5 sub-scores, `cv_match` (heaviest, 0.35 weight), `comp_vs_target` (0.25), `cultural_signals` (0.20), `posting_legitimacy` (0.20, the ghost-job axis), and `red_flags_penalty` (0-1, applied as multiplier). Weighted-global recommendation buckets: ≥4.0 = apply, 3.5-3.99 = apply_if_specific_reason, <3.5 = skip. The legacy 3-bucket match-strength tag (Strong/Good/Possible) is still rendered for backward compat when `score_breakdown` is absent.
- **Match strength → score mapping:** Strong = 5.0 cv_match, Good = 3.0-3.9, Possible = 2.0-2.9. Anything below ~30% alignment gets dropped, not flagged as Possible.
- **File naming conventions:** `Resume_[CompanyName]_[RoleShorthand].docx`, `CoverLetter_[CompanyName]_[RoleShorthand].docx`, `ApplicationTracker.html`, `tracker.json` (input to the renderer), `.job-hunter-profile.md` (dot-prefixed, lives in user's workspace, never in skill directory).

## Stable facts about the harness

- **Mock runner trigger rule:** ≥2 keywords from the description's Use-when clause must overlap with the prompt's tokenized words. Stopwords excluded. Explicit `/skill-name` invocation also triggers.
- **Trigger-keyword extraction region:** anchored on markers `Use when ` / `Use for ` / `TRIGGER when:` / `TRIGGER when `, stops at the next `do not use` / period / blank line. Content outside this region doesn't count.
- **Frozen cohorts are immutable.** `snapshot_frozen.py` refuses to overwrite. New cohorts auto-increment to `frozen-v(N+1).json`.
- **Audit scoring is out of 15** (full-stack completeness). Includes frontmatter, body discipline, evals presence, bookkeeping (`_meta.json`, CHANGELOG, frozen cohort), continuity stack.

## Stable facts about installed locations

- **Source of truth (v5+, THIS repo):** `E:\Git\job-hunter-public\`, branch `main`, remote `https://github.com/wexxwuther/job-hunter` (PRIVATE). All v5+ edits go here.
- **v4 ancestor (frozen, historical):** `E:\Git\skill-builder-workdir\job-hunter\`, separate git history, no merge path, read-only. (Dual-repo fact: v4 frozen at skill-builder-workdir; v5+ active here.)
- **Plugin-managed original:** `C:\Users\Owner\AppData\Roaming\Claude\local-agent-mode-sessions\skills-plugin\5c05cc04-2463-4046-bba9-caf393e8b23f\e536094f-d1a7-4bf2-b2e6-96280eabdba7\skills\job-hunter\`, READ-ONLY
- **v6.0.0 family installs (CURRENT, verified clean 2026-05-28):** the 6 members are installed as separate sibling dirs under each of the 3 deploy targets — `~/.claude/skills/`, `~/.agents/skills/` (Codex + OpenClaw share this), `~/.hermes/skills/`. Each target has exactly the 6 members; orchestrator `_meta.json` v6.0.0; `resume-tailor/scripts/verify_no_fabrication.py` PRESENT in all 3. The earlier staleness (pre-v5.2.0 installs missing the anti-fabrication script) is RESOLVED — that was the root cause of the "resume optimizer not part of skill set" symptom.
- **Stale installs REMOVED (2026-05-28):** the old `job-hunter-v3` + `job-hunter-v4` dirs (across `.claude`/`.codex`/`.agents`) and the orphaned `~/.codex/skills/job-hunter` are deleted. `~/.codex` is NOT a deploy target (Codex reads `~/.agents`).
- **v4 ancestor (frozen, historical):** still on disk at `E:\Git\skill-builder-workdir\job-hunter\` as read-only source history (not an install).
- **Install procedure (v6.0.0 family):** run `install/install.sh` (macOS/Linux) or `install/install.ps1` (Windows) from THIS repo's root; loops all 6 members into the 3 harness roots. Per-harness guides: `install/claude-code.md`, `install/codex.md`, `install/openclaw.md`, `install/hermes.md`.

## Stable facts about external dependencies

- **Python scripts target 3.10+** (uses `str | None` union syntax, `list[X]` builtin generics, dataclass kw_only patterns elsewhere).
- **DOCX:** `python-docx>=1.1.0` (declared PEP 723 in `parse_resume.py`)
- **PDF:** `pypdf>=4.0.0` (declared PEP 723 in `parse_resume.py`)
- **All other scripts:** stdlib only.
- **`uv` is the recommended runner** when PEP 723 deps need fetching.

## What this skill does NOT do (by deliberate design)

- Does NOT fabricate job listings. Every posting must come from a real web-search result with a real URL.
- Does NOT add skills/roles/accomplishments to a resume that the user doesn't actually have. In v5.2.0 this is a **Hard Gate** (truth-preservation): Phase 3 splits into Mode A (Tighten, zero fabrication) and Mode B (Tailor, rephrase/emphasize, gated by a verification step backed by `scripts/verify_no_fabrication.py`). Web/posting content is treated as untrusted data, not as license to expand what the agent claims about the user.
- Does NOT silently include or exclude red-flag postings, flags them visibly for user choice.
- Does NOT proceed past Phase 1 without role/location/comp confirmed.
- Does NOT generate a cover letter without the user explicitly asking for one.
- Does NOT engage on career-coaching / generic-resume-review / salary-negotiation / interview-prep / post-layoff-support, these are explicitly excluded in the description.
- Does NOT write `.job-hunter-profile.md` anywhere except the user's workspace folder (load-bearing safety test `test_no_sample_profile_in_skill_directory` enforces this; never include a sample profile in the skill directory itself, PII vector).
- Does NOT change posting_legitimacy and cv_match scores together when they have different evidence (they are deliberately orthogonal axes; conflating them is the failure mode v4 step 2 addressed).

## Stable Facts

(canonical-heading anchor for the validator, content lives in the sections above:
"Stable facts about the skill itself", "Stable facts about the workflow", "Stable facts
about the harness", "Stable facts about installed locations", "Stable facts about external
dependencies", "What this skill does NOT do".)

## Notes on terminology

- "Tailoring" means emphasizing and rephrasing what the user actually has, not adding what they don't.
- "ATS-optimized" means structurally parseable (single-column, standard headings, no tables-with-content) plus keyword-aligned to the JD.
- "Match strength" is about the user's *current resume* vs. the JD, not about hireability in general.
- "Source" in a posting card refers to where the posting was found (LinkedIn, Built In, "Texas Workforce Commission", etc.), not the employer.
