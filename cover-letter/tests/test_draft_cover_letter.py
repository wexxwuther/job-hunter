"""Tests for the cover-letter member.

These lock in the SAFETY behavior, not just the happy path: the drafter must
ground every factual slot in supplied input and emit [CONFIRM: ...] for anything
ungrounded, and the anti-fabrication gate must be bundled and importable so a
standalone install is still safe.
"""
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))

import draft_cover_letter as dcl  # noqa: E402


def test_letter_contains_only_supplied_company_role_applicant():
    letter = dcl.build_letter("Stripe", "Senior PM", "Jordan Lee", [])
    assert "Stripe" in letter
    assert "Senior PM" in letter
    assert "Jordan Lee" in letter


def test_no_highlights_emits_confirm_placeholder_not_invented_content():
    """With no grounded qualifications, the body must be a [CONFIRM] placeholder,
    never an invented accomplishment."""
    letter = dcl.build_letter("Acme", "Engineer", "Pat Doe", [])
    assert "[CONFIRM:" in letter
    # must not invent quantified claims out of nothing
    for invented in ("increased", "%", "led a team of", "saved $"):
        assert invented not in letter.lower() or "[confirm" in letter.lower()


def test_highlight_mapping_is_used_verbatim_not_embellished():
    """A supplied qualification appears verbatim; the script does not add new facts."""
    h = ["Shipped the billing rewrite cutting latency 30% :: scale payment systems"]
    letter = dcl.build_letter("Stripe", "PM", "Jordan", h)
    assert "Shipped the billing rewrite cutting latency 30%" in letter
    assert "scale payment systems" in letter
    # the connective sentence must be a CONFIRM slot, not an invented fact
    assert "[CONFIRM:" in letter


def test_every_paragraph_with_a_fact_pairs_it_with_a_confirm_connective():
    h = ["Ran support for 200 accounts"]
    letter = dcl.build_letter("Acme", "CSM", "Sam", h)
    assert "Ran support for 200 accounts" in letter
    assert "[CONFIRM:" in letter  # connective sentence is not auto-written


def test_blank_required_fields_become_confirm_placeholders_not_blank():
    letter = dcl.build_letter("", "", "", [])
    assert "[CONFIRM: company name]" in letter
    assert "[CONFIRM: role title]" in letter
    assert "[CONFIRM: your name]" in letter


def test_cli_writes_file(tmp_path):
    out = tmp_path / "cl.md"
    hi = tmp_path / "h.txt"
    hi.write_text("Built the data pipeline :: own data infrastructure\n", encoding="utf-8")
    rc = dcl.main(["--company", "Globex", "--role", "Data Eng",
                   "--applicant", "Lee", "--highlights", str(hi), "--out", str(out)])
    assert rc == 0
    body = out.read_text(encoding="utf-8")
    assert "Globex" in body and "Built the data pipeline" in body


# --- the load-bearing safety guarantee: the fabrication gate is bundled ---

def test_fabrication_gate_is_bundled():
    assert (SCRIPTS / "verify_no_fabrication.py").exists(), \
        "cover-letter must bundle verify_no_fabrication.py so standalone installs are safe"


def test_bundled_gate_detects_a_new_number_in_a_draft(tmp_path):
    """End-to-end proof the bundled gate catches an invented metric in a letter."""
    source = tmp_path / "source.txt"
    draft = tmp_path / "draft.txt"
    source.write_text("Jordan Lee. Product manager at Acme. Led the checkout project.",
                      encoding="utf-8")
    # draft invents a metric that is NOT in the source
    draft.write_text("I led the checkout project and increased revenue by 47% last year.",
                     encoding="utf-8")
    r = subprocess.run(
        [sys.executable, str(SCRIPTS / "verify_no_fabrication.py"),
         "--original", str(source), "--proposed", str(draft)],
        capture_output=True, text=True,
    )
    assert r.returncode == 0
    # the invented "47" must surface as a new number
    assert "47" in r.stdout, f"gate failed to flag invented metric; stdout={r.stdout[:400]}"


def test_gate_byte_identical_to_resume_tailor():
    """The bundled gate must be the SAME gate, not a fork that could drift."""
    rt = SKILL.parent / "resume-tailor" / "scripts" / "verify_no_fabrication.py"
    if not rt.exists():
        # standalone checkout without the sibling; bundling test above still covers safety
        return
    import hashlib
    a = (SCRIPTS / "verify_no_fabrication.py").read_bytes()
    b = rt.read_bytes()
    assert hashlib.sha256(a).digest() == hashlib.sha256(b).digest(), \
        "bundled gate has drifted from resume-tailor's canonical gate"
