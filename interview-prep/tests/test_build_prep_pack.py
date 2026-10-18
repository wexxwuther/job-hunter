"""Tests for build_prep_pack.py.

These lock in the SAFETY contract, not just the layout:
  - every line the user would say is a blockquote, and only those reach the gate;
  - a gap bridge never claims the missing requirement;
  - the bundled gate catches an invented tool and metric in a filled answer;
  - research from a posting URL, without a source, or about an interviewer's
    personal life never lands as verified research.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parent.parent
SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))

import build_prep_pack as bpp  # noqa: E402

RESUME = ("Pat Doe\nData Analyst, Acme Corp, 2021-2024\n"
          "- Built weekly SQL reports for the sales team\n"
          "- Trained four new analysts on the reporting process\n")
POSTING = ("Senior Data Analyst at Globex. Apply at https://globex.example/apply?ref=x\n"
           "Requirements:\n- Advanced SQL and reporting experience\n"
           "- Build Looker dashboards for executives\n- Train and mentor junior analysts\n")


def _context(posting=POSTING, resume=RESUME, letter="", **extra):
    ctx = {
        "application": {"company": "Globex Corp", "title": "Senior Data Analyst"},
        "documents": {"resume": {"found": bool(resume), "text": resume},
                      "cover_letter": {"found": bool(letter), "text": letter}},
        "posting": {"text": posting},
        "posting_urls_do_not_open": ["https://globex.example/apply?ref=x"],
        "lessons": [], "warnings": [],
    }
    ctx.update(extra)
    return ctx


def _section(pack, heading_start):
    lines = pack.splitlines()
    start = next(i for i, ln in enumerate(lines) if ln.startswith(heading_start))
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("#")), len(lines))
    return "\n".join(lines[start:end])


# --- unhappy paths -----------------------------------------------------------

def test_unknown_stage_is_rejected():
    with pytest.raises(ValueError):
        bpp.build_pack(_context(), "tea_chat")


def test_no_posting_says_to_ask_for_it():
    pack = bpp.build_pack(_context(posting=""), "hiring_manager")
    assert "Ask the user to paste the posting text" in pack


def test_no_resume_means_no_starting_points_and_only_confirm_slots():
    pack = bpp.build_pack(_context(resume=""), "behavioral_panel")
    assert "Starting point" not in pack
    claims = bpp.extract_claims(pack)
    assert claims["unresolved_confirm"] > 0


def test_context_warnings_are_shown_first():
    pack = bpp.build_pack(_context(warnings=["Tracker says 'rejected'."]), "final")
    assert pack.index("## Check first") < pack.index("## Opener")


def test_gap_bridge_never_claims_the_missing_requirement():
    pack = bpp.build_pack(_context(), "hiring_manager")
    gap = _section(pack, "### 2. Build Looker dashboards")
    assert "(gap:" in gap
    said = [ln for ln in gap.splitlines() if ln.startswith(">")]
    assert said, "a gap must still offer an honest bridge answer"
    for line in said:
        assert "Looker" not in line and "dashboard" not in line.lower()
    assert "have not worked in directly" in gap


def test_research_from_a_posting_url_is_rejected():
    posting_urls = ["https://globex.example/apply?ref=x"]
    for variant in ("https://globex.example/apply?ref=x", "HTTPS://Globex.example/apply/",
                    "https://globex.example/apply?ref=other#top"):
        screened = bpp.screen_research([{"claim": "Remote-first culture",
                                         "source_url": variant}], posting_urls)
        assert screened["verified"] == [], variant
        assert "inside the posting" in screened["rejected"][0]["reason"]
    other_page = bpp.screen_research([{"claim": "Founded 1999",
                                       "source_url": "https://globex.example/about"}],
                                     posting_urls)
    assert other_page["verified"], "an independently found page on the same site is allowed"


def test_research_without_source_is_unverified_not_verified():
    screened = bpp.screen_research([{"claim": "CEO is Jane"}], [])
    assert screened["verified"] == [] and screened["unverified"][0]["claim"] == "CEO is Jane"


def test_interviewer_personal_details_are_rejected():
    notes = [{"claim": "Has two kids and lives in Denver", "about": "interviewer",
              "source_url": "https://people.example/x"}]
    screened = bpp.screen_research(notes, [])
    assert screened["verified"] == [] and screened["rejected"]


def test_non_http_source_and_malformed_notes_are_rejected():
    screened = bpp.screen_research([{"claim": "x", "source_url": "file:///etc/passwd"},
                                    "just a string", {"source_url": "https://a.example"}], [])
    assert screened["verified"] == [] and len(screened["rejected"]) == 3


def test_research_never_becomes_a_claim():
    notes = [{"claim": "Globex opened a Denver office", "source_url": "https://news.example/a"}]
    pack = bpp.build_pack(_context(), "final", research=notes)
    assert "Globex opened a Denver office" in pack
    assert all("Denver" not in c for c in bpp.extract_claims(pack)["claims"])


def test_claims_exit_3_while_confirm_slots_remain(tmp_path):
    pack = tmp_path / "pack.md"
    pack.write_text(bpp.build_pack(_context(), "skills"), encoding="utf-8")
    r = subprocess.run([sys.executable, str(SCRIPTS / "build_prep_pack.py"), "claims",
                        "--pack", str(pack), "--out", str(tmp_path / "claims.txt")],
                       capture_output=True, text=True)
    assert r.returncode == 3
    assert json.loads(r.stdout)["gate_still_required"] is True


def test_bad_context_file_exits_2(tmp_path):
    bad = tmp_path / "ctx.json"
    bad.write_text("{", encoding="utf-8")
    r = subprocess.run([sys.executable, str(SCRIPTS / "build_prep_pack.py"), "build",
                        "--context", str(bad), "--stage", "skills", "--out",
                        str(tmp_path / "p.md"), "--source-out", str(tmp_path / "s.txt")],
                       capture_output=True, text=True)
    assert r.returncode == 2


# --- the gate ----------------------------------------------------------------

def test_fabrication_gate_is_bundled():
    assert (SCRIPTS / "verify_no_fabrication.py").exists(), \
        "interview-prep must bundle verify_no_fabrication.py so standalone installs are safe"


def test_gate_byte_identical_to_resume_tailor():
    rt = SKILL.parent / "resume-tailor" / "scripts" / "verify_no_fabrication.py"
    if not rt.exists():
        return  # standalone checkout; the bundling test still covers safety
    a = (SCRIPTS / "verify_no_fabrication.py").read_bytes()
    assert hashlib.sha256(a).digest() == hashlib.sha256(rt.read_bytes()).digest(), \
        "bundled gate has drifted from resume-tailor's canonical gate"


def test_gate_catches_an_invented_tool_and_metric_in_a_filled_answer(tmp_path):
    """End to end: a filled answer that claims Looker and a 40% win must be flagged."""
    ctx = _context()
    pack = bpp.build_pack(ctx, "hiring_manager")
    filled = pack.replace("> **Result:** [CONFIRM: what happened - only numbers you can stand "
                          "behind]", "> **Result:** My Looker dashboards cut report time 40%.", 1)
    (tmp_path / "pack.md").write_text(filled, encoding="utf-8")
    (tmp_path / "source.txt").write_text(bpp.build_source(ctx), encoding="utf-8")
    subprocess.run([sys.executable, str(SCRIPTS / "build_prep_pack.py"), "claims", "--pack",
                    str(tmp_path / "pack.md"), "--out", str(tmp_path / "claims.txt")],
                   capture_output=True, text=True)
    r = subprocess.run([sys.executable, str(SCRIPTS / "verify_no_fabrication.py"),
                        "--original", str(tmp_path / "source.txt"),
                        "--proposed", str(tmp_path / "claims.txt")],
                       capture_output=True, text=True)
    report = json.loads(r.stdout)
    assert "Looker" in [x["token"] for x in report["new_proper_nouns"]]
    assert any("40" in x["token"] for x in report["new_numbers"])
    assert report["auto_approved"] is False


def test_unfilled_pack_claims_are_only_real_resume_lines_or_bridge_wording():
    ctx = _context()
    claims = bpp.extract_claims(bpp.build_pack(ctx, "hiring_manager"))["claims"]
    source = bpp.build_source(ctx)
    for claim in claims:
        assert claim in source or "worked in directly" in claim or "closest thing" in claim, \
            f"pack put an ungrounded line in the user's mouth: {claim!r}"


# --- happy path --------------------------------------------------------------

def test_requirements_map_to_the_users_real_lines():
    pack = bpp.build_pack(_context(), "hiring_manager")
    sql = _section(pack, "### 1. Advanced SQL")
    assert "Built weekly SQL reports for the sales team" in sql
    train = _section(pack, "### 3. Train and mentor")
    assert "Trained four new analysts" in train


def test_every_stage_builds_and_has_questions_to_ask():
    for stage in bpp.STAGES:
        pack = bpp.build_pack(_context(), stage)
        assert "## Questions to ask them" in pack
        assert bpp.STAGES[stage]["label"] in pack


def test_only_blockquote_lines_are_claims_and_labels_are_stripped():
    pack = "Question?\n> **Action:** I built the report.\n- tip\n> [CONFIRM: x]\n"
    result = bpp.extract_claims(pack)
    assert result == {"claims": ["I built the report."], "unresolved_confirm": 1}


def test_lessons_are_quoted_verbatim():
    lesson = {"heading": "2026-09-01: Lead with the result", "body": "**Pattern:** callbacks"}
    pack = bpp.build_pack(_context(lessons=[lesson]), "recruiter_screen")
    assert "2026-09-01: Lead with the result" in pack and "**Pattern:** callbacks" in pack


def test_cli_build_writes_pack_and_source(tmp_path):
    ctx = tmp_path / "ctx.json"
    ctx.write_text(json.dumps(_context()), encoding="utf-8")
    facts = tmp_path / "facts.txt"
    facts.write_text("- I volunteer teaching Excel at the library\n", encoding="utf-8")
    r = subprocess.run([sys.executable, str(SCRIPTS / "build_prep_pack.py"), "build",
                        "--context", str(ctx), "--stage", "behavioral_panel", "--facts",
                        str(facts), "--out", str(tmp_path / "p.md"), "--source-out",
                        str(tmp_path / "s.txt")], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert "I volunteer teaching Excel at the library" in (tmp_path / "s.txt").read_text(
        encoding="utf-8")
    assert (tmp_path / "p.md").read_text(encoding="utf-8").startswith("# Interview prep:")


def test_mock_question_order_opens_and_closes():
    items = bpp.question_list(_context(), "behavioral_panel", 6)
    assert items[0]["kind"] == "opener" and items[-1]["kind"] == "closer"
    assert len(items) == 6
    assert any(i["kind"] == "requirement" for i in items)


# --- regressions from the 2026-10-18 live trial ---------------------------------

def test_tenure_requirement_is_never_keyword_matched_to_a_line():
    """Live trial: '5+ years in an analytics role' was seeded with 'Trained four new
    analysts' on one shared word. Dates are the user's arithmetic, never a match."""
    posting = POSTING + "- 5+ years in an analytics role\n"
    pack = bpp.build_pack(_context(posting=posting), "hiring_manager")
    tenure = _section(pack, "### 4. 5+ years")
    assert "time requirement" in tenure
    assert "Starting point" not in tenure and "Trained four new analysts" not in tenure
    for line in (ln for ln in tenure.splitlines() if ln.startswith(">")):
        assert "5" not in bpp.CONFIRM_RE.sub("", line)


def test_one_shared_word_is_not_a_match():
    rows = bpp.map_requirements(["Experience with payroll analytics"],
                                [{"text": "Trained four new analysts on reports",
                                  "origin": "resume"}])
    assert rows[0]["evidence"] is None


def test_questions_to_ask_skip_gap_requirements():
    pack = bpp.build_pack(_context(), "hiring_manager")
    ask = _section(pack, "## Questions to ask them")
    assert "Looker" not in ask
    assert "Advanced SQL" in ask


def test_build_refuses_to_overwrite_a_filled_pack(tmp_path):
    ctx = tmp_path / "ctx.json"
    ctx.write_text(json.dumps(_context()), encoding="utf-8")
    pack = tmp_path / "p.md"
    pack.write_text("> my filled answer\n", encoding="utf-8")
    r = subprocess.run([sys.executable, str(SCRIPTS / "build_prep_pack.py"), "build",
                        "--context", str(ctx), "--stage", "skills", "--out", str(pack),
                        "--source-out", str(tmp_path / "s.txt")], capture_output=True, text=True)
    assert r.returncode == 2 and "refusing to overwrite" in r.stderr
    assert pack.read_text(encoding="utf-8") == "> my filled answer\n"


def test_source_subcommand_refreshes_facts_without_touching_the_pack(tmp_path):
    ctx = tmp_path / "ctx.json"
    ctx.write_text(json.dumps(_context()), encoding="utf-8")
    facts = tmp_path / "facts.txt"
    facts.write_text("I have built charts in Excel for the sales managers.\n", encoding="utf-8")
    pack = tmp_path / "p.md"
    pack.write_text("> my filled answer\n", encoding="utf-8")
    r = subprocess.run([sys.executable, str(SCRIPTS / "build_prep_pack.py"), "source",
                        "--context", str(ctx), "--facts", str(facts), "--out",
                        str(tmp_path / "s.txt")], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    source = (tmp_path / "s.txt").read_text(encoding="utf-8")
    assert "charts in Excel" in source and "Built weekly SQL reports" in source
    assert pack.read_text(encoding="utf-8") == "> my filled answer\n"
