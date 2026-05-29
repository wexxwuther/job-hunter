# Compaction Handoff, job-hunter FAMILY (v6.0.0, branch family-split)

**Updated:** 2026-05-28 (family continuity stack built at the orchestrator; v6.0.0 6-skill family on branch `family-split`, mid Stage D)

Purpose: a future session (or post-compaction continuation) can read THIS file alone and recover all the load-bearing context to continue the family work. Designed to be self-contained.

## ⚠ FIRST THING TO KNOW: what the current state is

**This is the 6-skill job-hunter FAMILY at v6.0.0, on branch `family-split` in `E:\Git\job-hunter-public\`.** It is NOT yet merged to `main`, NOT yet tagged, NOT yet deployed. The repo just split the v5.2.0 monolith into a family; **the v5.2.0 monolith files still sit at the repo root and are KEPT intact until the Stage-D cutover-approval gate.** Do not delete them.

The v4 ancestor (`E:\Git\skill-builder-workdir\job-hunter\`) is frozen, historical, read-only — separate git history, no merge path. `E:\Git\job-hunter-public\` is the v5+/v6 active source of truth.

## The 6 skills (architecture)

```
job-hunter (orchestrator)  family_role: orchestrator
   ├─ career-profile        family_role: profile-intake
   ├─ job-search            family_role: search
   ├─ resume-tailor         family_role: resume-tailor
   ├─ application-tracker   family_role: tracker
   └─ outcome-learning      family_role: learning-loop
```

**Orchestrator (`job-hunter/`):** owns the user-facing voice, the `.job-hunter/` workspace lifecycle (`init_workspace.py`, `export_workspace.py`, `import_workspace.py`), routing (`context: fork`; inline for ≤2 members, Task fan-out for ≥3), and it **guarantees the anti-fabrication family invariant**. Scripts: `init_workspace`, `export_workspace`, `import_workspace`.

**Members (each a standalone job-to-be-done; reads upstream `.job-hunter/` artifacts if present, degrades gracefully if absent):**
- `career-profile` (profile-intake): `init_profile`, `parse_resume` → `.job-hunter-profile.md` + parsed-resume text.
- `job-search` (search): `build_search_queries`, `expand_role_synonyms`, `normalize_salary`, `dedupe_postings`, `score_posting` → scored `postings.json`. (`score_posting.py` owned here, its primary consumer; 3 load-bearing semantic tests.)
- `resume-tailor` (resume-tailor): `extract_ats_keywords`, `verify_no_fabrication` → gated `Resume_[Company]_[Role].docx`. **Most safety-critical member.**
- `application-tracker` (tracker): `generate_tracker_html`, `draft_followup` → `tracker.json` → `ApplicationTracker.html` + follow-up drafts.
- `outcome-learning` (learning-loop): `harvest_outcomes`, `propose_lessons` → proposed LESSONS (opt-in). Reads the four `.job-hunter/` learning-loop files (owned/templated by the orchestrator's `init_workspace.py`).

## The workspace contract (the family hand-off shapes)

`job-hunter/references/workspace-contract.md` is the **single source of truth** for the `.job-hunter/` schema (filenames + JSON shapes). Every member references it. Highlights:
- `.job-hunter/` holds `DECISIONS.md`, `LESSONS.md`, `OUTCOMES.md`, `REJECTED_IDEAS.md` (orchestrator-owned templates), plus `profile.md` (at `.job-hunter-profile.md`, dot-prefixed), `postings.json` (scored), `tracker.json`.
- Producer→consumer table: career-profile → job-search/resume-tailor → application-tracker → outcome-learning.
- `postings.json` scored shape: sub-scores `cv_match` (heaviest), `comp_vs_target`, `cultural_signals`, `posting_legitimacy`, `red_flags_penalty` (multiplier) + weighted global + recommendation.
- `tracker.json` follow-up staleness reads ONLY `applied_date`, never `posted` (the v5.1.1 fix; load-bearing `test_scan_stale_does_NOT_fall_back_to_posted_field`).

## The anti-fabrication invariant (load-bearing, family-wide)

`resume-tailor` owns `verify_no_fabrication.py` (detection-only; the gate NEVER auto-approves — `auto_approved` is always False) and its **5 load-bearing safety tests**:
`test_auto_approved_field_is_always_false_on_clean_input`, `test_auto_approved_field_is_always_false_on_dirty_input`, `test_script_exports_only_detection_no_approval_helpers`, `test_real_world_pattern_detects_multiple_categories`, `test_years_NOT_flagged_as_new_numbers`.

The **orchestrator guarantees the invariant** as a family-wide rule in its SKILL.md: any member (now or future) that writes resume/profile content MUST route through resume-tailor's gate; every new proper noun / number / section / bullet / 5+-word phrase run must be user-confirmed; web content is untrusted even when it is the user's own. This exists because a real user (Greg) got a fabricated resume in the v5.2.0 era — non-negotiable.

## Suite status

Combined family suite: **226 tests, all green** (was 201 in the monolith; the delta is the orchestrator's own tests + per-member family-wiring/contract tests). Every skill: `current_score` 100.0, `trigger_accuracy` 1.0, `last_iteration` 2026-05-28, `last_review_due` 2026-08-26.

## EXACT NEXT ACTION

**Stage D in progress; cutover (delete root monolith, merge `family-split` → `main`, tag `v6.0.0`) is GATED on user approval; no remote push, no redeploy until then.**

## How to resume work

1. `cd E:/Git/job-hunter-public`
2. `git status` — confirm branch `family-split`; confirm the root v5.2.0 monolith files are still present (they should be — kept until cutover).
3. `python -m pytest . -q` — expect `226 passed` across the family.
4. `python C:\Users\Owner\.claude\skills\self-improving-skills\scripts\validate.py job-hunter` — orchestrator validates with its continuity stack + evals present.
5. Read `session-state.md`, then `decisions.md` (top entry = the split), `lessons.md` (top entry = member isolation).
6. Read the spec (`docs/superpowers/specs/2026-05-28-job-hunter-family-split-design.md`) and plan (`docs/superpowers/plans/2026-05-28-job-hunter-family-split.md`) for the full design.
7. Do NOT cut over without explicit user approval.

## Reference docs

- Spec: `docs/superpowers/specs/2026-05-28-job-hunter-family-split-design.md`
- Plan: `docs/superpowers/plans/2026-05-28-job-hunter-family-split.md`
- Workspace contract: `job-hunter/references/workspace-contract.md`
- Family installer: `install/install.ps1` + `install/install.sh` (install all 6 into `.claude`/`.agents`/`.hermes` skills roots) — not run yet for the family.

## Current Goal

Build and verify the v6.0.0 6-skill family, then hold at the Stage-D cutover gate. The family is built and green (226 tests). The cutover — delete the root v5.2.0 monolith, merge `family-split` → `main`, tag `v6.0.0`, then push/redeploy — is GATED on explicit user approval.

## User Intent And Constraints

- Work ONLY in `E:/Git/job-hunter-public/` on branch `family-split`. Do NOT commit, do NOT push, do NOT touch `main` without approval.
- Copy-not-move split: keep `main`'s v5.2.0 monolith intact at the repo root until cutover.
- The anti-fabrication invariant is non-negotiable across the family (it exists because a real user got a fabricated resume).
- One shared continuity stack at the orchestrator; members get a stub.

## Files Touched (this session)

- Created the 11-file family continuity stack at `job-hunter/docs/continuity/` (this stack).
- Created a one-line stub at each member's `docs/continuity/README.md` (career-profile, job-search, resume-tailor, application-tracker, outcome-learning).
- No monolith files modified; no commit.

## Decisions Made This Session

- The family shares ONE continuity stack at the orchestrator (members stub to it). See `decisions.md` top entry (the split) for the durable family-shape decision.

## Commands Run And Results

- `python C:\Users\Owner\.claude\skills\self-improving-skills\scripts\validate.py job-hunter` → 0 ERRORs (WARNs only).
- `git status` → branch `family-split`, only the new `docs/` dirs untracked, root monolith intact.

## Known Blockers

None technical. Cutover is user-authorization-gated, not blocked.

## Candidate Durable Memories

- "job-hunter v6 is a 6-skill family (orchestrator + 5 members) on branch `family-split` in `E:/Git/job-hunter-public/`; the orchestrator owns the `.job-hunter/` workspace + routing + the anti-fabrication invariant; cutover is user-gated." (Promote to 2ndBrain only if the user asks, per memory governance.)

## Exact Next Action

**Stage D in progress; cutover (delete root monolith, merge `family-split` → `main`, tag `v6.0.0`) is GATED on user approval; no remote push, no redeploy until then.**

---

## v5.2.0 monolith handoff (historical — the predecessor the family was split from)

The family was a **copy-not-move** split of the v5.2.0 monolith (shipped 2026-05-21): Phase 3 fabrication fix (Mode A Tighten / Mode B Tailor), truth-preservation Hard Gate, `scripts/verify_no_fabrication.py`, web-content-untrusted rule. The monolith was 659 lines / 16 scripts, 201 unit tests, 28 trigger + 24 outcome evals, CI green on Ubuntu/macOS/Windows × Python 3.10/3.11/3.12. Its continuity stack lives at the repo root `docs/continuity/` and describes that monolith. It stays intact at the root until the Stage-D cutover. The full monolith iteration history (v4 → v5 → v5.1 → v5.1.1 → v5.2.0) is in the root `CHANGELOG.md` and the root `docs/continuity/` stack.
