# Maintenance, job-hunter family (orchestrator-owned shared stack)

Recurring tasks + freshness checks for the whole family (orchestrator + 5 members). Each has a
cadence, a trigger, and the exact commands or manual steps. Run on the schedule even if nothing
seems broken, staleness compounds quietly. The state-portal / niche-board freshness tasks below
now apply to the **job-search** member's references; the deploy task uses the **family installer**
(`install/install.ps1` / `install/install.sh`, all 6 skills). The combined suite is 226 tests.

## Before accepting a behavior change

(Not a cadence, gates every iteration.)

1. Read this continuity stack in order: `session-state.md`, `compaction-handoff.md`,
   `decisions.md`, `rejected-ideas.md`, `lessons.md`, `discovery-log.md`.
2. Update or add trigger/outcome evals covering the proposed change.
3. Run `run_evals.py --runner mock` against the change.
4. Verify frozen-v1 AND frozen-v2 cohorts both hold (5/5 each).
5. If the change touches a bundled script, add or update unit tests in `tests/`. Run
   `python -m pytest tests/` and verify all tests pass. If a load-bearing design choice
   was made (weight rationale, asset-as-source-of-truth, dot-prefix privacy, threshold
   values), write a paranoid safety test and list it in `_meta.json` under
   `load_bearing_safety_tests` (CL45 pattern; see v4 entries for examples).
6. If live trigger accuracy drops vs. prior iteration, REJECT the change.
7. Run `ci_check.py` against both source and installed copy; both must pass all 6 stages.
8. If accepted, append `CHANGELOG.md` with the signal, change, and before/after scores.
9. Update `_meta.json` (`current_score`, `last_iteration`, `signals_observed`, add
   iteration entry to `iterations[]` array).
10. Revise the four time-sensitive continuity docs (`session-state.md`,
    `compaction-handoff.md`, `lessons.md`, `discovery-log.md`) against ACTUAL landed
    state before declaring done (CL11, aspirational continuity docs are a documented
    failure mode).
11. When ready to deploy, run the v5+ installer (`install/install.ps1` on Windows,
    `install/install.sh` on macOS/Linux) to refresh the installed `~/.claude/skills/job-hunter/`
    copy. Re-sync after any accepted change; the installed copy is a snapshot, not a live view.

## Quarterly: state workforce commission URL freshness

**Cadence:** every 90 days from `_meta.json.last_review_due` (current family value: 2026-08-26 → next 2026-11-24 → …)

**Why:** State agencies rebrand and redomain. The `references/state-workforce-commissions.md`
table lists 50 portals. If any 404 or redirect to "we've moved," users get confusing
search results.

**Procedure:**
1. Pick 5 random states from the table.
2. Visit each portal URL in a browser.
3. If any return 4xx/5xx or redirect to a different portal: search `[state] workforce
   commission jobs` and update the table with the new URL + a note.
4. If any URLs changed: also bump `last_reviewed` in the file's frontmatter (if added) or
   add a "Last verified: YYYY-MM-DD" line near the top.

## Quarterly: niche-board URL freshness

**Cadence:** every 90 days, same cycle as state-workforce.

**Why:** Niche boards consolidate, get acquired, or shut down regularly (GitHub Jobs is
already noted as discontinued in the reference). Each closure or rename invalidates a row
of the table.

**Procedure:**
1. Skim `references/niche-boards-by-industry.md`.
2. Spot-check 1-2 boards per industry section by hitting their root URL.
3. If a board has shut down: mark it `(discontinued YYYY-MM)` and stop recommending it.
4. If a board has changed name: update the row.

## Annually: full audit + eval re-run

**Cadence:** every 365 days from `last_iteration` (next: 2027-05-11).

**Why:** Even with no intentional changes, the surrounding ecosystem shifts: new ATS products,
new niche boards, new posting conventions, new compensation transparency laws. An annual
re-audit catches drift.

**Procedure:**
```powershell
$builder = "C:\Users\Owner\.claude\skills\self-improving-skills"
$work = "E:\Git\job-hunter-public"
python "$builder\scripts\audit_existing.py" --skill $work
python "$builder\scripts\validate.py" $work
python "$builder\scripts\run_evals.py" --skill $work --runner mock --out-dir "$work\evals\results\annual-$(Get-Date -Format yyyyMMdd)"
```

If audit drops below 15/15, address findings. If trigger accuracy drops below 95%, treat as
a regression and enter the iteration loop.

## After any real user run

**Cadence:** opportunistic, when there's a real-world job-hunter run with transcripts.

**Why:** Real usage surfaces trigger misses and overfires the eval suite didn't anticipate.
This is the canonical "iterate on real signal, not imagined signal" path.

**Procedure:**
1. `python "$builder\scripts\harvest_signals.py" --skill $work --transcripts <path>`
2. `python "$builder\scripts\propose_iteration.py" --signals <signals.json> --skill $work`
3. Review the proposed suggestions; accept/reject/modify per Karpathy's surgical-changes rule.
4. Apply edits, re-run evals, follow the standard accept-only-on-real-deltas gate.

## When a sibling docx or pdf skill update lands

**Cadence:** opportunistic.

**Why:** Job-hunter (v3+) prefers `parse_resume.py` (standalone) over sibling skills, but if a
sibling docx/pdf skill in the active client improves dramatically (better formatting,
specific feature like PDF form filling), the SKILL.md guidance for *writing* tailored
resumes might want to update its sibling-skill recommendation.

**Procedure:** Read the sibling skill's CHANGELOG; if it adds features job-hunter could
benefit from, update the "Reading and writing resume formats" section in SKILL.md to call
them out. Add a trigger eval if the new feature creates a new triggering surface.

## When self-improving-skills (the harness) updates

**Cadence:** opportunistic.

**Why:** The harness scripts (`audit_existing.py`, `validate.py`, `run_evals.py`,
`optimize_skill.py`) may change their CLI args, output formats, or scoring rules. Job-hunter
maintenance commands in this file may need updating.

**Procedure:** When the harness updates, re-run the commands in this file once. If any args
have changed (e.g., `--results` vs `--out-dir`), update the maintenance.md commands accordingly.

## Deploy the family to the installed skills

**Cadence:** triggered, not recurring. Run after the cutover is approved and you want the
installed family to reflect the repo state.

**Why:** The installed copies are packaged snapshots, NOT symlinks or live views of the repo.
Repo edits don't propagate automatically. **As of 2026-05-28 the family has NOT been deployed:
deploy (and the whole cutover — delete root monolith, merge `family-split` → `main`, tag
`v6.0.0`, push) is GATED on explicit user approval. Do not run the installer unprompted.**

**Procedure (family, canonical, THIS repo) — only after cutover approval:**
```powershell
cd E:\Git\job-hunter-public
# 1. Confirm branch + family suite passes before deploying
git status --short
python -m pytest . -q            # expect 226 passed (the family)

# 2. Run the family installer — installs ALL 6 skills into each harness root
powershell -ExecutionPolicy Bypass -File install\install.ps1
#   (macOS/Linux: bash install/install.sh)

# 3. Verify an installed member, e.g. the orchestrator
python C:\Users\Owner\.claude\skills\self-improving-skills\scripts\ci_check.py C:\Users\Owner\.claude\skills\job-hunter
```

`install/install.ps1` (Windows) and `install/install.sh` (macOS/Linux) install all 6 family
skills into `~/.claude/skills/<member>/` (Claude Code), `~/.agents/skills/<member>/` (Codex AND
OpenClaw), and `~/.hermes/skills/<member>/` (Hermes). Per-harness guides:
`install/claude-code.md`, `install/codex.md`, `install/openclaw.md`, `install/hermes.md`.
Installer self-test: `install/test_installer_targets.py`.

**Historical (v4 ancestor):** the frozen workdir copy used a `.install.ps1` that packaged via
`package_skill.py` and deployed to versioned `job-hunter-vN` paths + refreshed
`E:\Git\SKILL-CATALOG.md`. That procedure applies only to the frozen ancestor, not to v5+.

## Snapshot a new frozen-vN cohort

**Cadence:** triggered, not recurring. Run whenever the description gets a substantial rewrite.

**Why:** A new description means the existing frozen cohort was scored against a different
set of trigger criteria. Without a new cohort matched to the new description, the regression
detector loses some of its grip.

**Procedure:**
```powershell
python "$builder\scripts\snapshot_frozen.py" --skill $work --apply
```
The script auto-increments to the next available `frozen-vN.json` and refuses to overwrite
existing ones, so this is safe to run.
