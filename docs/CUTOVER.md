# v6.0.0 Cutover — Monolith → Family

**Date:** 2026-05-28
**What happened:** The single-skill job-hunter v5.2.0 monolith was retired and replaced by the 6-skill job-hunter family (v6.0.0). This file documents what was archived, tested, and removed, so the change is fully auditable and reversible.

## Archive (done BEFORE any deletion — recoverable forever)

The working v5.2.0 monolith is preserved two independent ways:

1. **Git tag** `v5.2.0-monolith-archive` on the pre-cutover `main` HEAD (commit `55463b7`). Recover with:
   ```
   git checkout v5.2.0-monolith-archive
   ```
2. **Zip** `E:/Git/job-hunter-v5.2.0-monolith-archive.zip` (1,427,851 bytes; 89 entries incl. SKILL.md + all 17 scripts). A filesystem copy independent of git.

Plus the prior release zips already on disk: `job-hunter-v5.0.0.zip` … `v5.1.1.zip`, and the v4 ancestor frozen at `E:/Git/skill-builder-workdir/job-hunter/` (tag/commit `8591b33`).

## What was tested before deletion (no-regression gate)

- **Behavior parity:** all **16 scripts** in the family are **byte-identical** to the monolith's (modulo CRLF→LF normalization). The family runs the exact same code, reorganized — so no behavioral regression is possible at the script level.
- **End-to-end (real input):** job-search scored a real posting (4.55 → `apply`); `verify_no_fabrication` caught 14 planted fabrications on a real resume diff (→ `review_required`, `auto_approved: false`); `init_workspace` created `.job-hunter/` with all 4 templates; `generate_tracker_html` rendered a real tracker (6,109 bytes, CSS from the member's own asset).
- **Live routing:** a model read-through of the orchestrator routed all 5 representative scenarios correctly with zero mismatches against the expected routes (one ambiguity — the "set me up and find some roles" onboarding case — was hardened by adding a worked example).
- **Test parity:** combined family suite = **226 tests** (vs the monolith's 201), all green — verified again *after* the monolith was fully removed, proving the family stands alone.
- **OS portability:** 0 os-coupling findings across all 6 members; `.gitattributes` enforces LF; cross-OS family installer (sh + ps1).
- **Validation:** all 6 members report 0 validate ERRORs.

## What was removed

The root-level monolith (now superseded by the 6 member directories):
`SKILL.md`, `scripts/` (16 scripts), `tests/` (9 test files), `evals/`, `references/`, `_meta.json`, and the root `assets/` (its templates + `tracker.css` now live inside their owning members).

## The family (what replaced it)

| Skill | Role | Owns |
|---|---|---|
| `job-hunter` | orchestrator | routing + `.job-hunter/` workspace lifecycle + the anti-fabrication invariant |
| `career-profile` | profile-intake | `init_profile`, `parse_resume` |
| `job-search` | search | `build_search_queries`, `expand_role_synonyms`, `normalize_salary`, `dedupe_postings`, `score_posting` |
| `resume-tailor` | resume-tailor | `extract_ats_keywords`, `verify_no_fabrication` (+ all 5 load-bearing safety tests) |
| `application-tracker` | tracker | `generate_tracker_html`, `draft_followup` |
| `outcome-learning` | learning-loop | `harvest_outcomes`, `propose_lessons` |

Shared artifact contract: `job-hunter/references/workspace-contract.md`.

## NOT done (still gated, require separate approval)

- **No push to the GitHub remote** (`github.com/wexxwuther/job-hunter`).
- **No redeploy** to the installed skill paths (`~/.claude`, `~/.agents`, `~/.hermes`). The installed copies remain at their prior (stale) state until a separately-approved redeploy via `install/install.ps1`.

## Recovery

If the family ever needs to be rolled back to the monolith:
```
git checkout v5.2.0-monolith-archive    # or unzip the archive zip
```
The v6.0.0 family lives on `main` from the merge commit onward; the monolith lives at the `v5.2.0-monolith-archive` tag.
