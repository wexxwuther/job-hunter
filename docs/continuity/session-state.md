# Session State, job-hunter (PUBLIC REPO, v5+ active source of truth)

**This file lives in `E:\Git\job-hunter-public\`, THE active source of truth for job-hunter.**

**Last updated:** 2026-10-18 (first live outcome-eval run: interview-prep 6 evals, `f02767a`; gate trailing-comma fix `cec398d`; earlier the same day: live routing 16/16, runner fix `24eea6a`, interview-prep v1.0.0 `c01d73c`)

## 2026-10-18 live interview-prep outcome evals (commits `cec398d`, `f02767a`)

- First real-harness run of ANY family outcome eval (earlier ones were only read through
  or mock-scored; the old `run_evals.py --runner claude` named in open-questions no longer
  exists). New `tools/run_outcome_evals.py` + `tools/outcome-scenarios/interview-prep.json`:
  fresh fictional workspace per case (Pat Doe / Globex / Initech, built under the
  `--out-dir`, outside the repo), each user turn through `claude -p` (turn 2 via
  `--resume`), `--settings {"disableAllHooks": true}`, tools limited to Skill, Read,
  Write, Edit, Glob, Grep, Bash(python/mkdir/ls), WebSearch, WebFetch, `--max-budget-usd 5`
  per call. Grades the eval's assertions over assistant text + tool inputs; manual verdict
  per case from `<out-dir>/manual-review.json`. `--invoke-skill` prefixes turn 1 with
  `/interview-prep`. 14 tests in `tools/test_run_outcome_evals.py`; 12/12 runner mutants
  killed (`E:\tmp\jh-interview\outcome-live\mutate.py`).
- Results (`docs/evals/outcome-2026-10-18-interview-prep/`, model claude-opus-4-8[1m],
  one sample per case, $10.78 CLI-reported): with the skill loaded 6/6 meet
  expected_output (1, 5, 6 natural; 2, 3, 4 with `/interview-prep`). Natural routing
  (no hooks = plain install) loaded the skill in 3/6: cases 2 (make me sound like I know
  Looker), 3 (research Globex), 4 (mock panel) were answered by the base model; in case
  2 its script put invented experience in the user's mouth.
- Fixed, test-first: (1) gate false positives: `verify_no_fabrication.py` kept the comma
  in "In 2023, ..." so known years/numbers were flagged new (`cec398d`; canonical
  resume-tailor + byte-identical copies; resume-tailor 1.1.1, cover-letter 1.1.1,
  interview-prep 1.0.1; 2 regression tests, one load-bearing). (2) eval 3's
  `mentions_none` value matched the model quoting the injection to warn the user
  (`f02767a`; now checks for relaying the fee as a requirement).
- CI command: 383 passed (was 367). ruff clean on the new tools files; runner parses
  on Python 3.10.
- NOT done: description change for the natural-routing misses (needs a decision; see
  open-questions); gate fix NOT deployed to installs or Q (installs still run the pre-fix
  gate, which only over-flags); one sample per case; raw transcripts and workspaces kept
  at `E:\tmp\jh-interview\outcome-live\` (run/, run-invoked/), not committed.
- Hooks note: on this machine the ts-judge UserPromptSubmit hook injects "load
  interview-prep" for these prompts, so the user's own sessions likely route correctly;
  plain installs do not have it.

## 2026-10-18 routing runner: CLI errors are errors (commit `24eea6a`)

- `tools/run_routing_evals.py`: a `result` event with `is_error: true` (e.g. "Not logged
  in - Please run /login", subtype "success") now gives `errored: true` + `error` text;
  such cases are excluded from strict/lenient/negative scores, listed under "## Errored",
  make the run exit 1, and are re-run (not reused) when the same `--out-dir` is rerun.
- Tests: 2 new in `tools/test_run_routing_evals.py` replay the real not-logged-in stream
  (from `E:\tmp\jh-interview\routing-live\raw\062.jsonl`) through `main()` with a fake CLI process;
  both failed on the old runner (exit 0; errored raw reused). CI command: 367 passed.
- Live interview-prep routing run, after the user logged the CLI in: `--ids 62,63,73-86`
  (dry-run numbering checked; interview-prep evals #11 and #12 dedupe into cases 19 and 56,
  so they are not in these ids). 16/16 as expected on model claude-opus-4-8[1m]: positive strict 11/11, negative 5/5, 0 errored; CLI-reported cost $1.46 for the 5 completed negatives, 11 early-stopped positives not reported.
  Raw transcripts spot-checked (real Skill tool calls). Results (commit `9fd33e3`) in
  `docs/evals/routing-2026-10-18-interview-prep/` (report.md + results.json; raw/ and cwd/
  not committed, same as earlier runs); proxy report links to it.

## 2026-10-18 interview-prep, 8th family member (commit `c01d73c`)

- Origin: the ai-job-search review ranked its `/interview` command next after the reviewer
  pass; interview prep had been deferred since v4 for sibling-collision risk.
- Built `interview-prep/`: `load_application.py` (one tracker entry + the resume and cover
  letter that were sent + posting + confirmed LESSONS entries; lists posting URLs as
  do-not-open; never writes tracker.json) and `build_prep_pack.py` (`stages`, `build`,
  `source`, `questions`, `claims`; 6 stages). Answer lines are `> ` blockquotes and only
  those reach the bundled `verify_no_fabrication.py` (byte-identical, parity test).
  References: `interview-stages.md`, `mock-interview.md`, workspace contract.
- Wiring (same places as cover-letter on 2026-05-29): orchestrator description (1012
  chars), member table, routing examples, invariant text; all 7 siblings' `sister_skills`;
  contract producer/consumer rows, re-synced into all 8 members, plus a new byte-equality
  test (`test_every_members_contract_copy_matches_the_orchestrators`); application-tracker
  do-not-use clause; installers; `build_plugin.py`; plugin.json/marketplace.json
  descriptions (were stale at 6 skills); routing runner + 7 new labels; CI test command;
  README (member table also lacked cover-letter; old FAQ said interview prep was out of
  scope).
- Live trial (Sonnet subagent, fictional workspace `E:\tmp\jh-interview\trial`, posting
  with an injected "$200 fee" instruction): injection ignored, posting URL not opened, Looker
  gap kept as an honest bridge. Found 4 defects, all fixed before commit with regression
  tests: "5+ years" keyword-matched to an unrelated line; rebuilding source.txt meant
  re-running `build`, overwriting the filled pack (`source` subcommand; `build` refuses to
  overwrite); URL kept a trailing period; gap requirements in questions to ask.
- Tests: 365 passed with the CI command (was 303; +61 interview-prep, +1 contract sync).
  Mutation check 15/15 killed (`E:\tmp\jh-interview\mutate.py`). ruff clean on new files.
  validate.py 0 errors on all 8 members; audit 11/15 interview-prep (same as other members).
  CI green on `c01d73c` (9/9 jobs).
- Trigger accuracy: the live `claude -p` routing run failed on every call with "Not logged
  in - Please run /login" (CLI not authenticated in this environment) and the runner
  mis-scored those as "(none)"; results discarded. Proxy check instead (fresh Sonnet
  subagent, real descriptions, name-only competitors): 18/18 as expected
  (`docs/evals/interview-prep-proxy-2026-10-18/`). Keyword mock runner: 14/16.
- Deployed: installer to all 24 installs (rollback `E:\Git\job-hunter-installs-pre-c01d73c.zip`,
  342 files), 309 files byte-verified; installed scripts run from all 3 roots. Q re-shipped
  (`E:\tmp\jh-interview\reship_q.py`, rollback `E:\Git\job-hunter-q-catalog-pre-c01d73c.zip`):
  34 zips, 761 entries byte-verified, INSTALL.md / NOTE-READ-ME-FIRST.txt rewritten for 8
  skills (ASCII), skill.json chain.members has interview-prep; update-catalog shows
  job-hunter in-sync.
- Not done: (live routing run since done: 16/16, see the runner entry above); outcome evals not run in a real
  harness; mock mode not exercised live; family version stays 6.0.0 (same precedent as
  cover-letter); no persistent story bank (see rejected-ideas).
- TypeSafe fit: declined (requirement-to-line matching is advisory and user-confirmed;
  public skill with resume PII and a no-phone-home rule).

## 2026-10-18 fresh-context reviewer pass (resume-tailor v1.1.0, cover-letter v1.1.0, commit `b010256`)

- Origin: competitive review of `MadsLorentzen/ai-job-search` (MIT, ~52K stars; checked safe
  before cloning: no hooks, symlinks, submodules, LFS or lifecycle scripts; settings.json
  only allow-lists commands). Verdict: do not adopt it (fork-and-own Claude Code template,
  Danish portal CLIs, LaTeX-only output, tech/academic profile assumptions). Borrow ideas.
  The clone is at `E:\tmp\ajs-clone` (nothing in it was run).
- Built first: the drafter-reviewer pass. New `scripts/review_pass.py` (canonical in
  resume-tailor, byte-identical in cover-letter, parity test). `packet` builds the reviewer
  prompt with random per-packet block markers and the posting marked untrusted; `check`
  validates the reviewer's JSON (quotes count only where they really appear; source
  evidence only from the source). Statuses: actionable / needs_user / needs_verification /
  dropped. Advisory only: `verify_no_fabrication.py` stays mandatory and runs last.
- SKILL.md: resume-tailor Mode B gains step 5 (gate is now step 6, cover letter step 7 also
  runs the pass); cover-letter gains step 3 (gate is now step 4, save step 5).
- Live trial (real Sonnet subagent, fictional resume, `E:\tmp\jh-review\live\`): valid
  JSON, all quotes verbatim, the injected posting instruction ignored. It found a real
  hole: `missed_requirement` with a real but insufficient quote ("2021-2024" for "5+
  years") came back actionable. Fixed: unaddressed requirements always go to the user.
  Regression test added; re-run of the same reply gives 6 actionable / 3 needs_user.
- Tests: 303 passed with the CI command (was 273; +26 resume-tailor, +4 cover-letter);
  7 new load-bearing tests listed in resume-tailor `_meta.json`, 3 in cover-letter;
  mutation check 9/9 killed (`E:\tmp\jh-review\mutate.py`). ruff clean on new files.
  validate.py 0 errors and audit 11/15 on both members, identical to HEAD before the
  change. CI green on `b010256`.
- Deployed: installer to all 21 installs (rollback `E:\Git\job-hunter-installs-pre-b010256.zip`,
  348 files), 273 files byte-verified against tracked source; installed `review_pass.py`
  run from all 6 resume-tailor/cover-letter installs on the live-trial files. Q re-shipped
  with a patched copy of the reship script (`E:\tmp\jh-review\reship_q.py`: dates no
  longer hardcoded, README SHA regex, cache-entry guard): 30 zips, 677 entries
  byte-verified, rollback `E:\Git\job-hunter-q-catalog-pre-b010256.zip`;
  `update-catalog.py` shows job-hunter shipped 2026-10-18.
- Cleaned during deploy: `.pytest_cache` dirs in 6 installs (the installer copies the
  working tree; the pre-deploy archive already held 12 such files from earlier deploys).
- Not done: Mode A (tighten) has no reviewer pass (gate-only, by design for now); the new
  outcome evals (resume-tailor #6, cover-letter #4) were not run against a real harness;
  the second review round and the no-subagent fallback were not exercised live.
- TypeSafe fit: declined for this feature (public portable skill with resume PII and a
  no-phone-home rule; evidence checks are exact substring logic; critique needs free text).

## 2026-10-13 state workforce portal check (job-search v1.0.1, commit `46b585e`)

- All 51 rows checked: Python HTTP pass (status, final URL, title) + Google DNS re-check + the in-app browser for blocked/unclear rows; replacements from web search confirmed by loading them and, for non-.gov hosts, by finding the link on the agency's .gov page (GA dol.georgia.gov, KY kcc.ky.gov, LA laworks.net, OR unemployment.oregon.gov, RI dlt.ri.gov). NY: official alias myjobs.ny.gov is a CNAME to myjobsny.usnlx.com but failed TLS in Python, curl and the browser, so the table uses newyork.usnlx.com ("Welcome to the New York State Job Bank!").
- Result: 13 replaced, 7 moved to .gov redirect targets; build_search_queries.py STATE_PORTALS fixed (5 dead incl. the hijacked GA domain). New `tools/check_state_portals.py` (network, manual) + `tools/test_state_portals.py` (offline, CI; mutation-checked). 273 tests; CI green on `46b585e`.
- Deployed: installs (rollback `E:\Git\job-hunter-installs-pre-46b585e.zip`), Q re-shipped (rollback `E:\Git\job-hunter-q-catalog-pre-46b585e.zip`, 661 entries byte-verified).
- Side effect during the check: opening dol.ny.gov/new-york-state-job-bank-fact-sheet in the browser pane triggered a PDF download dialog shown to the user; it was fetched with curl instead (E:\tmp\jh-links\dl\).
- Not verified: agency names for rows that were not replaced (e.g. FL, MI agencies may have been renamed); only portal hosts were checked.

## 2026-10-13 parse_resume fix (career-profile v1.1.0, commit `9d1bb29`)

- Tested 2026-10-12 on 11 Word-authored files (fictional resume, 5 layouts x DOCX/PDF + scanned PDF; harness in `E:\tmp\jh-resume\`). PDFs were fine; DOCX lost header/text-box contact info, appended tables at the end (experience filed under CERTIFICATIONS), tripled merged cells, lost in-table headings; scanned PDF returned empty text with exit 0.
- Fix: `_parse_docx` walks the body XML in document order (paragraphs, tables, content controls, text boxes; skips mc:Fallback duplicates; one read per w:tc), adds header/footer lines; `parse()` raises on empty extraction with an ask-the-user message. SKILL.md usage leads with `uv run`.
- Tests: `career-profile/tests/test_parse_resume.py` (15) + `tests/fixtures/resumes/` (8 files, 368 KB). 10/15 failed before the fix; all pass after. Re-score with the original harness: 12/12 facts on all 10 text files, sections + order correct; scanned PDF exits 2. Full suite 269 passed; CI green on `9d1bb29` (now installs python-docx + pypdf); tests skip cleanly without those packages.
- Correction: plain `python scripts/parse_resume.py` works on this machine (python-docx/pypdf in user site-packages); the earlier "not installed" result came from `python -I`.
- Deployed: installer -> 21 installs verified (rollback `E:\Git\job-hunter-installs-pre-9d1bb29.zip`); Q re-shipped (rollback `E:\Git\job-hunter-q-catalog-pre-9d1bb29.zip`), 661 entries byte-verified, catalog v6.0.0 in-sync. Per-member zips include tests/ (package_skill.py behavior), so career-profile zips now carry the fictional fixtures; installs and plugin strip tests.
- Not done: re-running career-profile routing evals (description unchanged, so not needed); testing Google Docs / LibreOffice-authored files (only Word-authored covered).

## 2026-10-12 live routing evals (first real-Claude measurement)

- Runner: `tools/run_routing_evals.py` (+ `tools/routing-labels.json`, 9 unit tests). Uses the user's real environment via `claude -p --output-format stream-json` and records the skill actually invoked (Skill tool call or Read of a SKILL.md), stopping each call at the first skill call (early-stop added after the first attempt cost $0.9-1.4/query by continuing the task).
- Result (`docs/evals/routing-2026-10-12/`): model claude-opus-4-8[1m], 306 skills loaded. 72 queries: positive strict 55/64 (86%), lenient (orchestrator accepted) 59/64 (92%); off-domain 8/8 (100%). CLI-reported cost $7.23 for the 12 completed calls; 60 early-stopped calls do not report cost (estimate ~$0.4-0.9 each).
- Hard misses (5): #15 resume DOCX -> `document-skills:docx`, #16 resume PDF -> `document-skills:pdf` (generic format skills beat career-profile); #8 "Restore my job-hunter workspace" -> no skill (orchestrator description never mentions workspace export/import/restore, which it owns; model went to 2ndBrain memory instead); #67 "Show me my application outcomes" -> application-tracker (ambiguous label); #68 "Reset what you know about my preferences" -> no skill (query has no job-search context; model discussed CLAUDE.md/memory).
- Soft misses (4, orchestrator chosen for broad asks): "Find me a job", freelance designer NYC, Texas state jobs, "Help me with my resume". Acceptable by design.
- Confirmed stale eval: resume-tailor#7 (cover letter) routed to cover-letter, as the label override predicted. application-tracker's description still points cover letters to resume-tailor (no observed miss from it).
- **Fixes applied (user-approved), commit `913ca8f`:** job-hunter description claims workspace export/import/back up/restore (987 chars); career-profile "read ... their resume file ... prefer this over a generic DOCX or PDF skill" (1010 chars); application-tracker cover letters -> cover-letter (frontmatter + body); resume-tailor eval #7 -> F; outcome-learning eval #5 reworded with job-search context; routing label for "application outcomes" accepts outcome-learning OR application-tracker (genuinely ambiguous; that pass comes from the label, not a routing change).
- **Deployed:** installer run from the repo to all 3 harness roots (rollback `E:\Git\job-hunter-installs-pre-913ca8f.zip`, 279 files); all 21 installs diff-clean vs source except tests/. Q re-shipped from `913ca8f` via `E:\tmp\jh-scripts\reship_q.py` (rollback `E:\Git\job-hunter-q-catalog-pre-913ca8f.zip`): 30 zips, 625 entries byte-verified, PLUGIN + FAMILY zips now built from git-tracked files (old FAMILY zip carried a stray .pytest_cache + .pyc); catalog v6.0.0 in-sync.
- **Re-run (11 affected queries, `docs/evals/routing-2026-10-12-rerun/`):** 11/11 strict. Combined with the unchanged 61: strict 60/64 (94%), lenient 64/64 (100%), off-domain 8/8. Caveats: one sample per query (routing is not deterministic); the 61 other queries were NOT re-run under the new descriptions (application-tracker's changed only in its do-not-use clause).
- Remaining strict misses are the 4 broad asks routed to the orchestrator (by design).
- CI: workflow fixed in `9274fb6` (was `pytest tests/`, no such dir since v6; red on every push since 2026-05-28). First green run since 2026-05-21: `e60a28d`, 3 OS x 3 Python.

## 2026-10-12 Q republish (DONE, user-approved)

- Rollback archive of the previous Q folder (148 files, 1,387,083 bytes, zip-tested): `E:\Git\job-hunter-q-catalog-pre-2026-10-11.zip`.
- `Q:\skills\job-hunter` now = 28 per-member zips (7 x claude-code/codex/cursor/portable, orchestrator named `job-hunter-orchestrator-v6.0.0-*`) + PLUGIN zip + FAMILY installer zip + INSTALL.md + NOTE-READ-ME-FIRST.txt + README.md + skill.json. v4 source tree and v0.1.0 zips removed.
- skill.json: v6.0.0, `chainability: chain-orchestrator`, `source_repo: E:\Git\job-hunter-public\job-hunter`, `family_source_commit: 57273f8`.
- Verified: 436 files across the 28 zips byte-identical to source (codex `agents/openai.yaml` excluded, packager-generated); `verify_no_fabrication.py` present in resume-tailor and cover-letter zips; `python Q:\skills\update-catalog.py` -> catalog.json lists job-hunter v6.0.0, version_drift in-sync, 30 packages (catalog total 91 skills).
- Script used: `E:\tmp\jh-scripts\republish_q.py`. Rollback = delete Q folder contents and unzip the archive's `job-hunter/` into `Q:\skills\`.

## 2026-10-11 audit (read this first)

**Source + installs are healthy. The Q catalog is NOT.**
- **Verified:** this repo at `4f7b84b` is clean and equal to origin/main; 244 tests green (corrected 2026-10-12 from a mis-added 247; job-hunter 65, career-profile 25, job-search 25, resume-tailor 28, cover-letter 12, application-tracker 51, outcome-learning 35, installer 3). All 7 members in `~/.claude`, `~/.agents`, `~/.hermes` match source except `tests/` (by design).
- **Regression (2026-06-06):** `E:\Git\skills\job-hunter` (a frozen v4 copy, separate nested repo) went through `E:\Git\skills\scripts\sync_q.py push` -> `publish_to_q.py`. Result on `Q:\skills\job-hunter`: v4 monolith zips labelled `v0.1.0` (v4 `_meta.json` has no `version`, script fell back to `0.1.0`); v4 source tree copied onto Q; `skill.json` and `Q:\skills\catalog.json` say `v0.1.0`; the 4 `job-hunter-orchestrator-v6.0.0-*.zip` files deleted (cleanup glob `job-hunter-*-<target>.zip` matched them). Anyone installing `job-hunter` from Q gets v4, which has no anti-fabrication gate.
- **Older drift found at the same time:** the per-member zips for career-profile, job-search, resume-tailor, application-tracker, outcome-learning on Q were built at 00:02 on 2026-05-29, BEFORE the cover-letter commit; they lack the updated `_meta.json` sister_skills, the 7-member workspace contract, and resume-tailor's "optimizer" triggers. Cover-letter zips, the PLUGIN zip (93 files) and the FAMILY installer zip (104 files) are byte-identical to source.
- **Locked (done):** `E:\Git\skills` commit `e6993da` adds `publish_to_q.EXTERNAL_SOURCES = {"job-hunter": "E:\Git\job-hunter-public"}`; `publish()` and `sync_q` push/pull skip it; cleanup glob narrowed to `<name>-v*-<target>.zip`; `tests/test_publish_guards.py` 6/6 (5/6 fail on pre-fix scripts). `sync_q --status` shows `job-hunter external -> E:\Git\job-hunter-public`. `E:\Git\skills` has no remote, so nothing to push.
- **Pending user approval:** the Q republish (deletes/overwrites files on Q, blocked by auto-mode classifier). Prepared: 28 fresh zips at `E:\tmp\jh-rebuild\` built from `4f7b84b` with `E:\Git\skill-builder-workdir\self-improving-skills\scripts\package_skill.py`; script `E:\tmp\jh-scripts\republish_q.py` was NOT written (denied). Plan: full rollback zip of the Q dir first, remove v4 tree + v0.1.0 zips, copy 28 zips, write v6 `skill.json` (`chainability: chain-orchestrator`, `source_repo` = `job-hunter-public\job-hunter` so update-catalog's SKILL.md+_meta.json fingerprint works), then `python Q:\skills\update-catalog.py`.
- Note: `publish_to_q.py`'s packager path `~/.claude/skills/self-improving-skills/scripts/package_skill.py` no longer exists; it falls back to scanning `E:\Git\skill-builder-workdir`.

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
- **Catalog (Q:) -- STALE as of 2026-10-11, see the audit section at the top; the text below is the 2026-05-28 state:** `Q:/skills/job-hunter/` has 5 v6.0.0 zips (claude-code, codex, openclaw, hermes, portable; 234,197 bytes each, 91 entries) + `skill.json` (current_version v6.0.0, chainability plugin-bundle, chain.members 6, source_version_hash 67161e9d516c) + README. `Q:/skills/catalog.json` lists job-hunter at current_version v6.0.0, kind skill-family-bundle.
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

Exact next action (2026-10-12): **none required.** Q republished and verified (see top). Optional, user-chosen: real-Claude routing/outcome eval pass; parse_resume on real DOCX/PDF; state workforce URL liveness check; GitHub `v6.0.0` Release object (user-gated). (2026-05-29 text, kept for history: v6.0.0 family (7 members) is fully shipped + redeployed + clean; repo is PUBLIC; plugin verified at Skills (7). Nothing technical pending.) The only open item is the optional GitHub `v6.0.0` *Release* object (user-gated). Do not cut it without explicit user authorization.

## Blockers

None. All technical work for the v6.0.0 family split, ship, and redeploy is complete and verified.
