# Session State, job-hunter (PUBLIC REPO, v5+ active source of truth)

**This file lives in `E:\Git\job-hunter-public\`, THE active source of truth for job-hunter.**

**Last updated:** 2026-05-28 (continuity stack created in this repo; OS/docs maintenance pass; v5.2.0 documented from this repo's perspective)
**v5.0.0 shipped:** 2026-05-20 (per-user learning loop)
**v5.0.1 shipped:** 2026-05-20 (decisions_present flag fix)
**v5.1.0 shipped:** 2026-05-20 (follow-up drafting + workspace export/import + non-tech references)
**v5.1.1 shipped:** 2026-05-20 (scan-stale posted-vs-applied_date conflation fix)
**v5.2.0 shipped:** 2026-05-21 (Phase 3 fabrication fix, split Mode A (Tighten/zero-fabrication) / Mode B (Tailor + verification gate); truth-preservation promoted to a Hard Gate; new `scripts/verify_no_fabrication.py`; web-content-untrusted rule)
**Current version:** v5.2.0
**Current scores (v5.2.0):** unit tests 201/201 passing (177 from v5.1.1 + 24 new); trigger evals: 28; outcome evals: 24; CI green on Ubuntu/macOS/Windows × Python 3.10/3.11/3.12

## ⚠ CRITICAL: This IS the v5+ active repo

**v5+ source of truth (THIS repo):** `E:\Git\job-hunter-public\`
- Git-tracked, branch `main`, HEAD on commit `6d725cd` (CRLF→LF + .gitattributes, 2026-05-28).
- Remote: `https://github.com/wexxwuther/job-hunter` (PRIVATE as of this writing, user controls visibility flip).
- Released tags: `v4.0.0`, `v5.0.0`, `v5.0.1`, `v5.1.0`, `v5.1.1` (NOTE: the `v4.0.0` tag here is the initial public-release commit, NOT skill-builder-workdir's v4). v5.2.0 not yet tagged/released as of this writing.
- All active job-hunter development happens HERE.

**v4 ancestor (frozen, historical):** `E:\Git\skill-builder-workdir\job-hunter\`
- Frozen at v4. No active development. THIS repo is v5+ active.
- The two repos have completely separate git histories. There is NO merge path. Treat the workdir copy as read-only history.

**Why the split:** see `decisions.md` entry "2026-05-20 (v5+), Public repo at `E:/Git/job-hunter-public/` is the new source of truth". TL;DR: public-distribution-shaped repo needs different file structure (LICENSE, README with badges, .github/workflows, install/) that doesn't fit skill-builder-workdir convention.

**What this means for future you:**
- If the user says "edit job-hunter", they mean THIS repo. Verify by checking the working directory.
- v4 install at `~/.claude/skills/job-hunter-v4/` still exists on the machine. v5+ public-repo installers write to `~/.claude/skills/job-hunter/` (no version suffix). Both coexist.

## 2026-05-28 maintenance pass (this session)

OS-portability + documentation hardening on the v5.2.0 source (no behavior change to the skill):
- **CRLF→LF fix in `scripts/verify_no_fabrication.py`**, the os-coupling guard caught CRLF line endings in the highest-stakes safety script; its `#!/usr/bin/env python3` shebang would fail on macOS/Linux.
- **`.gitattributes` added**, enforces `eol=lf` for `*.py`/`*.sh`/`*.md`/`*.json`/`*.css`/`*.txt`; keeps `*.ps1` as CRLF (Windows-only installer). Prevents CRLF regression.
- **`_meta.json` gained `last_review_due` + `signals_observed`**, for validate/CI compliance.
- **`ats-formatting-guide.md` wired into Phase 3** (Mode A), was an orphan reference; now load-bearing.
- **This continuity stack created**, `docs/continuity/` did not exist in this repo before today (was only in the frozen v4 workdir copy, where it pointed "forward" to here). It now lives here and is written from this repo's perspective.

Landed as commit `6d725cd` (OS fix + .gitattributes). The continuity-stack creation is this session's docs work.

## Where the skill lives right now

- **Source of truth (THIS repo, git-tracked):** `E:\Git\job-hunter-public\`, branch `main`, remote `https://github.com/wexxwuther/job-hunter` (PRIVATE). All v5+ edits go here. Distribution-shaped layout: `SKILL.md`, `scripts/`, `references/`, `assets/`, `evals/`, `tests/`, `install/`, `.github/`, `_meta.json`, `CHANGELOG.md`, `README.md`, `LICENSE`, `SECURITY.md`, `SUPPORT.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, and (as of 2026-05-28) this `docs/continuity/` stack.
- **Public-repo installers:** `install/install.ps1` + `install/install.sh` deploy whatever is on `main` to `~/.claude/skills/job-hunter/` (no version suffix). Per-harness guides: `install/claude-code.md`, `install/codex.md`, `install/openclaw.md`, `install/hermes.md`.
- **v4 ancestor (frozen, historical):** `E:\Git\skill-builder-workdir\job-hunter\`, separate git history, no merge path. Read-only for reference.
- **v4 installs (still on machine):** `~/.claude/skills/job-hunter-v4/`, `~/.codex/skills/job-hunter-v4/`, `~/.agents/skills/job-hunter-v4/`. Coexist with the no-suffix `job-hunter` install.
- **Plugin-managed original (read-only):** `C:\Users\Owner\AppData\Roaming\Claude\local-agent-mode-sessions\skills-plugin\...\skills\job-hunter\`. Untouched. Invocable as `anthropic-skills:job-hunter`.

> ⚠ **Installed-copy staleness (2026-05-28):** the installed `job-hunter` copies predate v5.2.0 and are MISSING `scripts/verify_no_fabrication.py`. They need a redeploy via `install/install.ps1`. Deferred pending user go-ahead, see "Next Step".

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

## Current state (v5.2.0, THIS repo)

- **Version:** v5.2.0 (`_meta.json`); current_score 100.0, baseline 66.7, trigger_accuracy 1.0
- **Unit tests:** 201/201 passing (177 carried from v5.1.1 + 24 new in v5.2.0)
- **Trigger evals:** 28; **Outcome evals:** 24
- **CI:** green on Ubuntu/macOS/Windows × Python 3.10/3.11/3.12 (`.github/workflows/test.yml`)
- **OS-clean:** `.gitattributes` enforces LF; `verify_no_fabrication.py` CRLF→LF fixed (2026-05-28)
- **Git:** branch `main`, HEAD `6d725cd`. Working tree as of the 2026-05-28 pass had `SKILL.md` + `_meta.json` staged/modified for the v5.2.x doc-wiring (verify with `git status` before trusting).

## What's NOT done yet (next session's work)

| Item | Why it's pending | Priority |
|---|---|---|
| **Re-sync installed copies to v5.2.0** | Installed `job-hunter` copies are STALE, missing `verify_no_fabrication.py`. Need redeploy via `install/install.ps1`. DEFERRED pending user go-ahead as of 2026-05-28 | High, but user-gated |
| **Tag/release v5.2.0** | v5.2.0 is shipped in-repo but not yet tagged on GitHub (latest released tag is v5.1.1). User controls release | Medium |
| **Public-repo visibility flip** | Remote is PRIVATE; user controls the flip to PUBLIC | User-gated |
| **Real `claude`-runner pass on outcome evals** | Mock runner is keyword-overlap-based; real Claude invocation can surface different behaviors, especially for the v5.2.0 fabrication-gate evals | Medium |
| **Remove `posting-quality-rubric.md` stub** | Intentional deprecated-stub redirector (see `_meta.json signals_observed`); can be deleted once nothing references it | Low |
| **First real-user run + harvest** | After 1-2 real v5.2.0 runs, harvest transcripts for the next iteration | Medium, opportunistic |

## What I would do first if I picked up this session cold

1. Read this file (session-state.md).
2. Read `compaction-handoff.md` for the full self-contained evidence chain.
3. Read `lessons.md` for traps (top entry: the CRLF-in-the-safety-script lesson).
4. Verify the skill still scores correctly against THIS repo:
   ```powershell
   python C:\Users\Owner\.claude\skills\self-improving-skills\scripts\ci_check.py E:\Git\job-hunter-public
   python -m pytest E:\Git\job-hunter-public\tests\ -q   # expect 201 passed
   ```
5. Then move to the next pending item from the table above (installed-copy re-sync is the top user-gated one).

## Current Goal

v5.2.0 source is complete, OS-clean, and documented. The next concrete action is re-syncing the stale installed copies to v5.2.0, but that is user-gated. No unprompted work until the user gives the go-ahead.

## Last Known State

v5.2.0 source in THIS repo: 201/201 unit tests, 28 trigger evals, 24 outcome evals, CI green across the matrix, `.gitattributes` enforcing LF, `verify_no_fabrication.py` shebang portable. Continuity stack created in this repo on 2026-05-28. Installed copies are stale (pre-v5.2.0, missing the anti-fabrication script).

## Next Step

Exact next action: **v5.2.0 source is complete + OS-clean + documented; installed copies are STALE (missing `verify_no_fabrication.py`) and need redeploy via `install/install.ps1`, DEFERRED pending user go-ahead as of 2026-05-28.**

## Blockers

None technical. The top pending action (installed-copy re-sync) is user-authorization-gated, not blocked.
