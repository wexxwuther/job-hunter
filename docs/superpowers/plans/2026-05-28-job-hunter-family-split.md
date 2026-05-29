# job-hunter Family Split — Implementation Plan

> **For agentic workers (required sub-skill):** use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split the monolithic job-hunter v5.2.0 skill into a 6-skill family (orchestrator + 5 members) with typed artifact hand-offs, applying v1.42 precedents + Opus-4.8 currency, without breaking the working public skill.

**Architecture:** Family monorepo at `E:/Git/job-hunter-public/` (branch `family-split`). One orchestrator dir (`job-hunter/`) owns the `.job-hunter/` workspace + routing + the anti-fabrication family invariant; 5 member dirs (`career-profile/`, `job-search/`, `resume-tailor/`, `application-tracker/`, `outcome-learning/`) each hold a SKILL.md + their owned scripts + tests + evals. The current v5.2.0 files stay at repo root until Stage D cutover.

**Tech Stack:** Python 3 (stdlib + pathlib; PEP 723 where external deps), pytest, agentskills.io skill format, bash + PowerShell installers.

**Spec:** `docs/superpowers/specs/2026-05-28-job-hunter-family-split-design.md`

**Invariants for every task:**
- Work on branch `family-split` only. NEVER touch `main`. NEVER `git push`. NEVER redeploy to install paths.
- All files written LF (repo `.gitattributes` enforces eol=lf; `*.ps1` stays crlf).
- The current root-level `SKILL.md`/`scripts/`/`tests/`/`evals/` (v5.2.0) stay working and untouched until Stage D — members are built as NEW dirs by COPYING scripts (not moving), so root stays intact for parity comparison. Deletion of root skill files happens only in Stage D after approval.
- Baseline to preserve: **201 tests passing** in the root suite. The family's combined suite must be ≥ 201.

**Script → member ownership (from spec §3):**
- orchestrator `job-hunter/`: `init_workspace.py`, `export_workspace.py`, `import_workspace.py`
- `career-profile/`: `init_profile.py`, `parse_resume.py`
- `job-search/`: `build_search_queries.py`, `expand_role_synonyms.py`, `normalize_salary.py`, `dedupe_postings.py`, `score_posting.py`
- `resume-tailor/`: `extract_ats_keywords.py`, `verify_no_fabrication.py`
- `application-tracker/`: `generate_tracker_html.py`, `draft_followup.py`
- `outcome-learning/`: `harvest_outcomes.py`, `propose_lessons.py`

**Test → script coverage (from audit):** scripts with a dedicated `tests/test_<name>.py`: init_profile, init_workspace, score_posting, verify_no_fabrication, generate_tracker_html, draft_followup, harvest_outcomes, propose_lessons, and workspace_export_import (covers export+import). **Eval-only scripts (no unit test, coverage travels via the eval partition):** build_search_queries, dedupe_postings, expand_role_synonyms, normalize_salary, extract_ats_keywords, parse_resume.

---

## STAGE A — Orchestrator reshape + shared contract + family skeleton

### Task A1: Create the family directory skeleton

**Files:**
- Create dirs: `job-hunter/`, `career-profile/`, `job-search/`, `resume-tailor/`, `application-tracker/`, `outcome-learning/` (each with `scripts/`, `references/`, `evals/`, `tests/`)

- [ ] **Step 1: Create the 6 skill dirs with standard subdirs**

```bash
cd E:/Git/job-hunter-public
for s in job-hunter career-profile job-search resume-tailor application-tracker outcome-learning; do
  mkdir -p "$s/scripts" "$s/references" "$s/evals" "$s/tests"
done
```

- [ ] **Step 2: Verify**

Run: `ls -d job-hunter career-profile job-search resume-tailor application-tracker outcome-learning`
Expected: all 6 dirs listed.

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "stage-a: scaffold 6-skill family dir skeleton"
```

### Task A2: Write the shared workspace-contract reference

**Files:**
- Create: `job-hunter/references/workspace-contract.md`
- Test: `job-hunter/tests/test_workspace_contract.py`

- [ ] **Step 1: Write the failing test (the contract file exists + documents each artifact)**

```python
# job-hunter/tests/test_workspace_contract.py
from pathlib import Path

CONTRACT = Path(__file__).resolve().parent.parent / "references" / "workspace-contract.md"

def test_contract_documents_every_shared_artifact():
    text = CONTRACT.read_text(encoding="utf-8")
    for artifact in ["profile.md", "postings.json", "tracker.json", ".job-hunter/"]:
        assert artifact in text, f"workspace-contract.md must document {artifact}"

def test_contract_names_every_producer_member():
    text = CONTRACT.read_text(encoding="utf-8")
    for member in ["career-profile", "job-search", "resume-tailor",
                   "application-tracker", "outcome-learning"]:
        assert member in text, f"contract must name producer {member}"
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd E:/Git/job-hunter-public && python -m pytest job-hunter/tests/test_workspace_contract.py -q`
Expected: FAIL (file not found / assertion).

- [ ] **Step 3: Write the contract**

Create `job-hunter/references/workspace-contract.md` documenting: the `.job-hunter/` dir layout; each artifact (`profile.md`, parsed-resume text, `postings.json` scored shape, `tracker.json` shape, proposed-LESSONS); for each, the producing member and consuming member(s); the rule that every member reads upstream artifacts if present and degrades gracefully if absent. (Pull the JSON shapes from the existing scripts' output — e.g. `score_posting.py` output keys, `generate_tracker_html.py` tracker.json keys.)

- [ ] **Step 4: Run to verify it passes**

Run: `python -m pytest job-hunter/tests/test_workspace_contract.py -q`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "stage-a: shared .job-hunter workspace-contract reference + test"
```

### Task A3: Move orchestrator-owned scripts + tests into job-hunter/

**Files:**
- Copy: `scripts/{init_workspace,export_workspace,import_workspace}.py` → `job-hunter/scripts/`
- Copy: `tests/{test_init_workspace,test_workspace_export_import}.py` → `job-hunter/tests/`

- [ ] **Step 1: Copy the 3 scripts + 2 tests (copy, not move — root stays intact for parity)**

```bash
cd E:/Git/job-hunter-public
cp scripts/init_workspace.py scripts/export_workspace.py scripts/import_workspace.py job-hunter/scripts/
cp tests/test_init_workspace.py tests/test_workspace_export_import.py job-hunter/tests/
```

- [ ] **Step 2: Fix test import paths if needed**

The copied tests resolve the script dir relative to their own location. Check each test's `sys.path` / script-locating logic. If a test computes `Path(__file__).parent.parent / "scripts"`, it now correctly points at `job-hunter/scripts/` — no change needed. If it hardcodes a different path, update it.

Run: `cd E:/Git/job-hunter-public && PYTHONPATH=job-hunter/scripts python -m pytest job-hunter/tests/ -q`
Expected: PASS (all init_workspace + export/import tests green from the new location).

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "stage-a: orchestrator scripts+tests (workspace lifecycle) into job-hunter/"
```

### Task A4: Write the orchestrator SKILL.md + _meta.json (family metadata skeleton)

**Files:**
- Create: `job-hunter/SKILL.md`, `job-hunter/_meta.json`
- Test: `job-hunter/tests/test_orchestrator_meta.py`

- [ ] **Step 1: Write the failing test (family metadata + routing surface)**

```python
# job-hunter/tests/test_orchestrator_meta.py
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
META = ROOT / "_meta.json"
SKILL = ROOT / "SKILL.md"

def test_orchestrator_declares_family():
    m = json.loads(META.read_text(encoding="utf-8"))
    assert m["family"] == "job-hunter"
    assert m["family_role"] == "orchestrator"
    assert set(m["sister_skills"]) == {
        "career-profile", "job-search", "resume-tailor",
        "application-tracker", "outcome-learning"}

def test_orchestrator_skill_routes_to_all_members():
    text = SKILL.read_text(encoding="utf-8")
    for member in ["career-profile", "job-search", "resume-tailor",
                   "application-tracker", "outcome-learning"]:
        assert member in text, f"orchestrator SKILL.md must reference {member}"

def test_orchestrator_states_antifabrication_invariant():
    text = SKILL.read_text(encoding="utf-8").lower()
    assert "verify_no_fabrication" in text or "fabrication" in text
    assert "invariant" in text or "hard gate" in text
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest job-hunter/tests/test_orchestrator_meta.py -q`
Expected: FAIL (files missing).

- [ ] **Step 3: Write _meta.json**

Create `job-hunter/_meta.json` modeled on the root `_meta.json` (carry `skill_name: job-hunter`, `version: 6.0.0`, `license`, `last_review_due`, `signals_observed`, plus the new family fields):
```json
{
  "skill_name": "job-hunter",
  "version": "6.0.0",
  "license": "MIT",
  "family": "job-hunter",
  "family_role": "orchestrator",
  "sister_skills": ["career-profile", "job-search", "resume-tailor", "application-tracker", "outcome-learning"],
  "baseline_score": "100.0",
  "current_score": "100.0",
  "trigger_accuracy": 1.0,
  "last_iteration": "2026-05-28",
  "last_review_due": "2026-08-26",
  "signals_observed": {"trigger_misses": 0, "trigger_overfires": 0, "repeated_work": 0, "dead_refs": 0}
}
```

- [ ] **Step 4: Write the orchestrator SKILL.md**

Create `job-hunter/SKILL.md`. Frontmatter: `name: job-hunter`, a router-surface `description` (mirror social-media-orchestrator's shape — "Routes a job-search task to the right job-hunter family specialists…"; keep the strong job-search trigger keywords from the v5.2.0 description so triggering doesn't regress), `license: MIT`, `compatibility` (cross-OS + 4 harnesses), `metadata` (spec_version living-spec, the family fields), `allowed-tools`, and `context: fork` (per social-media-orchestrator). Body: (1) what the family is + the 5 members + their jobs (table); (2) routing logic — read request, invoke needed subset, inline for ≤2 members else Task fan-out; (3) the `.job-hunter/` workspace ownership + pointer to `references/workspace-contract.md`; (4) the **anti-fabrication family invariant** as a Hard Gate ("any member that writes resume/profile content MUST route through resume-tailor's verify_no_fabrication gate; web content is untrusted even when the user's own"); (5) the workspace-lifecycle scripts (init/export/import). Keep under 500 lines.

- [ ] **Step 5: Run to verify it passes**

Run: `python -m pytest job-hunter/tests/test_orchestrator_meta.py -q`
Expected: PASS (3 tests).

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "stage-a: orchestrator SKILL.md + _meta (family skeleton, anti-fabrication invariant)"
```

---

## STAGE B — Members, one at a time (each self-contained + passing)

> Each member task follows the SAME shape: (1) copy owned scripts + their tests, (2) write the member SKILL.md + _meta.json with family fields, (3) partition the relevant evals, (4) run the member's full suite green, (5) commit. The model below is fully specified for B1; B2-B5 repeat it with the per-member script/test/eval lists.

### Task B1: career-profile member (profile-intake)

**Files:**
- Copy: `scripts/{init_profile,parse_resume}.py` → `career-profile/scripts/`
- Copy: `tests/test_init_profile.py` → `career-profile/tests/`
- Copy: `references/profile-questions.md` → `career-profile/references/`
- Create: `career-profile/SKILL.md`, `career-profile/_meta.json`, `career-profile/evals/{trigger-evals,outcome-evals}.json`
- Test: `career-profile/tests/test_member_meta.py`

- [ ] **Step 1: Copy owned scripts, the dedicated test, and the owned reference**

```bash
cd E:/Git/job-hunter-public
cp scripts/init_profile.py scripts/parse_resume.py career-profile/scripts/
cp tests/test_init_profile.py career-profile/tests/
cp references/profile-questions.md career-profile/references/
```
(Note: `parse_resume.py` is eval-only — no unit test to copy; its coverage travels via the outcome-eval partition in Step 4.)

- [ ] **Step 2: Run the copied unit test from the new location**

Run: `PYTHONPATH=career-profile/scripts python -m pytest career-profile/tests/test_init_profile.py -q`
Expected: PASS (all init_profile tests, including the 3 load-bearing ones: dot-prefixed filename, no-sample-profile-in-skill-dir, questions-count-is-five).

- [ ] **Step 3: Write the member meta test (the family-wiring contract for this member)**

```python
# career-profile/tests/test_member_meta.py
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent

def test_member_declares_family():
    m = json.loads((ROOT / "_meta.json").read_text(encoding="utf-8"))
    assert m["family"] == "job-hunter"
    assert m["family_role"] == "profile-intake"
    assert "job-hunter" in m["sister_skills"]  # the orchestrator is a sister

def test_skill_md_has_name_and_description():
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert "name: career-profile" in text
    assert "description:" in text
```

- [ ] **Step 4: Run to verify it fails, then write _meta.json + SKILL.md + evals**

Run: `python -m pytest career-profile/tests/test_member_meta.py -q` → FAIL.
Write `career-profile/_meta.json` (`skill_name: career-profile`, `version: 1.0.0`, `family: job-hunter`, `family_role: profile-intake`, `sister_skills` = other 5 incl. `job-hunter`, the standard score/review/signals fields).
Write `career-profile/SKILL.md`: `name: career-profile`; description authored for real-LLM routing on "set up my job-search profile / parse my resume", with `Do not use for tailoring a resume to a posting (use resume-tailor) or searching for jobs (use job-search)` to manage sibling collision; body = the v5.2.0 Phase 1 content (profile North-Star questions, resume parsing), pointing at `references/profile-questions.md` + `references/workspace-contract.md` (note: members reference the orchestrator's contract by relative install path or restate the produced-artifact shape). Partition evals: from the root `evals/`, copy the trigger evals about profile/resume-parsing and outcome evals about profile init/reuse into `career-profile/evals/`, renumbering ids from 1.

- [ ] **Step 5: Run the member's FULL suite**

Run: `PYTHONPATH=career-profile/scripts python -m pytest career-profile/tests/ -q`
Expected: PASS (init_profile tests + member_meta tests).

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "stage-b: career-profile member (profile-intake) - scripts, SKILL.md, evals, family-wired"
```

### Task B2: job-search member (search)

Repeat the B1 shape with:
- Copy scripts: `build_search_queries.py`, `expand_role_synonyms.py`, `normalize_salary.py`, `dedupe_postings.py`, `score_posting.py` → `job-search/scripts/`
- Copy test: `tests/test_score_posting.py` → `job-search/tests/` (the other 4 scripts are eval-only — coverage via eval partition). The 3 score_posting load-bearing tests (cv_match-heaviest-weight, red-flag-torpedoes-score, thresholds-match-career-ops) MUST pass from the new location.
- Copy references: `niche-boards-by-industry.md`, `state-workforce-commissions.md`, `match-quality-rubric.md`, `posting-legitimacy-rubric.md` → `job-search/references/`
- `_meta.json`: `family_role: search`.
- `SKILL.md`: `name: job-search`; description for "find + score jobs"; `Do not use for tailoring a resume (use resume-tailor)`; body = v5.2.0 Phase 2 + 2.5 (4-tier search, scoring); reads `profile.md` if present, degrades to explicit criteria; produces scored `postings.json` per the workspace-contract.
- Evals: partition the search/scoring/ghost-job/dedupe trigger + outcome evals.
- Member meta test mirrors B1 with `family_role == "search"`.
- Commit: `stage-b: job-search member (search) - scripts, SKILL.md, evals, family-wired`.

### Task B3: resume-tailor member (resume-tailor) — MOST SAFETY-CRITICAL

Repeat the B1 shape with EXTRA care for the anti-fabrication gate:
- Copy scripts: `extract_ats_keywords.py`, `verify_no_fabrication.py` → `resume-tailor/scripts/`
- Copy test: `tests/test_verify_no_fabrication.py` → `resume-tailor/tests/` (extract_ats_keywords is eval-only). **All 24 verify_no_fabrication tests, including the 5 load-bearing safety tests (auto_approved-false-on-clean, auto_approved-false-on-dirty, exports-only-detection-no-approval, real-world-multi-category, years-NOT-flagged), MUST pass from the new location. This is the highest-stakes move in the whole plan.**
- Copy reference: `ats-formatting-guide.md` → `resume-tailor/references/`
- `_meta.json`: `family_role: resume-tailor`; carry forward the `load_bearing_safety_tests` array naming the 5 verify tests.
- `SKILL.md`: `name: resume-tailor`; description for "tailor/tighten my resume"; `Do not use for searching jobs (use job-search) or setting up a profile (use career-profile)`; body = the FULL v5.2.0 Phase 3 (Mode A Tighten / Mode B Tailor, the Hard Gate truth-preservation framing at the TOP, the web-content-untrusted rule, the mandatory verify_no_fabrication gate before any DOCX). Do NOT weaken any gate wording in the move.
- Evals: partition outcome evals #22 (tighten-not-tailor), #23 (web-untrusted), #24 (keyword-gap-confirmation) + tailor trigger evals.
- Add a member meta test AND a load-bearing-preservation test:

```python
# resume-tailor/tests/test_member_meta.py (excerpt — add to the standard member_meta test)
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent

def test_load_bearing_safety_tests_present_after_move():
    """The 5 anti-fabrication safety tests must survive the family split."""
    t = (ROOT / "tests" / "test_verify_no_fabrication.py").read_text(encoding="utf-8")
    for name in ["test_auto_approved_field_is_always_false_on_clean_input",
                 "test_auto_approved_field_is_always_false_on_dirty_input",
                 "test_script_exports_only_detection_no_approval_helpers",
                 "test_real_world_pattern_detects_multiple_categories",
                 "test_years_NOT_flagged_as_new_numbers"]:
        assert name in t, f"load-bearing safety test {name} lost in the split"
```

Run: `PYTHONPATH=resume-tailor/scripts python -m pytest resume-tailor/tests/ -q` → PASS (24 + member_meta + preservation).
Commit: `stage-b: resume-tailor member - Phase 3 Mode A/B + verify_no_fabrication gate intact (5 load-bearing tests preserved)`.

### Task B4: application-tracker member (tracker)

Repeat the B1 shape with:
- Copy scripts: `generate_tracker_html.py`, `draft_followup.py` → `application-tracker/scripts/`
- Copy tests: `tests/test_generate_tracker_html.py`, `tests/test_draft_followup.py` → `application-tracker/tests/`. Load-bearing tests that MUST pass: `test_script_has_no_inline_css_block`, `test_css_asset_loaded_into_output` (generate_tracker_html), `test_no_smtp_or_send_imports_in_script`, `test_scan_stale_does_NOT_fall_back_to_posted_field` (draft_followup).
- Copy asset: `assets/templates/tracker.css` → `application-tracker/assets/templates/` (generate_tracker_html bundles it — verify the script's CSS-path resolution still finds it from the new location; if it computes a relative path, no change; else update).
- Copy reference: `followup-templates.md` → `application-tracker/references/`
- `_meta.json`: `family_role: tracker`.
- `SKILL.md`: `name: application-tracker`; description for "track applications + follow up"; `Do not use for tailoring resumes (use resume-tailor)`; body = v5.2.0 Phase 4 + 4.5 (tracker.json + posted-vs-applied_date discipline + stale follow-ups, never auto-sends); reads `postings.json` + tailored-resume filenames; produces `tracker.json` → HTML.
- Evals: partition tracker/follow-up/thank-you trigger + outcome evals.
- Run member suite green. Commit: `stage-b: application-tracker member (tracker) - scripts, SKILL.md, evals, family-wired`.

### Task B5: outcome-learning member (learning-loop)

Repeat the B1 shape with:
- Copy scripts: `harvest_outcomes.py`, `propose_lessons.py` → `outcome-learning/scripts/`
- Copy tests: `tests/test_harvest_outcomes.py`, `tests/test_propose_lessons.py` → `outcome-learning/tests/`. Load-bearing tests that MUST pass: `test_three_outcomes_below_threshold_returns_no_op`, `test_parse_skips_template_preamble` (harvest), `test_application_guidance_always_warns_against_auto_write` (propose_lessons).
- Copy reference: `learning-loop-guide.md` → `outcome-learning/references/`
- `_meta.json`: `family_role: learning-loop`.
- `SKILL.md`: `name: outcome-learning`; description for "learn from my job-search outcomes / what's working"; `Do not use for searching jobs (use job-search)`; body = v5.2.0 Phase 0 (read .job-hunter learning files) + Phase 5 (harvest → propose → user-confirmed LESSONS, ≥5-closed cold-start guard, opt-in only). Note the `.job-hunter/` workspace templates (`DECISIONS/LESSONS/OUTCOMES/REJECTED_IDEAS.template.md`) are owned by the orchestrator's `init_workspace.py`; outcome-learning READS them — restate that dependency.
- Evals: partition learning-loop/cold-start/opt-in trigger + outcome evals.
- Run member suite green. Commit: `stage-b: outcome-learning member (learning-loop) - scripts, SKILL.md, evals, family-wired`.

---

## STAGE C — Family wiring, routing evals, parity, installer

### Task C1: Family-wiring verification check

**Files:**
- Create: `job-hunter/tests/test_family_wiring.py`

- [ ] **Step 1: Write the wiring test (every sister resolves, every member has the required files)**

```python
# job-hunter/tests/test_family_wiring.py
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent  # E:/Git/job-hunter-public
MEMBERS = ["job-hunter", "career-profile", "job-search",
           "resume-tailor", "application-tracker", "outcome-learning"]

def test_all_members_exist_with_required_files():
    for m in MEMBERS:
        d = REPO / m
        assert (d / "SKILL.md").exists(), f"{m} missing SKILL.md"
        assert (d / "_meta.json").exists(), f"{m} missing _meta.json"

def test_sister_skills_resolve():
    for m in MEMBERS:
        meta = json.loads((REPO / m / "_meta.json").read_text(encoding="utf-8"))
        for sister in meta.get("sister_skills", []):
            assert sister in MEMBERS, f"{m} references unknown sister {sister}"

def test_every_member_in_same_family():
    fams = {json.loads((REPO / m / "_meta.json").read_text(encoding="utf-8"))["family"] for m in MEMBERS}
    assert fams == {"job-hunter"}, f"members not in one family: {fams}"

def test_exactly_one_orchestrator():
    roles = [json.loads((REPO / m / "_meta.json").read_text(encoding="utf-8"))["family_role"] for m in MEMBERS]
    assert roles.count("orchestrator") == 1
```

- [ ] **Step 2: Run, fix any unresolved wiring, until green**

Run: `cd E:/Git/job-hunter-public && python -m pytest job-hunter/tests/test_family_wiring.py -q`
Expected: PASS (4 tests). If a sister name is wrong in any `_meta.json`, fix it.

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "stage-c: family-wiring verification test (sisters resolve, one family, one orchestrator)"
```

### Task C2: Combined-suite parity (>=201 tests)

- [ ] **Step 1: Run the whole family suite and count**

```bash
cd E:/Git/job-hunter-public
for m in job-hunter career-profile job-search resume-tailor application-tracker outcome-learning; do
  echo "== $m =="; PYTHONPATH="$m/scripts" python -m pytest "$m/tests/" -q 2>&1 | tail -1
done
```
Expected: each member's suite green. Sum the test counts.

- [ ] **Step 2: Verify parity**

The combined family test count must be **≥ 201** (the root baseline) — the moved unit tests + the new member_meta/wiring tests. If a script's tests didn't get copied to a member, that's a gap: find it and copy it. Document the count in the commit message.

- [ ] **Step 3: Commit (parity record)**

```bash
git add -A && git commit -m "stage-c: combined family suite parity confirmed (N tests >= 201 baseline)" --allow-empty
```

### Task C3: Orchestrator routing evals

**Files:**
- Create: `job-hunter/evals/trigger-evals.json`, `job-hunter/evals/outcome-evals.json`

- [ ] **Step 1: Write routing trigger + outcome evals**

`job-hunter/evals/trigger-evals.json`: positives that should reach the orchestrator (broad "help me find a job", "run my whole job search", multi-need requests) + negatives (single-need requests that should route to one member directly are still orchestrator-positive since it routes — but include true negatives like "review my code"). `outcome-evals.json`: routing-outcome cases — "tailor my resume for this Stripe role" → expects resume-tailor invoked; "find jobs and tailor for the top one" → expects job-search THEN resume-tailor; "where am I on applications" → application-tracker. Assertions use deterministic `kind` where checkable (e.g. `substring` on the member name in the routing report).

- [ ] **Step 2: Validate the eval JSON parses + has both should/should-not triggers**

```bash
cd E:/Git/job-hunter-public
python -c "import json; t=json.load(open('job-hunter/evals/trigger-evals.json')); assert any(e['should_trigger'] for e in t) and any(not e['should_trigger'] for e in t); print(len(t),'trigger evals OK')"
python -c "import json; o=json.load(open('job-hunter/evals/outcome-evals.json')); assert o['evals']; print(len(o['evals']),'outcome evals OK')"
```
Expected: both print counts, no assertion error.

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "stage-c: orchestrator routing trigger+outcome evals"
```

### Task C4: Family installer (4 harnesses, cross-OS)

**Files:**
- Create: `install/install.sh` (rewrite for family), `install/install.ps1` (rewrite for family)
- Test: `install/test_installer_targets.py`

- [ ] **Step 1: Write the failing test (installer references all 6 members + 3 harness roots, no drive letters)**

```python
# install/test_installer_targets.py
from pathlib import Path
INSTALL = Path(__file__).resolve().parent
MEMBERS = ["job-hunter", "career-profile", "job-search", "resume-tailor", "application-tracker", "outcome-learning"]

def test_sh_installs_all_members_to_all_harnesses():
    sh = (INSTALL / "install.sh").read_text(encoding="utf-8")
    for m in MEMBERS:
        assert m in sh, f"install.sh missing member {m}"
    for h in [".claude/skills", ".agents/skills", ".hermes/skills"]:
        assert h in sh, f"install.sh missing harness path {h}"
    assert "C:\\\\" not in sh and "E:\\\\" not in sh  # no Windows drive letters in the posix installer

def test_ps1_installs_all_members():
    ps1 = (INSTALL / "install.ps1").read_text(encoding="utf-8")
    for m in MEMBERS:
        assert m in ps1, f"install.ps1 missing member {m}"
    assert "$HOME" in ps1  # derives from home, not a hardcoded drive
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd E:/Git/job-hunter-public && python -m pytest install/test_installer_targets.py -q`
Expected: FAIL (installers still single-skill).

- [ ] **Step 3: Rewrite install.sh + install.ps1 to loop the 6 member dirs**

`install.sh`: bash loop over the 6 dirs, copying each into `$HOME/.claude/skills/<name>`, `$HOME/.agents/skills/<name>` (Codex+OpenClaw), `$HOME/.hermes/skills/<name>`; strip `.git`/`docs/superpowers`/`install`/`tests` from each installed copy; `set -euo pipefail`. `install.ps1`: PowerShell equivalent over `$HOME\.claude\skills\<name>` etc. Both derive paths from home; no hardcoded drive letters in `.sh`.

- [ ] **Step 4: Run to verify it passes**

Run: `python -m pytest install/test_installer_targets.py -q`
Expected: PASS (2 tests).

- [ ] **Step 5: Dry-run the sh installer logic without writing (syntax + path check)**

Run: `bash -n install/install.sh && echo "install.sh syntax OK"`
Expected: `install.sh syntax OK`.

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "stage-c: family installer (6 members x 4 harnesses, cross-OS) + targets test"
```

---

## STAGE D — Continuity, docs, version cut, cutover-approval gate

### Task D1: Family continuity stack at the orchestrator + member stubs

**Files:**
- Create: `job-hunter/docs/continuity/*.md` (the 11-doc stack)
- Create: `<member>/docs/continuity/README.md` stub for each of the 5 members

- [ ] **Step 1: Build the orchestrator continuity stack**

Adapt the existing root `docs/continuity/` (the v5.2.0 stack created earlier) into `job-hunter/docs/continuity/`, reframed for the family: session-state/compaction-handoff describe the family architecture + the split; decisions.md prepends the family-split decision; memory.md records the 6-skill layout + the workspace-contract + the anti-fabrication invariant. Same 11 files.

- [ ] **Step 2: Add a one-file continuity stub to each member**

Each `<member>/docs/continuity/README.md`: "This member is part of the job-hunter family. The shared continuity stack lives in the orchestrator at `job-hunter/docs/continuity/`. Member-specific notes (if any) below." (Per spec §6 — avoid 6× continuity duplication.)

- [ ] **Step 3: Verify validate.py passes on the orchestrator**

Run: `python C:/Users/Owner/.claude/skills/self-improving-skills/scripts/validate.py job-hunter 2>&1 | grep -c ERROR`
Expected: `0`.

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "stage-d: family continuity stack (orchestrator) + member stubs"
```

### Task D2: README + CHANGELOG + v6.0.0 + audit each member

**Files:**
- Modify: `README.md` (family overview)
- Modify: `CHANGELOG.md` (v6.0.0 entry)

- [ ] **Step 1: Rewrite README.md as a family overview**

Family description, the 6-skill table (member | role | job | scripts), how the orchestrator routes, the install command, the per-member triggering. Keep the v5.2.0 FAQ entries (fabrication fix etc.) — move them under resume-tailor's section.

- [ ] **Step 2: Add the v6.0.0 CHANGELOG entry**

Human-voice entry: "v6.0.0 — split the monolith into a 6-skill family (orchestrator + career-profile/job-search/resume-tailor/application-tracker/outcome-learning). Breaking structural change: install path is now the family installer. Phase 3's anti-fabrication gate moved intact into resume-tailor with all 5 load-bearing tests. No behavior regression — combined suite >= 201 tests." Note it's a major version because the install shape changed.

- [ ] **Step 3: Audit each member with the skill-builder audit**

```bash
cd E:/Git/job-hunter-public
for m in job-hunter career-profile job-search resume-tailor application-tracker outcome-learning; do
  echo "== $m =="; python C:/Users/Owner/.claude/skills/self-improving-skills/scripts/audit_existing.py --skill "$m" 2>&1 | grep "Full-stack score"
done
```
Expected: each member scores reasonably (≥12/15; orchestrator + members may flag body-length or dir-name like the monolith did — acceptable). Note any genuine gaps.

- [ ] **Step 4: Bump _meta versions + commit**

Ensure `job-hunter/_meta.json` is `6.0.0`; members `1.0.0`. Commit:
```bash
git add -A && git commit -m "stage-d: family README + v6.0.0 CHANGELOG + per-member audit"
```

### Task D3: OS-coupling guard across all 6 members

- [ ] **Step 1: Run the v1.42 os-coupling guard on each member**

```bash
cd E:/Git/job-hunter-public
for m in job-hunter career-profile job-search resume-tailor application-tracker outcome-learning; do
  echo -n "$m: "; python C:/Users/Owner/.claude/skills/self-improving-skills/scripts/script_audit.py "$m" --json 2>&1 | python -c "import json,sys; print(len([f for f in json.load(sys.stdin)['findings'] if f['category']=='os-coupling']),'os-coupling')"
done
```
Expected: `0 os-coupling` for every member (scripts were already clean; `.gitattributes` keeps them LF).

- [ ] **Step 2: Fix any finding (convert CRLF→LF, etc.), re-run until all 0**

- [ ] **Step 3: Commit (if any fix)**

```bash
git add -A && git commit -m "stage-d: confirm all 6 members os-coupling clean" --allow-empty
```

### Task D4: STOP — cutover-approval gate (do NOT proceed without user approval)

- [ ] **Step 1: Present the built family for cutover approval**

Summarize: the 6 skills, combined test count vs 201 baseline, each member's audit score, routing-eval results, the installer. State explicitly: "main's v5.2.0 is still intact; this is all on branch family-split. Approve to (a) delete the root-level monolith skill files [SKILL.md, scripts/, tests/, evals/, references/ at root], (b) merge family-split → main, (c) tag v6.0.0. Redeploy to install paths and any GitHub push remain separately gated."

- [ ] **Step 2: ON APPROVAL ONLY — remove the root monolith, merge, tag**

```bash
# Only after explicit user approval:
cd E:/Git/job-hunter-public
git rm -r SKILL.md scripts tests evals references _meta.json  # the root monolith (now superseded by job-hunter/ + members)
git commit -m "v6.0.0: retire root monolith; job-hunter is now a 6-skill family"
git checkout main && git merge --no-ff family-split -m "v6.0.0: job-hunter family split"
git tag v6.0.0
```
(Do NOT `git push`. Do NOT run the installer/redeploy. Those are separate, separately-approved steps.)

---

## Self-review notes
- **Spec coverage:** §2 architecture→A4/C3; §3 boundaries→A3,B1-B5; §4 hand-offs→A2 contract + each member's read/degrade; §5 safety gate→B3 (+ orchestrator invariant A4); §6 v1.42/Opus→B* descriptions + D3 + D1 continuity; §7 layout→A1; §8 installer→C4; §9 migration→branch-only + D4 gate; §10 staging→A/B/C/D; §11 risks→B3 safety-test preservation + C1 wiring + D4 gate. All covered.
- **Parity guard:** C2 enforces ≥201 tests; B3 adds an explicit load-bearing-preservation test for the 5 anti-fabrication tests.
- **No-push / no-redeploy / main-untouched:** stated in the header invariants and re-stated in D4.
