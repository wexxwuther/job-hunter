"""Tests for load_application.py: unhappy paths first, then the happy path.

The reader is written against the producers' real shapes: tracker.json from
application-tracker (a list, or {"entries": [...]} as draft_followup.py
accepts) and LESSONS.md from the orchestrator's template, whose scaffolding
contains a "## YYYY-MM-DD" example ABOVE the append marker.
"""
import json
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parent.parent
SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))

import load_application as la  # noqa: E402

LESSONS_TEMPLATE = SKILL.parent / "job-hunter" / "assets" / "templates" / "LESSONS.template.md"


def _template() -> str:
    if not LESSONS_TEMPLATE.exists():
        pytest.skip("standalone checkout without the orchestrator's LESSONS template")
    return LESSONS_TEMPLATE.read_text(encoding="utf-8")


def _tracker(tmp_path, entries):
    path = tmp_path / "tracker.json"
    path.write_text(json.dumps(entries), encoding="utf-8")
    return path


def _globex(**extra):
    entry = {"company": "Globex Corp", "title": "Senior Data Analyst", "status": "interviewing",
             "url": "https://globex.example/jobs/42", "resume_file": "Resume_Globex.md",
             "cover_letter_file": "CoverLetter_Globex.md"}
    entry.update(extra)
    return entry


def _run(*args):
    return subprocess.run([sys.executable, str(SCRIPTS / "load_application.py"), *args],
                          capture_output=True, text=True)


# --- unhappy paths -----------------------------------------------------------

def test_missing_tracker_exits_2_with_a_question(tmp_path):
    r = _run("--tracker", str(tmp_path / "nope.json"), "--company", "Globex")
    assert r.returncode == 2
    assert "tracker not found" in json.loads(r.stdout)["error"]


def test_malformed_tracker_exits_2(tmp_path):
    bad = tmp_path / "tracker.json"
    bad.write_text("{not json", encoding="utf-8")
    r = _run("--tracker", str(bad), "--company", "Globex")
    assert r.returncode == 2
    assert "not valid JSON" in json.loads(r.stdout)["error"]


def test_tracker_of_wrong_shape_exits_2(tmp_path):
    r = _run("--tracker", str(_tracker(tmp_path, {"company": "Globex"})), "--company", "Globex")
    assert r.returncode == 2


def test_no_match_lists_candidates(tmp_path):
    r = _run("--tracker", str(_tracker(tmp_path, [_globex()])), "--company", "Initech")
    assert r.returncode == 2
    out = json.loads(r.stdout)
    assert out["candidates"][0]["company"] == "Globex Corp"


def test_ambiguous_match_asks_instead_of_guessing(tmp_path):
    entries = [_globex(), _globex(title="Data Engineer")]
    r = _run("--tracker", str(_tracker(tmp_path, entries)), "--company", "globex")
    assert r.returncode == 2
    assert len(json.loads(r.stdout)["candidates"]) == 2


def test_role_filter_resolves_ambiguity(tmp_path):
    entries = [_globex(), _globex(title="Data Engineer")]
    ctx = la.build_context(_tracker(tmp_path, entries), company="Globex", role="engineer")
    assert ctx["tracker_index"] == 1


def test_bad_index_exits_2(tmp_path):
    r = _run("--tracker", str(_tracker(tmp_path, [_globex()])), "--index", "5")
    assert r.returncode == 2


@pytest.mark.parametrize("status", ["rejected", "withdrawn", "applied", "to apply", "offer",
                                    "no_response_after_21d", "mystery"])
def test_non_interviewing_status_warns_and_asks_to_confirm(tmp_path, status):
    ctx = la.build_context(_tracker(tmp_path, [_globex(status=status)]), company="Globex")
    assert ctx["status_is_interviewing"] is False
    assert any("onfirm" in w for w in ctx["warnings"])


def test_missing_submitted_documents_warn_not_crash(tmp_path):
    ctx = la.build_context(_tracker(tmp_path, [_globex()]), company="Globex")
    assert ctx["documents"]["resume"]["found"] is False
    assert any("resume_file not found" in w for w in ctx["warnings"])


def test_entry_without_document_fields_warns(tmp_path):
    entry = _globex()
    del entry["resume_file"], entry["cover_letter_file"]
    ctx = la.build_context(_tracker(tmp_path, [entry]), company="Globex")
    assert any("no resume_file" in w for w in ctx["warnings"])


def test_unsupported_document_type_is_not_read(tmp_path):
    (tmp_path / "Resume.exe").write_bytes(b"MZ")
    ctx = la.build_context(_tracker(tmp_path, [_globex(resume_file="Resume.exe")]),
                           company="Globex")
    assert ctx["documents"]["resume"]["found"] is False
    assert "unsupported type" in ctx["documents"]["resume"]["warning"]


def test_corrupt_docx_warns_not_crash(tmp_path):
    (tmp_path / "Resume.docx").write_bytes(b"not a zip")
    ctx = la.build_context(_tracker(tmp_path, [_globex(resume_file="Resume.docx")]),
                           company="Globex")
    assert ctx["documents"]["resume"]["found"] is False


def test_no_posting_tells_agent_to_ask(tmp_path):
    ctx = la.build_context(_tracker(tmp_path, [_globex()]), company="Globex")
    assert ctx["posting"]["source"] == "none"
    assert any("paste the posting" in w for w in ctx["warnings"])


def test_lessons_template_scaffolding_is_not_read_as_lessons(tmp_path):
    """The template has a '## YYYY-MM-DD' example above the marker; it is not a lesson."""
    (tmp_path / ".job-hunter").mkdir()
    (tmp_path / ".job-hunter" / "LESSONS.md").write_text(_template(), encoding="utf-8")
    ctx = la.build_context(_tracker(tmp_path, [_globex()]), company="Globex")
    assert ctx["lessons"] == []


def test_lessons_without_marker_are_skipped_with_warning(tmp_path):
    (tmp_path / ".job-hunter").mkdir()
    (tmp_path / ".job-hunter" / "LESSONS.md").write_text("## 2026-01-01: x\n", encoding="utf-8")
    ctx = la.build_context(_tracker(tmp_path, [_globex()]), company="Globex")
    assert ctx["lessons"] == []
    assert any("append marker" in w for w in ctx["warnings"])


def test_never_writes_the_tracker(tmp_path):
    tracker = _tracker(tmp_path, [_globex(status="applied")])
    before = tracker.read_bytes()
    r = _run("--tracker", str(tracker), "--company", "Globex", "--out",
             str(tmp_path / "ctx.json"))
    assert r.returncode == 0
    assert tracker.read_bytes() == before
    source = (SCRIPTS / "load_application.py").read_text(encoding="utf-8")
    assert "tracker_path.write" not in source and "args.tracker.write" not in source


# --- happy path --------------------------------------------------------------

def test_reads_submitted_documents_posting_urls_and_confirmed_lessons(tmp_path):
    (tmp_path / "Resume_Globex.md").write_text("- Built weekly SQL reports\n", encoding="utf-8")
    (tmp_path / "CoverLetter_Globex.md").write_text("Dear Globex team.\n", encoding="utf-8")
    posting = tmp_path / "posting.txt"
    posting.write_text("Apply at https://globex.example/apply?ref=1 now.\n- SQL\n",
                       encoding="utf-8")
    (tmp_path / ".job-hunter").mkdir()
    (tmp_path / ".job-hunter" / "LESSONS.md").write_text(
        _template()
        + "\n## 2026-09-01: Lead with the result\n\n**Pattern:** callbacks rise\n",
        encoding="utf-8")
    ctx = la.build_context(_tracker(tmp_path, [_globex()]), company="GLOBEX, Inc.",
                           posting=posting)
    assert ctx["documents"]["resume"]["text"].startswith("- Built weekly SQL reports")
    assert ctx["documents"]["cover_letter"]["found"] is True
    assert ctx["posting_urls_do_not_open"] == ["https://globex.example/apply?ref=1"]
    assert ctx["lessons"] == [{"heading": "2026-09-01: Lead with the result",
                               "body": "**Pattern:** callbacks rise"}]
    assert ctx["warnings"] == []


def test_entries_wrapper_shape_is_accepted(tmp_path):
    ctx = la.build_context(_tracker(tmp_path, {"entries": [_globex()]}), company="Globex")
    assert ctx["application"]["company"] == "Globex Corp"


def test_docx_text_is_read_with_stdlib(tmp_path):
    w = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    xml = (f'<w:document xmlns:w="{w}"><w:body>'
           '<w:p><w:r><w:t>Pat Doe</w:t></w:r></w:p>'
           '<w:p><w:r><w:t>Built weekly </w:t></w:r><w:r><w:t>SQL reports</w:t></w:r></w:p>'
           '</w:body></w:document>')
    with zipfile.ZipFile(tmp_path / "Resume.docx", "w") as z:
        z.writestr("word/document.xml", xml)
    ctx = la.build_context(_tracker(tmp_path, [_globex(resume_file="Resume.docx")]),
                           company="Globex")
    assert ctx["documents"]["resume"]["text"] == "Pat Doe\nBuilt weekly SQL reports"


def test_postings_summary_is_a_partial_fallback(tmp_path):
    postings = tmp_path / "postings.json"
    postings.write_text(json.dumps([{"url": "https://globex.example/jobs/42",
                                     "summary": "Needs SQL."}]), encoding="utf-8")
    ctx = la.build_context(_tracker(tmp_path, [_globex()]), company="Globex", postings=postings)
    assert ctx["posting"]["text"] == "Needs SQL."
    assert "partial" in ctx["posting"]["source"]


def test_posting_url_loses_trailing_sentence_punctuation(tmp_path):
    """Live trial: 'see https://x.example/culture.' was listed with the period."""
    posting = tmp_path / "posting.txt"
    posting.write_text("Learn about us at https://globex-careers.example/culture. Thanks.\n",
                       encoding="utf-8")
    ctx = la.build_context(_tracker(tmp_path, [_globex()]), company="Globex", posting=posting)
    assert ctx["posting_urls_do_not_open"] == ["https://globex-careers.example/culture"]
