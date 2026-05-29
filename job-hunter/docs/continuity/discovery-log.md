# Discovery Log, job-hunter family (orchestrator-owned shared stack)

Where things live on disk + which files are load-bearing for which questions. A future session
looking for "where is X?" should find the answer here before grepping.

## ⚠ THIS is the v6 family source-of-truth repo (split recorded 2026-05-28)

job-hunter v6 is the **6-skill family** developed in THIS repo, `E:\Git\job-hunter-public\`
(remote `https://github.com/wexxwuther/job-hunter`), on branch **`family-split`** (not yet
merged to `main`, not yet tagged, not yet deployed). The v5.2.0 monolith files still sit at the
repo root and stay intact until the Stage-D cutover-approval gate. The `skill-builder-workdir/job-hunter/`
copy is the frozen v4 ancestor (separate git history, no merge path). See `session-state.md`
and `decisions.md` for the full rationale. **Current version: v6.0.0.**

## Family file / capability map (the 6 dirs + which scripts each owns)

| Dir | family_role | Owned scripts | Notable references / assets | Produces |
|---|---|---|---|---|
| `job-hunter/` | orchestrator | `init_workspace.py`, `export_workspace.py`, `import_workspace.py` | `references/workspace-contract.md` (the family hand-off SoT), this continuity stack | the `.job-hunter/` workspace + routing + merged result |
| `career-profile/` | profile-intake | `init_profile.py`, `parse_resume.py` | `references/profile-questions.md` | `.job-hunter-profile.md` + parsed-resume text |
| `job-search/` | search | `build_search_queries.py`, `expand_role_synonyms.py`, `normalize_salary.py`, `dedupe_postings.py`, `score_posting.py` | `references/niche-boards-by-industry.md`, `state-workforce-commissions.md`, `match-quality-rubric.md`, `posting-legitimacy-rubric.md` | scored `postings.json` |
| `resume-tailor/` | resume-tailor | `extract_ats_keywords.py`, `verify_no_fabrication.py` | `references/ats-formatting-guide.md` | gated `Resume_[Company]_[Role].docx` |
| `application-tracker/` | tracker | `generate_tracker_html.py`, `draft_followup.py` | `assets/templates/tracker.css` (CSS SoT, never inline) | `tracker.json` → `ApplicationTracker.html` + follow-up drafts |
| `outcome-learning/` | learning-loop | `harvest_outcomes.py`, `propose_lessons.py` | `references/learning-loop-guide.md` | proposed LESSONS (opt-in) |

`score_posting.py` is owned by **job-search** (its primary consumer); application-tracker
references the scored `postings.json` artifact, not the script — so no script is co-owned.

## The workspace contract (where the hand-off shapes live)

- **`job-hunter/references/workspace-contract.md`** — orchestrator-owned, every member references it. Single source of truth for the `.job-hunter/` directory layout, the producer→consumer table, the `postings.json` scored shape, the `tracker.json` shape (incl. the `applied_date`-only follow-up-staleness rule), and the anti-fabrication invariant statement.

## The anti-fabrication invariant (where it's enforced)

- **Script:** `resume-tailor/scripts/verify_no_fabrication.py` (detection-only; `auto_approved` always False).
- **Tests:** `resume-tailor/tests/test_verify_no_fabrication.py` — the 5 load-bearing safety tests (listed in `resume-tailor/_meta.json` under `load_bearing_safety_tests`).
- **Family-wide statement:** the orchestrator's `job-hunter/SKILL.md` restates the gate as a family invariant; the workspace-contract restates it too.

## The family installer (where deploy happens)

- **`install/install.ps1`** (Windows) + **`install/install.sh`** (macOS/Linux) — install ALL 6 skills into each harness root: `~/.claude/skills/<member>/` (Claude Code), `~/.agents/skills/<member>/` (Codex AND OpenClaw, shared path), `~/.hermes/skills/<member>/` (Hermes). Members list: `job-hunter` (orchestrator), `career-profile`, `job-search`, `resume-tailor`, `application-tracker`, `outcome-learning`.
- Per-harness guides: `install/claude-code.md`, `install/codex.md`, `install/openclaw.md`, `install/hermes.md`. Installer self-test: `install/test_installer_targets.py`.
- **Not run yet for the family** (deploy gated on cutover approval).

## Where the design lives

| Doc | Path |
|---|---|
| Design spec | `docs/superpowers/specs/2026-05-28-job-hunter-family-split-design.md` |
| Implementation plan | `docs/superpowers/plans/2026-05-28-job-hunter-family-split.md` |
| Family workspace contract | `job-hunter/references/workspace-contract.md` |
| This shared continuity stack | `job-hunter/docs/continuity/` |
| Member continuity stubs | `<member>/docs/continuity/README.md` (point back here) |

## Continuity stack (this directory, shared by the family)

| File | Read order | Purpose |
|---|---|---|
| `session-state.md` | 1st | Current family state, what's done, what's next (Stage D / cutover gate) |
| `compaction-handoff.md` | 2nd | Full self-contained family evidence chain (6 skills, contract, invariant, next action) |
| `reload-protocol.md` | 3rd (if resuming after compaction) | Step-by-step pickup protocol |
| `decisions.md` | 4th | Durable decisions + rationale (top = the split) |
| `rejected-ideas.md` | 5th | Approaches NOT taken |
| `lessons.md` | 6th | Specific failure modes (top = member-isolation) |
| `memory.md` | 7th | Durable family facts that don't fit elsewhere |
| `discovery-log.md` | This file | "Where is X?" lookup table |
| `open-questions.md` | When stuck | Unresolved questions |
| `maintenance.md` | Quarterly | Recurring tasks + freshness checks |

## The v5.2.0 monolith (predecessor, still at the repo root until cutover)

The root still carries the monolith: root `SKILL.md`, `scripts/` (16 scripts), `references/`,
`assets/`, `evals/` (28 trigger + 24 outcome), `tests/` (201 unit tests), and the root
`docs/continuity/` 11-doc stack that describes the monolith. These are KEPT intact until the
cutover-approval gate. The monolith's iteration history (v4 → v5 → v5.1 → v5.1.1 → v5.2.0) is in
the root `CHANGELOG.md` and the root continuity stack. The family carved its scripts/references
out of this monolith via copy-not-move.

## Dual-repo / external paths the agent should know

| Path | Significance |
|---|---|
| `E:\Git\job-hunter-public\` | **The v5+/v6 active source of truth.** Family on branch `family-split`; monolith at root. |
| `E:\Git\skill-builder-workdir\job-hunter\` | **Frozen v4 ancestor.** Separate git history, NO merge path, read-only/historical. |
| `~/.claude/skills/job-hunter/` (+ codex/openclaw/hermes) | Legacy v5.2.0 monolith install (no version suffix). Predates the family; untouched. |
| `C:\Users\Owner\AppData\Roaming\Claude\local-agent-mode-sessions\skills-plugin\...\skills\job-hunter\` | Plugin-managed original v1. READ-ONLY. Invocable as `anthropic-skills:job-hunter`. |
| `C:\Users\Owner\.claude\skills\self-improving-skills\` | The harness that drives audit/validate/run-evals for this work. |
