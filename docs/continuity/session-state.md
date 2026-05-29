# Session State, job-hunter (PUBLIC REPO, v5+ active source of truth)

**This file lives in `E:\Git\job-hunter-public\`, THE active source of truth for job-hunter.**

**Last updated:** 2026-05-29 (7th member `cover-letter` added; resume-tailor "optimizer" triggers; Claude Code PLUGIN packaging + per-runtime zips; repo now PUBLIC)
**2026-05-29 (post-v6.0.0, same version line):** added the **cover-letter** member (7th family skill), sharpened resume-tailor to trigger on "resume optimizer", packaged the family as a real Claude Code **plugin** (one-install) + per-runtime per-skill zips, and confirmed the GitHub repo is **PUBLIC**. See "2026-05-29 additions" below.
**v5.0.0 shipped:** 2026-05-20 (per-user learning loop)
**v5.0.1 shipped:** 2026-05-20 (decisions_present flag fix)
**v5.1.0 shipped:** 2026-05-20 (follow-up drafting + workspace export/import + non-tech references)
**v5.1.1 shipped:** 2026-05-20 (scan-stale posted-vs-applied_date conflation fix)
**v5.2.0 shipped:** 2026-05-21 (Phase 3 fabrication fix, split Mode A (Tighten/zero-fabrication) / Mode B (Tailor + verification gate); truth-preservation promoted to a Hard Gate; new `scripts/verify_no_fabrication.py`; web-content-untrusted rule) — **last MONOLITH version, now retired**
**v6.0.0 shipped:** 2026-05-28 (FAMILY SPLIT: monolith → orchestrator `job-hunter` + 5 members `career-profile`, `job-search`, `resume-tailor`, `application-tracker`, `outcome-learning`; typed artifact hand-offs via the shared `.job-hunter/` workspace contract; all 16 member scripts byte-identical to the monolith — zero behavior change)
**Current version:** v6.0.0 (family, now **7 members** after the 2026-05-29 cover-letter addition)
**Current scores (2026-05-29):** **244 tests green** (job-hunter 65 + career-profile 25 + job-search 25 + resume-tailor 28 + cover-letter 12 + application-tracker 51 + outcome-learning 35 + installer 3); orchestrator 0 validate ERRORs; all 7 members 0 os-coupling.

## 2026-05-29 additions (7th member + plugin packaging + public repo)

- **`cover-letter` (7th member) added.** Closed a real gap — the family had ZERO cover-letter capability. Drafts a posting-tailored cover letter from the user's confirmed facts (`scripts/draft_cover_letter.py`, deterministic, emits `[CONFIRM: ...]` for any ungrounded slot, never invents), then routes the draft through the family anti-fabrication gate. It **bundles `verify_no_fabrication.py` byte-identical** to resume-tailor's (a test asserts they can't drift). 12 tests, 9 trigger evals, 3 outcome evals, 0 os-coupling. Wired into orchestrator (member table + routing + description), all 6 siblings' `sister_skills`, the workspace-contract producer table (re-synced into all 7 members), install-readiness/family-wiring/orchestrator-meta/installer tests, both installers, and `build_plugin.py`.
- **resume-tailor "optimizer" trigger fix.** "resume optimizer" is NOT a missing skill — resume-tailor already does resume/ATS optimization; it just didn't match the noun "optimizer" (only the verb "optimize"). Added "resume optimizer / resume-optimization tool" to its description + 2 trigger evals. No duplicate skill.
- **Claude Code PLUGIN packaging (the real one-install path).** Discovered (via official docs + `claude` CLI) that Claude Code has NO "upload a zip" feature — it installs a *plugin* that bundles many skills. Added `plugin/` (a local marketplace at `plugin/.claude-plugin/marketplace.json` → the plugin at `plugin/job-hunter/.claude-plugin/plugin.json` + `skills/<7>/`) and `build_plugin.py` (generates `plugin/job-hunter/skills/` from the canonical member dirs; generated tree is gitignored so it can't drift). VERIFIED with `claude plugin install` → "Component inventory: Skills (7)". The plugin is also shipped as `job-hunter-PLUGIN-v6.0.0.zip` for `claude --plugin-dir`.
- **Per-runtime zips + Q catalog.** `Q:/skills/job-hunter/` now holds 7 members × 4 runtimes (`-claude-code`/`-codex`/`-cursor`/`-portable`, built via the canonical `package_skill.py`; codex variant adds `agents/openai.yaml`) = 28 zips + the plugin zip + the offline family-installer bundle = 30 zips, plus `INSTALL.md` (per-app guide). The per-skill zips are for the Claude.ai/Desktop uploader (one skill per zip); the plugin is for Claude Code; the family bundle is the offline CLI installer for any agent.
- **Repo is PUBLIC.** `gh repo view` confirms `visibility: PUBLIC`. The plugin marketplace `add wexxwuther/job-hunter` form now works for end users.

## ⚠ CRITICAL: This IS the v5+/v6 active repo — now a FAMILY MONOREPO

**v5+/v6 source of truth (THIS repo):** `E:\Git\job-hunter-public\`
- Git-tracked, branch `main`, HEAD on commit `31b90d2` (install-readiness fix + guards, 2026-05-28). **Pushed to origin/main (network-verified, 0 ahead / 0 behind).**
- Remote: `https://github.com/wexxwuther/job-hunter` (**PUBLIC** as of 2026-05-29).
- **Layout is now a FAMILY MONOREPO, not a single skill.** Root no longer has a `SKILL.md`. The 6 member dirs are: `job-hunter/` (orchestrator), `career-profile/`, `job-search/`, `resume-tailor/`, `application-tracker/`, `outcome-learning/`, plus `docs/` and `install/`.
- The retired v5.2.0 monolith is recoverable from tag `v5.2.0-monolith-archive` (and `E:/Git/job-hunter-v5.2.0-monolith-archive.zip`).
- All active job-hunter development happens HERE.

**v4 ancestor (frozen, historical):** `E:\Git\skill-builder-workdir\job-hunter\`
- Frozen at v4. No active development. THIS repo is v5+ active.
- The two repos have completely separate git histories. There is NO merge path. Treat the workdir copy as read-only history.

**Why the split:** see `decisions.md` entry "2026-05-20 (v5+), Public repo at `E:/Git/job-hunter-public/` is the new source of truth". TL;DR: public-distribution-shaped repo needs different file structure (LICENSE, README with badges, .github/workflows, install/) that doesn't fit skill-builder-workdir convention.

**What this means for future you:**
- If the user says "edit job-hunter", they mean THIS repo. Verify by checking the working directory. "job-hunter" now means the FAMILY (6 skills), and `job-hunter/` specifically is the orchestrator member.
- **Installs are CLEAN as of 2026-05-28:** all stale `job-hunter-v3`/`job-hunter-v4` copies were removed from all roots, and the orphaned `~/.codex/skills/job-hunter` is gone (Codex reads `~/.agents`, not `~/.codex`). Each of the 3 deploy targets has exactly the 6 v6.0.0 members and nothing stale. See "Where the skill lives".

## 2026-05-28 maintenance pass (this session)

OS-portability + documentation hardening on the v5.2.0 source (no behavior change to the skill):
- **CRLF→LF fix in `scripts/verify_no_fabrication.py`**, the os-coupling guard caught CRLF line endings in the highest-stakes safety script; its `#!/usr/bin/env python3` shebang would fail on macOS/Linux.
- **`.gitattributes` added**, enforces `eol=lf` for `*.py`/`*.sh`/`*.md`/`*.json`/`*.css`/`*.txt`; keeps `*.ps1` as CRLF (Windows-only installer). Prevents CRLF regression.
- **`_meta.json` gained `last_review_due` + `signals_observed`**, for validate/CI compliance.
- **`ats-formatting-guide.md` wired into Phase 3** (Mode A), was an orphan reference; now load-bearing.
- **This continuity stack created**, `docs/continuity/` did not exist in this repo before today (was only in the frozen v4 workdir copy, where it pointed "forward" to here). It now lives here and is written from this repo's perspective.

Landed as commit `6d725cd` (OS fix + .gitattributes). The continuity-stack creation is this session's docs work.

## Where the skill lives right now

- **Source of truth (THIS repo, git-tracked):** `E:\Git\job-hunter-public\`, branch `main`, remote `https://github.com/wexxwuther/job-hunter` (**PUBLIC**). All v6+ edits go here. FAMILY-MONOREPO layout: **7 member dirs** (`job-hunter/` orchestrator + `career-profile/`, `job-search/`, `resume-tailor/`, `cover-letter/`, `application-tracker/`, `outcome-learning/`), each with its own `SKILL.md`, `scripts/`, `references/`, `evals/`, `tests/`, `_meta.json`, `CHANGELOG.md`; plus root `docs/` (this continuity stack + `CUTOVER.md` + `superpowers/`), `install/`, `plugin/` (Claude Code plugin + local marketplace), and `build_plugin.py`. Root `SKILL.md` is GONE by design.
- **Family installers:** `install/install.sh` + `install/install.ps1` loop all 7 members into the 3 harness roots (`~/.claude/skills`, `~/.agents/skills` (Codex + OpenClaw share this), `~/.hermes/skills`); they install offline from the unzipped bundle or clone from GitHub. Per-harness guides: `install/claude-code.md`, `install/codex.md`, `install/openclaw.md`, `install/hermes.md`. **Claude Code's supported one-install path is the PLUGIN** (`/plugin marketplace add wexxwuther/job-hunter` → `/plugin install job-hunter@gdk-skills`), not the installer.
- **LIVE INSTALL STATE (2026-05-28, verified clean):** each of the 3 deploy targets (`~/.claude`, `~/.agents`, `~/.hermes`) has exactly the 6 v6.0.0 family members; orchestrator `_meta.json` reads v6.0.0; `resume-tailor/scripts/verify_no_fabrication.py` is PRESENT in all 3 (this is the fix for the original "resume optimizer not part of skill set" symptom, which was stale installs, not a broken chain). No stale/shadowing copies remain.
- **Catalog (Q:):** `Q:/skills/job-hunter/` has 5 v6.0.0 zips (claude-code, codex, openclaw, hermes, portable; 234,197 bytes each, 91 entries) + `skill.json` (current_version v6.0.0, chainability plugin-bundle, chain.members 6, source_version_hash 67161e9d516c) + README. `Q:/skills/catalog.json` lists job-hunter at current_version v6.0.0, kind skill-family-bundle.
- **v4 ancestor (frozen, historical):** `E:\Git\skill-builder-workdir\job-hunter\`, separate git history, no merge path. Read-only for reference.
- **Plugin-managed original (read-only):** `C:\Users\Owner\AppData\Roaming\Claude\local-agent-mode-sessions\skills-plugin\...\skills\job-hunter\`. Untouched. Invocable as `anthropic-skills:job-hunter`.

> ✅ **Installs are CURRENT (2026-05-28):** the live `job-hunter` family across all 3 harnesses is v6.0.0 and carries `verify_no_fabrication.py` (in the `resume-tailor` member). The old staleness warning (pre-v5.2.0 installs missing the anti-fabrication script) is RESOLVED — that was the root cause of the original symptom and it is fixed.

## How job-hunter reached v5.2.0 (version history)

The skill's most recent shipped state is v5.2.0 (2026-05-21). Highlights since v4:
- **v5.0.0:** per-user learning loop (4 workspace files + `harvest_outcomes.py` + `propose_lessons.py` + `init_workspace.py`; Phase 0 reads, Phase 5 closes the loop; 6 guardrails).
- **v5.1.0:** follow-up drafting (Phase 4.5, `draft_followup.py`), workspace export/import (`export_workspace.py` + `import_workspace.py`), expanded non-tech references.
- **v5.1.1:** scan-stale `posted`-vs-`applied_date` field-conflation fix (new canonical `applied_date` field).
- **v5.2.0:** Phase 3 fabrication fix, split Mode A (Tighten / zero-fabrication) and Mode B (Tailor + verification gate); truth-preservation promoted to a Hard Gate; new `scripts/verify_no_fabrication.py` + `tests/test_verify_no_fabrication.py`; web-content-untrusted rule.

The detailed per-version record is in `CHANGELOG.md` (one level up). The v4-ancestor iteration history below is kept for historical context only.

## v4-ancestor iteration history (historical, from the frozen workdir repo)

Signal: competitive review of `santifer/career-ops` (GitHub). Five capability gaps identified versus job-hunter v3; four folded in over 5 atomic steps with per-step eval gating.

1. **Step 0 (baseline):** ran mock evals against v3 working copy → trigger 24/24 (1.0), audit 15/15. Confirmed `.install.ps1` produces a clean install across three harness paths.
2. **Step 1 (`scripts/score_posting.py` + tests):** deterministic 1-5 scoring across 5 sub-scores with weighted global and recommendation enum. Weights documented inline with rationale (failure-mode #6 mitigation). 23 unit tests including load-bearing safety tests for weight intent. Post-step evals: trigger 24/24, audit 15/15. Commit `cf0df5c`.
3. **Step 2 (ghost-job axis as a separate sub-score):** split `references/posting-quality-rubric.md` into `posting-legitimacy-rubric.md` (NEW, three-tier confidence) + `match-quality-rubric.md` (NEW, severity-graded red flags). Old file converted to stub redirector. Added outcome evals #9 + #10. Post-step evals: trigger 24/24, audit 15/15, outcome 10. Commit `abad905`.
4. **Step 3 (multi-block scoring in HTML tracker):** rewrote `generate_tracker_html.py` with score badge as primary signal, collapsible sub-score breakdown, default sort by weighted_global, filter controls. CSS promoted from inline-string to `assets/templates/tracker.css` per CL43. 23 unit tests including the CL43 drift test. Post-step evals: trigger 24/24, audit 15/15, outcome 10, all 46 tests pass. Commit `c0cda3b`.
5. **Step 4 (North-Star profile capture):** new `scripts/init_profile.py` with init/read/exists subcommands; `.job-hunter-profile.md` lives in the user's workspace (dot-prefixed for privacy). Added Phase 1 sub-step 0 to SKILL.md. Added outcome evals #11 + #12. 23 unit tests including PII-vector-prevention safety test (no sample profile in skill dir) and dot-prefix privacy test. Post-step evals: trigger 24/24, audit 15/15, outcome 12, all 69 tests pass. Commit `4e20b75`.
6. **Step 5 (this commit):** `_meta.json` bumped to v4, CHANGELOG.md prepended with v4 entry, SKILL.md frontmatter updated (`last_iteration`, `last_review_due`), four continuity docs revised against ACTUAL state (this file + compaction-handoff.md + lessons.md + discovery-log.md), `.install.ps1` version bumped v3 → v4, install sync verified across all three harness paths.

## v4-ancestor scorecard (historical)

- **Trigger accuracy:** 100% (24/24), held from v3
- **Audit:** 15/15, held from v3
- **Skill score:** 106/106 (100.0%), first iteration where this was explicitly measured
- **Frozen-v1:** 5/5 (cross-iteration regression detector held)
- **Frozen-v2:** 5/5 (cross-iteration regression detector held)
- **Outcome evals:** 12 (the count at v4; v5+ grew this to 24 in THIS repo)
- **Unit tests:** 69/69 pass at v4 (THIS repo is at 201/201 for v5.2.0)
- **CI check:** all 6 stages green at v4

## Current state (v6.0.0 FAMILY, THIS repo)

- **Version:** v6.0.0 family. Orchestrator `job-hunter/_meta.json`: version 6.0.0, family "job-hunter", family_role "orchestrator", sister_skills = the 5 members.
- **Tests:** 226 family unit tests (per-member sum) + 3 install-readiness guards = 229 green. All 16 member scripts are byte-identical to the retired monolith (git tracked the moves as 100%-similarity renames) → **zero behavioral regression**. The 5 load-bearing `verify_no_fabrication` safety tests moved intact into `resume-tailor`.
- **Validate/audit:** orchestrator validates with 0 ERRORs; all 6 members pass the os-coupling guard (0 findings).
- **OS-clean:** `.gitattributes` enforces LF; `verify_no_fabrication.py` is LF (the CRLF-in-the-safety-script lesson, CL-tracked).
- **Git:** branch `main`, HEAD `31b90d2`, pushed to origin/main (network-verified). Working tree clean.
- **Shipped + deployed:** pushed to GitHub; 5 v6.0.0 zips on `Q:/skills/job-hunter/`; catalog.json updated to v6.0.0; live install redeployed + cleaned across all 3 harnesses.

## What's NOT done yet (next session's work)

| Item | Why it's pending | Priority |
|---|---|---|
| **Tag/release v6.0.0 on GitHub** | a `v6.0.0` *Release* object is not yet cut (tag `v5.2.0-monolith-archive` exists). User controls releases | Medium, user-gated |
| **~~Public-repo visibility flip~~** | DONE 2026-05-29 — repo is PUBLIC (`gh repo view` confirms) | ✅ resolved |
| **Real `claude`-runner pass on routing + outcome evals** | The routing/parity checks used read-through + mock runners; a real Claude invocation can surface different behaviors, especially the orchestrator routing and the fabrication-gate evals | Medium |
| **Remove `posting-quality-rubric.md` stub** | Intentional deprecated-stub redirector (now in the `job-search` member); deletable once nothing references it | Low |
| **First real-user run + harvest** | After 1-2 real v6.0.0 family runs, harvest transcripts (outcome-learning Phase 5) for the next iteration | Medium, opportunistic |

## What I would do first if I picked up this session cold

1. Read this file (session-state.md).
2. Read `compaction-handoff.md` for the full self-contained evidence chain.
3. Read `lessons.md` for traps + `docs/CUTOVER.md` for the archive/recovery path.
4. Verify the family still passes against THIS repo (note: monorepo, no root SKILL.md; test per member):
   ```bash
   cd E:/Git/job-hunter-public
   for m in job-hunter career-profile job-search resume-tailor application-tracker outcome-learning; do
     python -m pytest "$m/tests/" -q
   done   # expect 226 family + 3 install-readiness guards = 229 passed total
   ```
5. Then move to the next pending item (a GitHub `v6.0.0` release tag is the top user-gated one).

## Current Goal

v6.0.0 family (now **7 members**, incl. cover-letter) is complete, tested (244 green), pushed to the PUBLIC GitHub repo, shipped to the Q catalog (30 zips + plugin + INSTALL.md), packaged as a verified Claude Code plugin (Skills (7)), and live across all 3 harnesses. The original "resume optimizer not part of skill set" symptom is fixed (it was stale installs; resume optimization is resume-tailor, now also trigger-matched on the noun). No unprompted work; the only open item is the optional GitHub `v6.0.0` Release object (user-gated).

## Last Known State

v6.0.0 family in THIS repo (7 members as of 2026-05-29): **244 tests green**, orchestrator 0 validate ERRORs, all 7 members 0 os-coupling, latest HEAD `9e6bb19` pushed to origin/main (PUBLIC). Monolith retired and archived (tag `v5.2.0-monolith-archive` + zip). Live installs clean: **7 members per harness**, `verify_no_fabrication.py` present in resume-tailor AND cover-letter, no stale copies. Claude Code plugin verified: `claude plugin install` → Skills (7).

## Next Step

Exact next action: **v6.0.0 family (7 members) is fully shipped + redeployed + clean; repo is PUBLIC; plugin verified at Skills (7). Nothing technical pending.** The only open item is the optional GitHub `v6.0.0` *Release* object (user-gated). Do not cut it without explicit user authorization.

## Blockers

None. All technical work for the v6.0.0 family split, ship, and redeploy is complete and verified.
