# Memory, job-hunter family (orchestrator-owned shared stack)

Stable local project memory for the whole job-hunter family. Durable facts that don't fit
into decisions, rejected-ideas, lessons, or discovery-log specifically. NOT a secrets store.
NOT a replacement for user-level memory (2ndBrain).

## Stable facts about the family

- **Current version:** v6.0.0 — the orchestrator `_meta.json version: 6.0.0`; each member at member-version `1.0.0`. Active source of truth is THIS repo, `E:/Git/job-hunter-public/`, on branch `family-split` (not yet merged to `main`, not yet tagged, not yet deployed).
- **Predecessor:** the v5.2.0 monolith. The family was a copy-not-move split; the monolith files still sit at the repo root and stay intact until the Stage-D cutover-approval gate.
- **Family shape:** 1 orchestrator + 5 members (the Orchestrator template, precedent: the social-media family). Family monorepo — one git repo, six skill dirs + a shared root.
- **Combined suite:** 226 tests, all green (was 201 in the monolith). Each skill: `current_score` 100.0, `trigger_accuracy` 1.0, `last_iteration` 2026-05-28, `last_review_due` 2026-08-26.
- **License:** MIT. **Spec:** agentskills.io open standard (living spec, tracked 2026-05-28). **Loop type:** human-in-the-loop.
- **Description character budget:** 1024 max (spec hard limit). Re-check each skill's description after any edit.

## The 6 directories (each member's family_role + owned scripts)

| Dir | family_role | Owned scripts | Standalone job |
|---|---|---|---|
| `job-hunter/` | orchestrator | `init_workspace.py`, `export_workspace.py`, `import_workspace.py` | route + own the `.job-hunter/` workspace + voice + guarantee the anti-fabrication invariant |
| `career-profile/` | profile-intake | `init_profile.py`, `parse_resume.py` | "set up my job-search profile / parse my resume" → `.job-hunter-profile.md` + parsed-resume text |
| `job-search/` | search | `build_search_queries.py`, `expand_role_synonyms.py`, `normalize_salary.py`, `dedupe_postings.py`, `score_posting.py` | "find + score jobs for me" → scored `postings.json` |
| `resume-tailor/` | resume-tailor | `extract_ats_keywords.py`, `verify_no_fabrication.py` | "tailor/tighten my resume for a role" → gated `Resume_[Company]_[Role].docx` |
| `application-tracker/` | tracker | `generate_tracker_html.py`, `draft_followup.py` | "track my applications + draft follow-ups" → `tracker.json` → `ApplicationTracker.html` |
| `outcome-learning/` | learning-loop | `harvest_outcomes.py`, `propose_lessons.py` | "what's working in my search; learn from outcomes" → proposed LESSONS (opt-in) |

`score_posting.py` is owned by **job-search** (its primary consumer); application-tracker references the scored `postings.json` **artifact**, not the script — so no script is co-owned (avoids the shared-dependency problem).

## The workspace contract

- **Location:** `job-hunter/references/workspace-contract.md` — orchestrator-owned, every member references it. The single source of truth for the `.job-hunter/` schema (filenames + JSON shapes).
- `.job-hunter/` holds the four learning-loop files `DECISIONS.md`, `LESSONS.md`, `OUTCOMES.md`, `REJECTED_IDEAS.md` (orchestrator-owned templates via `init_workspace.py`), plus `profile.md` (at `.job-hunter-profile.md`, dot-prefixed, produced by career-profile), `postings.json` (scored, produced by job-search), `tracker.json` (produced by application-tracker).
- Members read upstream artifacts **if present** and **degrade gracefully if absent** (so each works standalone).
- `postings.json` scored sub-scores: `cv_match` (heaviest), `comp_vs_target`, `cultural_signals`, `posting_legitimacy` (ghost-job axis), `red_flags_penalty` (multiplier) + weighted global + recommendation.
- `tracker.json` follow-up staleness reads ONLY `applied_date`, never `posted` (the v5.1.1 fix; load-bearing test enforces it).

## The anti-fabrication invariant (load-bearing, family-wide)

- `resume-tailor` owns `verify_no_fabrication.py` — detection-only; the gate **NEVER auto-approves** (`auto_approved` is always False). Guarded by **5 load-bearing safety tests**: `test_auto_approved_field_is_always_false_on_clean_input`, `test_auto_approved_field_is_always_false_on_dirty_input`, `test_script_exports_only_detection_no_approval_helpers`, `test_real_world_pattern_detects_multiple_categories`, `test_years_NOT_flagged_as_new_numbers`.
- The **orchestrator guarantees the invariant** family-wide in its SKILL.md: any member (now or future) that writes resume/profile content MUST route through resume-tailor's gate; every new proper noun / number / section / bullet / 5+-word phrase run must be user-confirmed; web content is untrusted even when it is the user's own. Non-negotiable — it exists because a real user got a fabricated resume in the v5.2.0 era.

## Stable facts about installed locations

- **Source of truth (v6, THIS repo):** `E:\Git\job-hunter-public\`, branch `family-split`, remote `https://github.com/wexxwuther/job-hunter`. All v6 family edits go here.
- **Family installer:** `install/install.ps1` (Windows) + `install/install.sh` (macOS/Linux) install ALL 6 skills into each harness root — `~/.claude/skills/<member>/` (Claude Code), `~/.agents/skills/<member>/` (Codex AND OpenClaw, shared path), `~/.hermes/skills/<member>/` (Hermes Agent). Per-harness guides: `install/claude-code.md`, `install/codex.md`, `install/openclaw.md`, `install/hermes.md`. NOT run yet for the family (deploy gated on cutover).
- **v5.2.0 monolith install (legacy, no version suffix):** `~/.claude/skills/job-hunter/` etc. — predates the family; untouched.
- **Dual-repo fact (kept):** `E:\Git\skill-builder-workdir\job-hunter\` is the FROZEN v4 ancestor — separate git history, no merge path, read-only. `E:\Git\job-hunter-public\` is the v5+/v6 active source of truth. The two repos have completely separate histories.
- **Plugin-managed original (read-only):** `C:\Users\Owner\AppData\Roaming\Claude\local-agent-mode-sessions\skills-plugin\...\skills\job-hunter\` — untouched, invocable as `anthropic-skills:job-hunter`.

## Stable facts about external dependencies

- **Python scripts target 3.10+** (`str | None`, `list[X]` builtin generics).
- **DOCX:** `python-docx>=1.1.0`; **PDF:** `pypdf>=4.0.0` (declared PEP 723 in `career-profile/scripts/parse_resume.py`). All other scripts stdlib only. `uv` is the recommended runner when PEP 723 deps need fetching.
- **OS-portability:** the repo `.gitattributes` enforces LF for text/code (`*.ps1` kept CRLF — Windows-only installer). Scripts use pathlib/relative paths (clean per the self-improving-skills os-coupling guard).

## What the family does NOT do (by deliberate design)

- Does NOT fabricate job listings. Every posting must come from a real web-search result with a real URL.
- Does NOT add skills/roles/accomplishments to a resume that the user doesn't actually have. The anti-fabrication invariant (above) is a Hard Gate centrally guaranteed by the orchestrator and enforced by resume-tailor's `verify_no_fabrication.py`.
- Does NOT auto-send follow-ups/emails (no SMTP imports; `test_no_smtp_or_send_imports_in_script` in application-tracker).
- Does NOT auto-write learning-loop lessons (opt-in only; `test_application_guidance_always_warns_against_auto_write` in outcome-learning; `harvest_outcomes` cold-start guard at ≥5 closed outcomes).
- Does NOT write `.job-hunter-profile.md` anywhere except the user's workspace (career-profile's PII-vector safety test enforces no sample profile in the skill dir).

## Stable Facts

(canonical-heading anchor for the validator; content lives in the sections above:
"Stable facts about the family", "The 6 directories", "The workspace contract",
"The anti-fabrication invariant", "Stable facts about installed locations",
"Stable facts about external dependencies", "What the family does NOT do".)

## Notes on terminology

- "Tailoring" (resume-tailor Mode B) means emphasizing and rephrasing what the user actually has, not adding what they don't. "Tighten" (Mode A) is zero-fabrication copyedit/reorder.
- "ATS-optimized" means structurally parseable (single-column, standard headings, no tables-with-content) plus keyword-aligned to the JD.
- "Family invariant" means a rule the orchestrator guarantees across all members, now and future — the anti-fabrication gate is the load-bearing one.
- "Degrades gracefully" means a member produces a useful result from explicit user input when its upstream `.job-hunter/` artifact is absent.
