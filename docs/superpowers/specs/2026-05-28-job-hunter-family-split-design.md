# job-hunter Family Split — Design Spec

**Date:** 2026-05-28
**Status:** Approved for planning (architecture + granularity + shared-state ownership approved by user)
**Source:** `E:/Git/job-hunter-public/` (v5.2.0 monolith, public repo, GitHub remote `github.com/wexxwuther/job-hunter`)
**Precedent:** social-media family "Orchestrator template" (`E:/Git/skill-builder-workdir/social-media-orchestrator/` + 9 members); family-operations.md (CL7 3-step establishment); self-improving-skills v1.42 precedents.

---

## 1. Goal

Split the monolithic 659-line, 16-script job-hunter v5.2.0 skill into a **6-skill family**: one orchestrator that owns the user-facing voice + the `.job-hunter/` workspace state + routing, and five member skills that are each a standalone job-to-be-done the orchestrator routes to in whatever combination an invocation needs. Apply the v1.42 precedents (OS-portability enforced, eval-schema, trigger-signal hierarchy, continuity stack) and Opus-4.8 currency to every skill. The working public skill must stay intact until the family is proven and the user approves cutover.

## 2. Architecture — 6 skills, Orchestrator template

```
job-hunter (orchestrator)  — owns voice + .job-hunter/ workspace + routing + the anti-fabrication CONTRACT
   ├─ career-profile         P1: capture identity + parse resume         → .job-hunter/profile.md, parsed-resume text
   ├─ job-search             P2: build queries, expand, normalize, dedupe, score → .job-hunter/postings.json (scored)
   ├─ resume-tailor          P3: tighten (Mode A) / tailor (Mode B) + fabrication gate → Resume_[Co]_[Role].docx (gated)
   ├─ application-tracker    P4/4.5: tracker + stale follow-ups          → .job-hunter/tracker.json → HTML, follow-up drafts
   └─ outcome-learning       P0/P5: workspace lifecycle + harvest/propose learning → proposed LESSONS entries
```

**Routing:** the orchestrator reads the request and invokes the needed subset. "Find jobs and tailor for the top one" → job-search → resume-tailor. "Just tighten my resume" → resume-tailor alone. "Where am I on my applications?" → application-tracker alone. Uses `context: fork` like social-media-orchestrator (route + merge in a clean parent context; inline for ≤2 members, Task fan-out for ≥3).

**Family metadata (CL7, all land in one iteration):** every member's `_meta.json` gets `family: "job-hunter"`, a unique `family_role`, and `sister_skills` listing the other five. The orchestrator's `family_role: "orchestrator"`.

## 3. Member boundaries + script ownership

| Skill | family_role | Scripts (moved from monolith) | Standalone job |
|---|---|---|---|
| job-hunter | orchestrator | init_workspace, export_workspace, import_workspace | route + own workspace + voice |
| career-profile | profile-intake | init_profile, parse_resume | "set up my job-search profile / parse my resume" |
| job-search | search | build_search_queries, expand_role_synonyms, normalize_salary, dedupe_postings, score_posting | "find + score jobs for me" |
| resume-tailor | resume-tailor | extract_ats_keywords, verify_no_fabrication | "tailor/tighten my resume for a role" |
| application-tracker | tracker | generate_tracker_html, draft_followup | "track my applications + draft follow-ups" |
| outcome-learning | learning-loop | harvest_outcomes, propose_lessons | "what's working in my search; learn from outcomes" |

`score_posting.py` is owned by **job-search** (its primary consumer); application-tracker references the *scored postings.json artifact*, not the script, so no script is co-owned (avoids the shared-dependency problem).

## 4. Typed artifact hand-offs (the family contract)

All artifacts live under the shared `.job-hunter/` workspace (orchestrator-owned). Each member reads upstream artifacts if present and degrades gracefully if not (so each works standalone):

- `career-profile` → writes `.job-hunter/profile.md` + parsed resume text.
- `job-search` → reads `profile.md` (for match scoring) → writes `.job-hunter/postings.json` (scored). Degrades: if no profile, scores on explicitly-provided criteria.
- `resume-tailor` → reads parsed resume + (optional) a chosen posting from `postings.json` → writes `Resume_[Co]_[Role].docx`. Degrades: works from a resume the user pastes, no workspace needed.
- `application-tracker` → reads `postings.json` + tailored-resume filenames → writes `.job-hunter/tracker.json` → HTML. Degrades: tracks manually-entered applications.
- `outcome-learning` → reads `tracker.json` outcomes → writes proposed LESSONS (user-confirmed). Degrades: cold-start guard (≥5 closed outcomes, already in harvest_outcomes).

**Path contract:** the `.job-hunter/` schema (filenames + JSON shapes) is documented in a shared `references/workspace-contract.md` that the orchestrator owns and every member references. This is the single source of truth for the hand-off shapes.

## 5. Shared state + the anti-fabrication safety gate (the load-bearing decision)

**Decision: the orchestrator owns the `.job-hunter/` workspace lifecycle AND the anti-fabrication contract is centrally enforced.** Rationale grounded in the v5.2.0 incident: `verify_no_fabrication.py` exists *because a real user (Greg) got a fabricated resume*. It must NOT be bypassable by any current or future member that writes resume content.

Concretely:
- `verify_no_fabrication.py` ships **inside `resume-tailor`** (its only caller) — but resume-tailor's SKILL.md makes the gate a **Hard Gate** (the v5.2.0 framing: imperative, top-of-phase, "you may not write a DOCX until every flagged claim is user-confirmed"), and a **load-bearing test** asserts the gate is never auto-approved (the 5 existing `test_verify_no_fabrication.py` safety tests move with it).
- The orchestrator's SKILL.md documents the anti-fabrication contract as a **family invariant**: any member (now or future) that produces resume/profile content MUST route through resume-tailor's gate. This is the centrally-enforced rule.
- The "web content is untrusted even when it's the user's own" rule (v5.2.0) lives in resume-tailor + is restated as a family invariant in the orchestrator.

## 6. v1.42 precedents + Opus-4.8 currency (applied to all 6)

- **OS-portability:** every member ships LF (the `.gitattributes` covers the whole repo); scripts use pathlib/relative paths (already clean per the os-coupling guard); no member ships a `.ps1`-only install.
- **Eval-schema:** each member's `evals/outcome-evals.json` uses the `{id,prompt,expected_output,files,assertions[{text,kind?}]}` shape; deterministic `kind`s where checkable. The monolith's 24 outcome + 28 trigger evals are partitioned to their owning members + each member gets focused trigger evals.
- **Trigger-signal hierarchy:** each member's description is authored for real-LLM routing first; the orchestrator's description is the broad router surface, members' are sharp single-job surfaces with `Do not use … (use sister-skill)` clauses to manage sibling collisions (career/resume/job all share "job"/"resume" vocabulary — the ~93% sibling ceiling applies; documented as known_overfire where it bites).
- **Continuity stack:** the family shares ONE continuity stack at the orchestrator (the members are co-developed; per-member continuity would be 6× duplication). Members get a minimal stub pointing to the orchestrator's stack.
- **Opus 4.8:** add effort-awareness guidance (a quick resume tighten is low-effort; a full multi-posting search + tailor + track campaign is high-effort/xhigh) where it changes member behavior.

## 7. Repo layout (monorepo, one git repo, multiple skill dirs)

The public repo becomes a **family monorepo** (like social-media-plugin bundles members):

```
E:/Git/job-hunter-public/
├── job-hunter/              orchestrator skill (SKILL.md, scripts/, references/, evals/, docs/continuity/)
├── career-profile/          member skill
├── job-search/              member skill
├── resume-tailor/           member skill
├── application-tracker/     member skill
├── outcome-learning/        member skill
├── install/                 family installer (install.sh + install.ps1) — installs all 6 to the 4 harnesses
├── README.md                family overview + per-member table
├── LICENSE, CONTRIBUTING, SECURITY, CODE_OF_CONDUCT, SUPPORT
└── .github/workflows/       CI runs every member's tests
```

Each skill dir is a complete agentskills.io skill (its own SKILL.md + scripts + evals). The repo root holds the public-distribution files + the family installer. The flat-namespace install names each member by its own `name:` (e.g. `~/.claude/skills/job-hunter/`, `~/.claude/skills/resume-tailor/`, …) — the orchestrator references members by bare name (the agentskills.io flat-namespace convention; falls back gracefully if a member isn't installed).

## 8. Install / distribution across 4 harnesses

The family installer (`install/install.sh` + `install/install.ps1`) loops the 6 skill dirs and installs each into `~/.claude/skills/`, `~/.agents/skills/` (Codex+OpenClaw), and `~/.hermes/skills/` — 6 skills × the harness paths. Cross-OS by construction (the v1.42 portable pattern: Path.home()/derived, LF, no drive letters). `gh skill` documented as the alternative per-skill install path.

## 9. Migration path (keeps the working skill intact)

Staged; the v5.2.0 monolith keeps working until the family is proven:

1. **Branch** `family-split` off `main` (do NOT mutate `main`'s working v5.2.0 until cutover).
2. **Scaffold the 5 members + reshape the orchestrator** on the branch (move scripts per §3, write each SKILL.md, partition evals, wire family metadata, write the workspace-contract reference).
3. **TDD throughout:** every moved script keeps its tests (move test files with their scripts); each member must pass its own suite; the combined family suite ≥ the monolith's 201 tests (no coverage lost). Load-bearing safety tests (esp. the 5 verify_no_fabrication ones) must move intact.
4. **Family wiring verification:** a check (mirroring the wiring-map audit) that every sister_skills reference resolves, every artifact hand-off's producer/consumer exist, the orchestrator routes to all 5 members.
5. **Eval the family:** orchestrator routing evals (does "tailor my resume" reach resume-tailor? does "find + tailor" fan out correctly?) + each member's trigger/outcome evals.
6. **Approval gate:** present the built family for cutover approval. Only then merge `family-split` → `main`, tag a new major version (v6.0.0 — breaking structural change), and (separately, gated) redeploy.
7. The old single-skill `job-hunter` install stays until the family install replaces it; document the transition for existing users in README + CHANGELOG.

**Not pushed to the GitHub remote without explicit approval** (public repo).

## 10. Scope / staging (this is a large build)

Comparable to establishing the social-media family. Staged so each stage is independently verifiable:
- **Stage A:** scaffold orchestrator reshape + workspace-contract reference + family metadata skeleton (no member content yet).
- **Stage B:** members one at a time, each: move scripts+tests, write SKILL.md, partition evals, pass its suite. Order: career-profile → job-search → resume-tailor (most safety-critical) → application-tracker → outcome-learning.
- **Stage C:** family wiring + routing evals + combined-suite parity (≥201 tests) + family installer.
- **Stage D:** continuity/docs/CHANGELOG + v6.0.0 cut + cutover-approval gate.

Each stage ends in a branch commit + a verification gate. No `main` mutation, no remote push, no redeploy until Stage D approval.

## 11. Risks

- **Sibling trigger collisions** (career/resume/job-search all share vocabulary) — managed via sharp Do-not-use clauses + known_overfire docs; accept the ~93% ceiling per CL36.
- **Artifact-contract drift** — mitigated by the single `workspace-contract.md` source of truth + a wiring-verification check.
- **The anti-fabrication gate is the highest-stakes piece** — it moves with resume-tailor, keeps its 5 load-bearing tests, and is restated as a family invariant. Verified before cutover.
- **Public-repo blast radius** — entire build on a branch; `main`'s working v5.2.0 untouched; cutover + remote push are separately gated.
