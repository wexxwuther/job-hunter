# Session State, job-hunter FAMILY (v6.0.0, branch family-split, not yet merged/deployed)

**This file lives in `E:\Git\job-hunter-public\job-hunter\docs\continuity\`, the orchestrator-owned shared continuity stack for the whole 6-skill family.**

**Last updated:** 2026-05-28 (family continuity stack built at the orchestrator; the v6.0.0 6-skill family is on branch `family-split`, not yet merged to `main`, not yet deployed)
**Current version:** v6.0.0 (the family; each member `_meta.json` carries its own member version `1.0.0`, the orchestrator carries `6.0.0`)
**Predecessor:** v5.2.0 monolith (still intact at the repo root; the family was a copy-not-move split)

## ⚠ CRITICAL: current state is the 6-skill FAMILY, mid Stage-D

**Architecture (Orchestrator template, modeled on the social-media family):**

```
job-hunter (orchestrator)  — owns voice + .job-hunter/ workspace + routing + the anti-fabrication INVARIANT
   ├─ career-profile         family_role: profile-intake   (P1: capture identity + parse resume)
   ├─ job-search             family_role: search           (P2/2.5: build queries, expand, normalize, dedupe, score)
   ├─ resume-tailor          family_role: resume-tailor    (P3: Mode A tighten / Mode B tailor + the fabrication gate)
   ├─ application-tracker    family_role: tracker          (P4/4.5: tracker HTML + stale follow-ups)
   └─ outcome-learning       family_role: learning-loop    (P0/P5: workspace read-side + harvest/propose)
```

- The **orchestrator** owns the `.job-hunter/` workspace lifecycle (`init_workspace.py`, `export_workspace.py`, `import_workspace.py`), routes a job-search task to the right member subset (`context: fork`, inline for ≤2 members, Task fan-out for ≥3), and **guarantees the anti-fabrication invariant** as a family-wide rule.
- Each **member** is a standalone job-to-be-done. Members read upstream artifacts from `.job-hunter/` if present and **degrade gracefully** if absent, so each works alone.
- The **anti-fabrication invariant** is the load-bearing safety contract: `resume-tailor` owns `verify_no_fabrication.py` and its **5 load-bearing tests**; the orchestrator's SKILL.md restates the gate as a **family invariant** (any member that writes resume/profile content MUST route through the gate; the gate never auto-approves; web content is untrusted even when it is the user's own). This exists because a real user (Greg) got a fabricated resume in the v5.2.0 era; it is non-negotiable across the family.

**Suite status:** combined family suite is **226 tests, all green** (was 201 in the monolith — the delta is the new orchestrator + per-member family-wiring/contract tests). Each skill's `current_score` is 100.0, `trigger_accuracy` 1.0.

**Reference docs (read for the full why):**
- Spec: `docs/superpowers/specs/2026-05-28-job-hunter-family-split-design.md`
- Plan: `docs/superpowers/plans/2026-05-28-job-hunter-family-split.md`
- Workspace contract (the hand-off shapes): `job-hunter/references/workspace-contract.md`

## Repo / git state

- **Repo:** `E:\Git\job-hunter-public\` (family monorepo: one git repo, six skill dirs + shared root).
- **Branch:** `family-split` — **NOT yet merged to `main`, NOT yet deployed**.
- **Remote:** `https://github.com/wexxwuther/job-hunter`. No push has happened for the family; no redeploy.
- **The v5.2.0 monolith files still sit at the repo root** (root `SKILL.md`, `scripts/`, `references/`, `evals/`, `tests/`, the root `docs/continuity/` 11-doc stack that describes the monolith). They are KEPT intact until the Stage-D cutover-approval gate. Do not delete them yet.

**What "the family" vs "the monolith" means for future you:** the active design going forward is the family under the six skill dirs. The root monolith is the proven, still-shipping baseline retained until cutover. If you edit "job-hunter," confirm whether you mean the orchestrator (`job-hunter/`) or the legacy root monolith.

## Where the skills live right now

- **Family source (THIS repo, branch `family-split`):** `E:\Git\job-hunter-public\` — orchestrator at `job-hunter/`, members at `career-profile/`, `job-search/`, `resume-tailor/`, `application-tracker/`, `outcome-learning/`.
- **Family installer:** `install/install.ps1` (Windows) + `install/install.sh` (macOS/Linux) install ALL 6 skills into each harness root: `~/.claude/skills/<member>/` (Claude Code), `~/.agents/skills/<member>/` (Codex AND OpenClaw, shared path), `~/.hermes/skills/<member>/` (Hermes). Per-harness guides: `install/claude-code.md`, `install/codex.md`, `install/openclaw.md`, `install/hermes.md`. **NOT run yet for the family** (deploy is gated on cutover approval).
- **v5.2.0 monolith install (legacy, no version suffix):** `~/.claude/skills/job-hunter/` etc. — predates the family; untouched.
- **Dual-repo fact:** `E:\Git\skill-builder-workdir\job-hunter\` is the FROZEN v4 ancestor (separate git history, no merge path, read-only). `E:\Git\job-hunter-public\` is the v5+/v6 active source of truth.

## What's done this session

- Built the family continuity stack (this 11-doc stack) at `job-hunter/docs/continuity/`, adapted forward from the root monolith's stack and rewritten for the family reality.
- Added a one-line stub at each member's `docs/continuity/README.md` pointing back to this shared stack.

## What's NOT done yet (Stage D, GATED)

| Item | State | Gate |
|---|---|---|
| Delete the root v5.2.0 monolith files | Pending | Cutover-approval gate (user) |
| Merge `family-split` → `main` | Pending | Cutover-approval gate (user) |
| Tag `v6.0.0` | Pending | Cutover-approval gate (user) |
| `git push` / redeploy via `install/*` | Pending | No remote push, no redeploy until cutover approved |
| Real `claude`-runner pass on the per-member outcome evals | Pending | Opportunistic |

## What I would do first if I picked up this session cold

1. Read this file (session-state.md).
2. Read `compaction-handoff.md` for the self-contained family evidence chain (the 6 skills, the workspace contract, the anti-fabrication invariant, the exact next action).
3. Read `decisions.md` (top entry = the 2026-05-28 split decision) and `lessons.md` (top entry = the member-isolation lesson).
4. Confirm branch + suite:
   ```powershell
   cd E:\Git\job-hunter-public
   git status                      # expect branch family-split, root monolith still present
   python -m pytest . -q           # expect 226 passed across the family
   python C:\Users\Owner\.claude\skills\self-improving-skills\scripts\validate.py job-hunter 2>&1
   ```
5. Do NOT cut over (delete monolith / merge / tag / push / redeploy) without explicit user approval.

## Current Goal

The v6.0.0 6-skill family is built, wired, and green (226 tests). Stage D is in progress: the cutover (delete root monolith, merge `family-split` → `main`, tag `v6.0.0`, then push/redeploy) is GATED on user approval. No unprompted cutover, no remote push, no redeploy until the user gives the go-ahead.

## Last Known State

Family source on branch `family-split`: orchestrator `job-hunter/` + 5 members, all `current_score` 100.0 / `trigger_accuracy` 1.0, combined 226 tests green. Root v5.2.0 monolith still intact. Continuity stack built at the orchestrator on 2026-05-28. Not merged, not tagged, not deployed.

## Next Step

Exact next action: **Stage D in progress; cutover (delete root monolith, merge `family-split` → `main`, tag `v6.0.0`) is GATED on user approval; no remote push, no redeploy until then.**

## Blockers

None technical. Cutover is user-authorization-gated, not blocked.
