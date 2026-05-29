# Discovery Log, job-hunter

Where things live on disk + which files are load-bearing for which questions. A future session
looking for "where is X?" should find the answer here before grepping.

## ⚠ THIS is the v5+/v6 source-of-truth repo — now a FAMILY MONOREPO (v6.0.0, 2026-05-28)

job-hunter is developed in THIS repo, `E:\Git\job-hunter-public\` (remote `https://github.com/wexxwuther/job-hunter`, currently PRIVATE). The `skill-builder-workdir/job-hunter/` copy is the frozen v4 ancestor (separate git history, no merge path). See `session-state.md` and `decisions.md` for the full rationale. **Current version: v6.0.0 (family split).**

**Where things live now (v6.0.0 family, THIS repo) — root has NO SKILL.md:**
- Source repo: `E:\Git\job-hunter-public\` (you are here), branch `main`, HEAD `31b90d2` (pushed to origin/main).
- **6 member dirs**, each self-contained (own `SKILL.md`, `scripts/`, `references/`, `evals/`, `tests/`, `_meta.json`, `CHANGELOG.md`):
  - `job-hunter/` — orchestrator (routing surface, context:fork, member table; owns `init_workspace`/`export_workspace`/`import_workspace`; ships the canonical `references/workspace-contract.md`)
  - `career-profile/` — profile-intake (`init_profile`, `parse_resume`)
  - `job-search/` — search+score (`build_search_queries`, `expand_role_synonyms`, `normalize_salary`, `dedupe_postings`, `score_posting`)
  - `resume-tailor/` — tailor (`extract_ats_keywords`, **`verify_no_fabrication`** + its 5 load-bearing safety tests)
  - `application-tracker/` — submit+track (`generate_tracker_html`, `draft_followup`, `assets/templates/tracker.css`)
  - `outcome-learning/` — learning loop (`harvest_outcomes`, `propose_lessons`)
- Workspace contract (single source of truth for typed hand-offs): `job-hunter/references/workspace-contract.md`; a COPY is shipped into all 5 members so each is self-contained post-install.
- Install-readiness guards: `job-hunter/tests/test_install_readiness.py` (3 guards: no monorepo-path sibling refs, every member ships the contract, every member owns the scripts its SKILL.md names).
- Cutover doc: `docs/CUTOVER.md` (archive + E2E/parity + what was removed + recovery).
- Continuity stack: `E:\Git\job-hunter-public\docs\continuity\` (this directory).
- Family installers: `install/install.sh` + `install/install.ps1` (loop 6 members into 3 harness roots), per-harness guides `install/{claude-code,codex,openclaw,hermes}.md`.
- LF enforcement: `.gitattributes`.
- Archive of the retired monolith: tag `v5.2.0-monolith-archive` + `E:/Git/job-hunter-v5.2.0-monolith-archive.zip`.
- Q catalog: `Q:/skills/job-hunter/` (5 v6.0.0 zips + skill.json + README); index `Q:/skills/catalog.json`.
- Local v6 zip backups: `E:/Git/job-hunter-v6.0.0-{claude-code,codex,openclaw,hermes,portable}.zip`.
- Local submission drafts: `E:\Git\job-hunter-submission-drafts.md` (post-public-flip PR drafts).
- Local roadmap: `E:\Git\job-hunter-roadmap.md`.

**Where the frozen v4 ancestor lives (read-only, historical):**
- `E:\Git\skill-builder-workdir\job-hunter\`. Many path/inventory tables in the rest of this document were authored against v4 state and reference that ancestor's layout; they are historically accurate but the v5+ source of truth is THIS repo. v5+ adds the learning-loop scripts (`harvest_outcomes.py`, `propose_lessons.py`, `init_workspace.py`), follow-up/export-import scripts (`draft_followup.py`, `export_workspace.py`, `import_workspace.py`), and `verify_no_fabrication.py` not in the v4 inventory below.

## v6.0.0 family-split discoveries (2026-05-28)

**Diagnosis: "resume optimizer not part of skill set" = STALE INSTALLS, not a broken chain.** Resume optimization is Phase 3 / the `resume-tailor` member; it was never a separate component. The live installs predated v5.2.0 and lacked `verify_no_fabrication.py`. Fix = redeploy, not re-architecture.

**Behavior parity is provable via git rename detection.** All 16 member scripts moved out of the monolith are byte-identical to their originals — `git` recorded the moves as 100%-similarity renames. That's the strongest possible parity evidence: no behavioral regression is possible when the bytes are unchanged. The 5 load-bearing `verify_no_fabrication` safety tests moved intact with their script.

**Post-install cross-member reference trap (caught + fixed).** A member SKILL.md that references a sibling by a monorepo-relative path (e.g. `job-hunter/references/workspace-contract.md`) resolves IN the repo but BREAKS once each member installs as a separate sibling dir at `~/.claude/skills/<member>/`. Fix: ship `workspace-contract.md` into all 5 members + rewrite refs to local + add `test_install_readiness.py` guards so it can't regress. This is the family analogue of "every member must be self-contained on its references."

**Codex reads `~/.agents`, not `~/.codex`.** The 3 real deploy targets are `~/.claude/skills` (Claude Code), `~/.agents/skills` (Codex AND OpenClaw share this), `~/.hermes/skills` (Hermes). The orphaned `~/.codex/skills/job-hunter` was a dead path and was removed.

**Asset dependencies travel with their script.** `init_workspace.py` reads `assets/templates/` → those 4 `.job-hunter` templates had to be copied into the orchestrator's `assets/`. Same pattern: `tracker.css` had to land in `application-tracker/assets/templates/`. A moved script that reads a bundled asset is not self-contained until the asset moves too.

**Test count arithmetic:** authoritative per-member sum is **226** family unit tests; the install-readiness file adds **3** guards = **229** total. (A shell loop briefly flickered 225 vs 226 — a shell-arithmetic artifact, not a real discrepancy; trust the per-member sum.)

## v5.1.1 audit + bug-fix discoveries (2026-05-20)

**Audit context:** ran comprehensive e2e testing of v5.1.0 against multiple scenarios beyond unit tests (release zip integrity, install.sh against live repo, cross-version export/import, real tracker.json schema, CI workflow status). Found 2 real issues:

**Bug found:** `scan-stale` in `draft_followup.py` was conflating `posted` (when company posted role) with the application date. Fixed by introducing `applied_date` as a separate canonical field. See `lessons.md` + `decisions.md` entries dated 2026-05-20 (v5.1.1).

**Cosmetic found:** `_meta.json` iterations array was out of order (v2/v3/v4/v5.1.0/v5.0.1/v5, confusing). Fixed by reordering to chronological.

**Patterns to remember (now also in CHAIN_LESSONS.md as CL55-57):**
- Template-as-data pollution: when a template file ships with format documentation, parsers that scan the file will mis-parse the docs unless they use an explicit append marker. (Bug class hit twice in v5 work.)
- Schema field conflation between sibling scripts: when two scripts share a JSON file, fallback chains like `entry.get("A") or entry.get("B")` produce silent wrong-answer bugs if A and B have different meanings. Use ONE canonical name per concept.
- E2E test against producer-shape, not synthetic fixtures: unit tests pass because you wrote both the code and the fixtures with the same field names. Bugs surface only when consumer-script receives data shaped like what producer-script actually emits.

## v5 architecture discoveries (2026-05-20)

**Source-of-truth for self-improving-skills' continuity stack:** at `~/.claude/skills/self-improving-skills/docs/continuity/` (installed copy, NOT git-tracked). The chain's `_designs/CHAIN_LESSONS.md` is the proper place for cross-skill lessons. job-hunter's continuity stack now lives in THIS repo at `E:/Git/job-hunter-public/docs/continuity/` (created 2026-05-28, adapted forward from the frozen v4 workdir copy). It is self-contained.

**RESOLVED (2026-05-28):** the earlier TODO, "create a `docs/continuity/` stack inside `E:/Git/job-hunter-public/`", is done. The 11-file stack was copied from the v4 workdir copy and rewritten from this repo's perspective. The frozen v4 copy at `skill-builder-workdir/job-hunter/docs/continuity/` is now purely historical.

## career-ops competitive review (v4 signal source)

**Repo:** `https://github.com/santifer/career-ops`, open-source job-search system by Santiago
(now Head of Applied AI somewhere). Built after he manually processed 740+ listings + generated
100+ customized CVs. Published with MIT license + permissive trademark.

**What career-ops does** (full enumeration so future sessions don't re-research):
- A-F grading system across 10 weighted dimensions (Match on CV, North-Star alignment, Comp,
  Cultural signals, Red flags, Global weighted average), internally a 1-5 scale rendered as
  letters; we adopted the 1-5 directly, skipped the letter rendering
- 6 archetypes (LLMOps, Agentic AI, Tech PM, Solutions Architect, Forward Deployed,
  Transformation), narrowly tuned to AI roles; we rejected this for generalist scope
- "Block G" posting legitimacy as a separate 3-tier confidence scale, we adopted as a sub-score
- Portal scanner via Playwright + ATS APIs (Greenhouse/Ashby/Lever/Workday/BambooHR/Teamtailor)
  with `scan-history.tsv` dedup, we rejected (too AI-tier-specific; our web search works for
  any role)
- Per-application PDF rendering via Playwright + bespoke typography (Space Grotesk + DM Sans),
  we rejected (heavy, fragile, our DOCX-first is ATS-equivalent + portable)
- Go + Bubble Tea TUI dashboard with Catppuccin Mocha theme, we rejected (HTML tracker is
  browser-portable, no install)
- 45+ pre-configured companies in `portals.yml` (Anthropic, OpenAI, Mistral, ElevenLabs,
  Deepgram, Retool, Vercel, n8n, Zapier, etc.), we rejected hardcoded list (generalist scope)
- STAR+R story bank with audience-aware mapping (recruiter/hiring-manager/peer-tech/panel),
  we DEFERRED (sibling-collision risk per CL36; revisit if real-user signal warrants)
- Iterative profile building ("first evaluations won't be great. The system doesn't know you
  yet"), we ADOPTED as `.job-hunter-profile.md`
- Quality-over-quantity discipline ("not a spray-and-pray tool"; "below 4.0 = recommend against"),
  we ADOPTED via score_posting.py threshold constants

**career-ops file structure** (so future sessions know what to look for upstream):
```
modes/             # 14 skill modes (apply/batch/deep/interview-prep/latex/pdf/scan/tracker/...)
modes/_shared.md   # Scoring rubric definitions
dashboard/         # Go-based Bubble Tea TUI
batch/             # Parallel worker orchestration
templates/         # CV template, portals.yml, state definitions
config/profile.yml # User profile (their iterative-context insight)
data/, reports/    # Tracking + eval outputs (gitignored)
```

**Ghost-job context:** career-ops cites "~40% of LinkedIn postings show ghost indicators per
recent FTC inquiries." We use this as the rationale for splitting `posting_legitimacy` into
its own sub-score (rather than burying it as a soft red flag).

## Skill file map (current v4 state)

| Area | Path | Purpose |
|---|---|---|
| Entry point | `SKILL.md` | Description (1024 chars at spec max, unchanged in v4), When-to-use, 4-phase workflow with v4 Phase 1 sub-step 0 + Phase 2.5 scoring step, links to all scripts/refs |
| Frontmatter scores | `SKILL.md` frontmatter `metadata:` | `baseline_score: 66.7`, `current_score: 100.0`, `last_iteration: 2026-05-18`, `last_review_due: 2026-08-16` |
| Sidecar scores | `_meta.json` | Same data + full iteration history (v2/v3/v4) with frozen-cohort hold flags + v4 `load_bearing_safety_tests` array |
| Iteration history | `CHANGELOG.md` | v1 baseline + v2 (drastic retrofit) + v3 (eval-driven refinement) + v4 (career-ops competitive review). Per-version detail. |
| Trigger evals | `evals/trigger-evals.json` | 24 cases (16 positive, 8 negative), unchanged in v4 |
| Outcome evals | `evals/outcome-evals.json` | 12 cases (v3 had 8; v4 added #9 ghost-job, #10 full-scoring, #11 first-run profile, #12 second-run profile) |
| Frozen-v1 cohort | `evals/frozen-v1.json` | 5 trigger + 1 outcome, **IMMUTABLE**, snapshotted at v2, holds through v4 |
| Frozen-v2 cohort | `evals/frozen-v2.json` | 5 trigger + 1 outcome, **IMMUTABLE**, snapshotted at v3 description rewrite, holds through v4 |
| Eval results (v3) | `evals/results/iteration-2/`, `iteration-3*/` | v3-era results, gitignored |
| Eval results (v4) | `evals/results/iteration-4/` | `baseline/`, `step-1/`, `step-2/`, `step-3/`, `step-4/`, `final/`, full audit trail of v4 per-step gates, gitignored |
| Pre-retrofit backup | `.retrofit-backups/20260511T175635/SKILL.md` | v1 monolithic SKILL.md, 18 KB single file |

## v4 new files (where things added in iteration v4 live)

| Path | What it does |
|---|---|
| `scripts/score_posting.py` | Deterministic 5-sub-score scoring with weighted global + recommendation enum. Weights documented inline. Entry point for Phase 2.5. |
| `scripts/init_profile.py` | Manages `.job-hunter-profile.md` in user's workspace. Subcommands: init / read / exists. Phase 1 sub-step 0 calls this. |
| `references/posting-legitimacy-rubric.md` | Ghost-job axis. Three-tier confidence scale + signals catalog. Maps to `posting_legitimacy` sub-score. |
| `references/match-quality-rubric.md` | cv_match axis. Red-flag catalog with severity gradations (soft/moderate/severe). Severe red flags feed `red_flags_penalty` multiplier. |
| `references/profile-questions.md` | 5 North-Star questions with rationale per question. |
| `references/posting-quality-rubric.md` | DEPRECATED stub redirector. Points at the two new files. Remove in v5 once nothing references it. |
| `assets/templates/tracker.css` | CSS source of truth for the tracker HTML. Loaded by `generate_tracker_html.py` at render time. **Do not move back inline**, `test_script_has_no_inline_css_block` will fail. |
| `tests/test_score_posting.py` | 23 tests including load-bearing safety (weight intent, threshold values, directional sanity). |
| `tests/test_generate_tracker_html.py` | 23 tests including the CL43 drift test (`test_script_has_no_inline_css_block`, `test_css_asset_loaded_into_output`). |
| `tests/test_init_profile.py` | 23 tests including PII-vector-prevention (`test_no_sample_profile_in_skill_directory`, `test_profile_filename_is_dot_prefixed`). |

## Script inventory (all in `scripts/`)

| Script | What it does | Added in |
|---|---|---|
| `build_search_queries.py` | Tier 1-4 query generation for role+location+industry+companies. Knows 9 industries and 15 state portals. | v2 |
| `dedupe_postings.py` | Collapse duplicates by (company, title, location). URL canonicalization strips 22 tracking params. | v2 (v3 update) |
| `extract_ats_keywords.py` | Keyword gap analysis: present / matchable / missing. Adjacency map for AWS↔Amazon Web Services, K8s↔Kubernetes, etc. Punctuation stripper. | v2 |
| `expand_role_synonyms.py` | 80+ roles across 9 industries. Bidirectional lookup ("RN" → "nurse"). Optional adjacent-role expansion. | v3 |
| `generate_tracker_html.py` | Phase 4 Application Tracker renderer. Self-contained inline CSS, status badges, match tags. | v3 |
| `normalize_salary.py` | Free-text salary → structured numeric. Handles k-suffix, hourly→annual, currency detection. | v3 |
| `parse_resume.py` | DOCX (python-docx) / PDF (pypdf) / MD/TXT/HTML (stdlib) → plain text + best-effort sections. PEP 723 inline deps. | v3 |

## Reference inventory (all in `references/`, load on demand)

| Reference | Used when | Added in |
|---|---|---|
| `ats-formatting-guide.md` | Producing the tailored resume in Phase 3, optimizing for specific ATS products (Workday, Greenhouse, Lever, Ashby). | v2 |
| `niche-boards-by-industry.md` | Phase 2 Tier 2 search planning. 9 industries × 4-10 boards each. | v2 |
| `posting-quality-rubric.md` | Phase 2 borderline judgment calls. Red-flag catalog, match-strength rubric, drop-vs-flag, salary-vs-market check, freshness threshold. | v3 |
| `state-workforce-commissions.md` | Phase 2 Tier 3 search planning for US locations. 50 states + DC, portal URL + agency name. | v2 |

## Continuity stack (this directory)

| File | Read order | Purpose |
|---|---|---|
| `session-state.md` | 1st | Current state, what's done, what's next |
| `compaction-handoff.md` | 2nd | Full evidence chain; designed to be self-contained for cold pickup |
| `reload-protocol.md` | 3rd (if resuming after compaction) | Step-by-step protocol for picking up |
| `decisions.md` | 4th | Durable decisions + rationale + consequences |
| `rejected-ideas.md` | 5th | Approaches NOT taken, with reasons (prevents re-litigation) |
| `lessons.md` | 6th | Specific failure modes from real iterations |
| `memory.md` | 7th | Durable facts that don't fit elsewhere |
| `discovery-log.md` | This file | "Where is X?" lookup table |
| `open-questions.md` | When stuck | Unresolved questions for future sessions |
| `maintenance.md` | Quarterly | Recurring tasks + freshness checks |

## External paths the agent should know

| Path | Significance |
|---|---|
| `C:\Users\Owner\.claude\skills\job-hunter-v3\` | **The installed v3.** Invocable as `job-hunter-v3`. Packaged copy of working-dir state at install time. |
| `C:\Users\Owner\.claude\skills\self-improving-skills\` | The harness used to do all this work (v1.37.1). Scripts here drive audit/validate/retrofit/run-evals/etc. |
| `C:\Users\Owner\AppData\Roaming\Claude\local-agent-mode-sessions\skills-plugin\5c05cc04-2463-4046-bba9-caf393e8b23f\e536094f-d1a7-4bf2-b2e6-96280eabdba7\skills\job-hunter\` | Plugin-managed original v1. READ-ONLY. Invocable as `anthropic-skills:job-hunter`. SHA256 of its SKILL.md: `C9031AB1AB57CDFBD146A4E15838F20F0390E30D387AE2018AB2A145EB9D2724`. |
| `E:\Git\skill-builder\` | self-improving-skills source repo. Main branch HEAD: `c8bf2d9` (bang-backtick fix). |
| `E:\Git\skill-builder-release-v137\self-improving-skills\` | v1.37 release directory; should equal source modulo .claude/ exclusion |
| `E:\Git\skill-builder-20260511-v137.1.zip` | Latest distributable harness zip. SHA256: `2714FE2C46F86441A65BC6CBF60E3E1C75392CA295FFF43A4E18B581E6E55F13` |
| `E:\Git\skill-builder-workdir\` | Parent dir of this skill's working copy. Created as a holding area for working-copy-not-yet-installed skills. |
| `E:\Git\skill-builder-workdir\job-hunter\.git\` | **Local git repo** for the working copy. Branch `main`, HEAD `171347d`, no remote. |
| `E:\Git\skill-builder-workdir\job-hunter-install-pkg\job-hunter\` | Transient packaging staging directory (output of `package_skill.py`). Re-created on each install. Safe to delete. |
