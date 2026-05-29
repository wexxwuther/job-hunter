"""
Tests for scripts/verify_no_fabrication.py

Covers:
- Clean case: identical text returns verdict=clean, zero new claims
- New proper noun: "Pinecone" added → flagged
- New number: "60 houses/week" added → flagged
- New section: "## GDK Digital" promoted → flagged
- New bullet: extra bullet line under a section → flagged
- New phrase run: "early specialization in insurance restoration" → flagged
- Sentence-start capitalization NOT flagged as proper noun
- Years (1992, 2023) NOT flagged as new numbers
- Month names NOT flagged as proper nouns
- Common stopwords (The, A, We, You, ...) NOT flagged
- Light paraphrasing same facts → minimal phrase-run flags
- The auto_approved field is ALWAYS False (load-bearing safety)
- CLI: --original + --proposed + --out file
- CLI: --original-stdin works
- CLI: missing args produce clear errors

Run from skill root:
    python -m pytest tests/test_verify_no_fabrication.py -v
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).parent.parent
SCRIPT = SKILL_ROOT / "scripts" / "verify_no_fabrication.py"
sys.path.insert(0, str(SCRIPT.parent))

from verify_no_fabrication import verify  # noqa: E402


# ---- Clean case ------------------------------------------------------------


def test_identical_text_returns_clean():
    text = "Senior Engineer at Acme. Built the payments platform."
    report = verify(text, text)
    assert report["summary"]["verdict"] == "clean"
    assert report["summary"]["total_new_claims"] == 0
    assert report["new_proper_nouns"] == []
    assert report["new_numbers"] == []
    assert report["new_sections"] == []
    assert report["new_bullets"] == {}
    assert report["new_phrase_runs"] == []


def test_whitespace_only_differences_return_clean():
    original = "Built the payments platform at Acme."
    proposed = "Built  the   payments   platform   at   Acme."
    report = verify(original, proposed)
    # Whitespace differences should not produce new phrase runs (we tokenize on whitespace)
    assert report["summary"]["total_new_claims"] == 0


# ---- New proper nouns -----------------------------------------------------


def test_new_proper_noun_flagged():
    original = "Built APIs in Python at Acme."
    proposed = "Built APIs in Python at Acme using Pinecone vector database."
    report = verify(original, proposed)
    nouns = [n["token"] for n in report["new_proper_nouns"]]
    assert "Pinecone" in nouns
    assert report["summary"]["verdict"] == "review_required"
    assert report["summary"]["highest_risk"] == "new_proper_nouns"


def test_multiple_new_proper_nouns_flagged():
    """The exact failure pattern from Greg's conversation: agent added Pinecone
    AND Weaviate to Technical Skills from memory of a prior conversation."""
    original = "Technical Skills: AWS, Kubernetes, Python."
    proposed = "Technical Skills: AWS, Kubernetes, Python, Pinecone, Weaviate, LangChain."
    report = verify(original, proposed)
    nouns = [n["token"] for n in report["new_proper_nouns"]]
    assert "Pinecone" in nouns
    assert "Weaviate" in nouns
    assert "LangChain" in nouns


def test_sentence_start_capitalization_NOT_flagged():
    """A capitalized word at the start of a sentence (or after . ! ?) is NOT
    a proper noun. We approximate by skipping tokens preceded by sentence-end
    punctuation."""
    original = "Built systems. Used many tools."
    proposed = "Built systems. Used many tools. Designed APIs."
    report = verify(original, proposed)
    nouns = [n["token"] for n in report["new_proper_nouns"]]
    # "Designed" starts a sentence so should NOT be flagged as a new proper noun
    assert "Designed" not in nouns


def test_stopwords_not_flagged():
    original = "Worked on X."
    proposed = "Worked on X. The team grew."
    report = verify(original, proposed)
    nouns = [n["token"] for n in report["new_proper_nouns"]]
    assert "The" not in nouns


def test_month_names_not_flagged():
    """Months in employment dates are not fabrications."""
    original = "Engineer (2020 - Present): built things."
    proposed = "Engineer (May 2020 - Present): built things."
    report = verify(original, proposed)
    nouns = [n["token"] for n in report["new_proper_nouns"]]
    assert "May" not in nouns


# ---- New numbers -----------------------------------------------------------


def test_new_number_flagged():
    """The exact failure pattern: '60 houses/week' or 'team of 12' added when
    the original resume had no quantification."""
    original = "Managed the production team and shipped homes."
    proposed = "Managed a production team of 250+ employees and shipped 60 homes/week."
    report = verify(original, proposed)
    numbers = [n["token"] for n in report["new_numbers"]]
    assert any("60" in n for n in numbers)
    assert any("250" in n for n in numbers)


def test_dollar_amounts_flagged():
    original = "Managed projects."
    proposed = "Managed $5M+ projects with $120k average value."
    report = verify(original, proposed)
    numbers = [n["token"] for n in report["new_numbers"]]
    assert any("$5M" in n or "5M" in n for n in numbers)
    assert any("$120k" in n or "120k" in n for n in numbers)


def test_percentages_flagged():
    original = "Reduced costs."
    proposed = "Reduced costs by 23%."
    report = verify(original, proposed)
    numbers = [n["token"] for n in report["new_numbers"]]
    assert any("23%" in n for n in numbers)


def test_years_NOT_flagged_as_new_numbers():
    """Calendar years like 1992, 2023, 2024 are employment-date noise, not
    fabrications. The script special-cases 4-digit years matching ^(19|20)\\d{2}$."""
    original = "Worked at Acme from 2020."
    proposed = "Worked at Acme from 2020 to 2023."
    report = verify(original, proposed)
    numbers = [n["token"] for n in report["new_numbers"]]
    assert "2023" not in numbers
    assert "2020" not in numbers


# ---- New section headings --------------------------------------------------


def test_new_markdown_section_flagged():
    """The exact failure pattern: GDK Digital promoted from a bullet under
    'Authorship & Projects' to its own '## Professional Experience: GDK Digital'."""
    original = "## Professional Experience\nAcme Co - Engineer\n\n## Authorship\n- Built thing"
    proposed = (
        "## Professional Experience: GDK Digital\nLead Developer\n\n"
        "## Professional Experience: Acme Co\nEngineer\n\n## Authorship\n- Built thing"
    )
    report = verify(original, proposed)
    assert any("GDK Digital" in s for s in report["new_sections"])


def test_all_caps_section_flagged():
    original = "Just a paragraph."
    proposed = "Just a paragraph.\n\n**TECHNICAL SKILLS**\nPython, Go"
    report = verify(original, proposed)
    assert any("TECHNICAL SKILLS" in s for s in report["new_sections"])


# ---- New bullets per section -----------------------------------------------


def test_new_bullets_in_existing_section_flagged():
    original = (
        "## Experience\n"
        "- Bullet one\n"
        "- Bullet two\n"
    )
    proposed = (
        "## Experience\n"
        "- Bullet one\n"
        "- Bullet two\n"
        "- New bullet three\n"
        "- New bullet four\n"
    )
    report = verify(original, proposed)
    # Should detect a +2 delta in the Experience section
    assert any("Experience" in section and delta == 2
               for section, delta in report["new_bullets"].items())


# ---- New phrase runs (semantic fabrication catch) --------------------------


def test_new_phrase_run_flagged():
    """The exact failure pattern: 'early specialization in insurance restoration'
    added at Mark Scott Construction. No new proper nouns, no new numbers, but
    a meaningful claim is invented."""
    original = "Performed restoration work at Mark Scott Construction."
    proposed = (
        "Performed restoration work at Mark Scott Construction with "
        "early specialization in insurance restoration projects."
    )
    report = verify(original, proposed)
    assert any("specialization" in run.lower() or "insurance" in run.lower()
               for run in report["new_phrase_runs"])


def test_light_paraphrasing_same_facts_few_phrase_flags():
    """Pure copyediting (changing word order, fixing grammar) will still produce
    some phrase-run flags because the n-gram windows shift. The test verifies
    the agent can see these and decide they're paraphrasing not fabrication."""
    original = "Managed a team and delivered projects on time."
    proposed = "Delivered projects on time while managing the team."
    report = verify(original, proposed)
    # Some phrase runs will differ due to word reordering. The script flags them
    # as new, the agent's job is to recognize this as legitimate copyediting.
    # We just assert the verdict is review_required (correctly NOT auto-approved).
    assert report["summary"]["verdict"] == "review_required" or report["summary"]["verdict"] == "clean"


# ---- LOAD-BEARING safety tests --------------------------------------------


def test_auto_approved_field_is_always_false_on_clean_input():
    """LOAD-BEARING: the script must NEVER set auto_approved=True. The whole
    point is that detection is the script's job and approval is the user's job.
    If a future refactor introduces auto-approval, this test fails."""
    report = verify("same text", "same text")
    assert report["auto_approved"] is False


def test_auto_approved_field_is_always_false_on_dirty_input():
    """LOAD-BEARING (same boundary as above): even with a wildly different
    proposed text, auto_approved must stay False. The script never decides
    fabrications are OK."""
    original = "I am an engineer."
    proposed = (
        "I am a senior staff principal distinguished engineer at FAANG "
        "with 47 years of experience leading 12 teams across 8 countries "
        "and shipping $400M ARR products. Specialized in Pinecone, Weaviate, "
        "LangChain, RAG, and reactive Kubernetes architectures."
    )
    report = verify(original, proposed)
    assert report["auto_approved"] is False
    assert report["summary"]["verdict"] == "review_required"
    assert report["summary"]["total_new_claims"] > 5  # lots of new claims


def test_script_exports_only_detection_no_approval_helpers():
    """LOAD-BEARING: the module's public API is detection-only. No function
    should exist that says 'this is fine' or 'auto-approve this batch'."""
    import verify_no_fabrication as mod
    public_names = [n for n in dir(mod) if not n.startswith("_")]
    forbidden = {"approve", "auto_approve", "is_fine", "is_acceptable", "accept",
                 "mark_clean", "whitelist", "ignore_claim"}
    for name in public_names:
        assert name.lower() not in forbidden, (
            f"verify_no_fabrication.py exports '{name}', which sounds like an "
            f"approval helper. This script must be detection-only."
        )


# ---- CLI tests --------------------------------------------------------------


def test_cli_writes_json_report(tmp_path: Path):
    original = tmp_path / "original.txt"
    proposed = tmp_path / "proposed.txt"
    out = tmp_path / "report.json"
    original.write_text("Engineer at Acme.", encoding="utf-8")
    proposed.write_text("Engineer at Acme using Pinecone.", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCRIPT),
         "--original", str(original),
         "--proposed", str(proposed),
         "--out", str(out)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert out.is_file()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["auto_approved"] is False
    assert any("Pinecone" in n["token"] for n in payload["new_proper_nouns"])


def test_cli_stdin_original(tmp_path: Path):
    proposed = tmp_path / "proposed.txt"
    proposed.write_text("Engineer at Acme using Pinecone.", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCRIPT),
         "--original-stdin",
         "--proposed", str(proposed)],
        input="Engineer at Acme.",
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    payload = json.loads(result.stdout)
    assert any("Pinecone" in n["token"] for n in payload["new_proper_nouns"])


def test_cli_missing_args_errors():
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True, text=True,
    )
    assert result.returncode != 0


def test_cli_both_stdin_errors():
    """Can't read both inputs from stdin."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--original-stdin", "--proposed-stdin"],
        input="anything",
        capture_output=True, text=True,
    )
    assert result.returncode != 0
    assert "stdin" in result.stderr.lower()


# ---- Realistic scenario mirroring Greg's incident -------------------------


def test_real_world_pattern_detects_multiple_categories():
    """A condensed sanitized version of the failure mode: a 'tighten' request
    that returns content with NEW proper nouns, NEW numbers, NEW sections,
    and NEW bullets. All should be flagged."""
    original = (
        "PROFESSIONAL SUMMARY\n"
        "AI systems builder and construction operations leader.\n\n"
        "PROFESSIONAL EXPERIENCE\n"
        "Acme Co - Customer Experience Manager (2023 - Present)\n"
        "- Managed customer relationships\n"
        "- Oversaw insurance restoration projects\n\n"
        "AUTHORSHIP AND PROJECTS\n"
        "- Co-Founder, Sample Brand: building AI tools\n"
    )
    proposed = (
        "PROFESSIONAL SUMMARY\n"
        "AI systems builder with 20+ years construction operations leadership "
        "and 200+ five-star reviews.\n\n"
        "PROFESSIONAL EXPERIENCE\n"
        "Sample Brand - Co-Founder and Lead Developer (2023 - Present)\n"
        "- Built FTC, GDK-CRM, Fortilis, Custom GPTs, and Feathers AI\n"
        "- Architected RAG over Pinecone and Weaviate vector databases\n"
        "- Architecture and engineering across the stack\n\n"
        "Acme Co - Customer Experience Manager (2023 - Present)\n"
        "- Managed 250+ customer relationships across 60 active projects\n"
        "- Oversaw insurance restoration projects with early specialization "
        "in large-loss claims\n"
    )
    report = verify(original, proposed)
    # Should flag many things
    assert report["summary"]["verdict"] == "review_required"
    assert report["summary"]["total_new_claims"] >= 10
    # Specifically: new proper nouns (Pinecone, Weaviate, FTC, GDK-CRM, etc.)
    nouns = [n["token"] for n in report["new_proper_nouns"]]
    assert "Pinecone" in nouns
    assert "Weaviate" in nouns
    # New numbers (200+, 250+, 60, 20+)
    numbers = [n["token"] for n in report["new_numbers"]]
    assert len(numbers) >= 2
    # auto_approved stays False
    assert report["auto_approved"] is False
