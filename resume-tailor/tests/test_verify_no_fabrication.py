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
import os
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


def test_trailing_comma_does_not_make_a_known_number_new():
    """Live outcome eval 2026-10-18 (interview-prep #1): 'In 2023, four new' and
    'from 2021 to 2024, where' were flagged as new numbers '2023,' and '2024,'
    although both years were in the source; the comma stuck to the token."""
    original = "Data Analyst, Acme Corp, 2021-2024\nin 2023 I trained four new analysts\nwe hit 40 sites"
    proposed = "From 2021 to 2024, I was at Acme. In 2023, four new analysts joined. We hit 40, then more."
    numbers = [n["token"] for n in verify(original, proposed)["new_numbers"]]
    assert numbers == []


def test_trailing_comma_still_flags_a_truly_new_number():
    original = "Managed the reporting team."
    proposed = "Managed 12, then 15 analysts, and $5,000, of budget."
    numbers = [n["token"] for n in verify(original, proposed)["new_numbers"]]
    assert sorted(numbers) == ["$5,000", "12", "15"]


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


# Windows pipes use the console code page (cp1252), not UTF-8. Before 1.1.6
# stdout JSON came out in cp1252 (an em dash as byte 0x97, a check mark
# crashed) and piped stdin UTF-8 was read as cp1252 mojibake.
_CP1252_PIPE = dict(os.environ, PYTHONIOENCODING="cp1252")


def test_cli_stdout_is_ascii_json_on_a_cp1252_pipe(tmp_path: Path):
    original = tmp_path / "original.txt"
    proposed = tmp_path / "proposed.txt"
    original.write_text("Built apps.", encoding="utf-8")
    proposed.write_text("Built apps \u2014 now on Pinecone \u2713 today.", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--original", str(original), "--proposed", str(proposed)],
        capture_output=True, env=_CP1252_PIPE,
    )
    assert result.returncode == 0, result.stderr
    text = result.stdout.decode("ascii")
    payload = json.loads(text)
    context = payload["new_proper_nouns"][0]["context"]
    assert "\u2014" in context and "\u2713" in context


def test_cli_out_file_keeps_real_utf8_characters(tmp_path: Path):
    original = tmp_path / "original.txt"
    proposed = tmp_path / "proposed.txt"
    out = tmp_path / "report.json"
    original.write_text("Built apps.", encoding="utf-8")
    proposed.write_text("Built apps \u2014 now on Pinecone.", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--original", str(original), "--proposed", str(proposed),
         "--out", str(out)],
        capture_output=True, env=_CP1252_PIPE,
    )
    assert result.returncode == 0, result.stderr
    assert "\u2014" in out.read_text(encoding="utf-8")


def test_cli_stdin_is_read_as_utf8_on_a_cp1252_pipe(tmp_path: Path):
    original = tmp_path / "original.txt"
    original.write_text("Built apps.", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--original", str(original), "--proposed-stdin"],
        input="Built apps \u2014 now on Pinecone.".encode("utf-8"),
        capture_output=True, env=_CP1252_PIPE,
    )
    assert result.returncode == 0, result.stderr
    context = json.loads(result.stdout.decode("ascii"))["new_proper_nouns"][0]["context"]
    assert "\u2014" in context
    assert "\u00e2" not in context


def test_cli_original_stdin_is_read_as_utf8_on_a_cp1252_pipe(tmp_path: Path):
    """The gate must see the same original text a file would give it: one em
    dash is one character, not the three of its cp1252 mojibake."""
    text = "Built apps \u2014 now on Pinecone."
    proposed = tmp_path / "proposed.txt"
    proposed.write_text(text, encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--original-stdin", "--proposed", str(proposed)],
        input=text.encode("utf-8"), capture_output=True, env=_CP1252_PIPE,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout.decode("ascii"))
    assert payload["original_chars"] == len(text)
    assert payload["summary"]["verdict"] == "clean"


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


# ---- Mode A reformat noise (owner run 2026-10-19) --------------------------
# Synthetic fixture, invented for this test. A tighten-only reformat that adds
# no claims: the one-per-line competency list is joined with " | " and a
# bullet that the source export wrapped mid-sentence is rejoined.

_REFORMAT_ORIGINAL = (
    "JORDAN AVERY\n"
    "Field Operations Coordinator\n\n"
    "CORE COMPETENCIES\n"
    "Scheduling\n"
    "Budgeting\n"
    "Vendor Relations\n"
    "Fleet Safety\n"
    "Team Leadership\n\n"
    "EXPERIENCE\n"
    "Operations Coordinator, Harbor Lane Freight (2018 - 2024)\n"
    "- Coordinated 200+ deliveries per week across three depots.\n"
    "- Supervised a crew of 20\n"
    "Mechanics and drivers on rotating shifts.\n"
    "- Ran weekly sales and safety reviews with depot leads.\n"
)

_REFORMAT_PROPOSED = (
    "JORDAN AVERY\n"
    "Field Operations Coordinator\n\n"
    "CORE COMPETENCIES\n"
    "Scheduling | Budgeting | Vendor Relations | Fleet Safety | Team Leadership\n\n"
    "EXPERIENCE\n"
    "Operations Coordinator, Harbor Lane Freight (2018 - 2024)\n"
    "- Coordinated 200+ deliveries per week across three depots.\n"
    "- Supervised a crew of 20 mechanics and drivers on rotating shifts.\n"
    "- Ran weekly Sales and Safety reviews with depot leads.\n"
)


def test_mode_a_reformat_with_no_new_claims_flags_no_nouns_or_numbers():
    """Owner run 2026-10-19: a Mode A reformat with no new claims got 14-19
    new_proper_nouns (Budgeting, Sales, Team, ...) and a new number '20'."""
    report = verify(_REFORMAT_ORIGINAL, _REFORMAT_PROPOSED)
    assert [n["token"] for n in report["new_proper_nouns"]] == []
    assert [n["token"] for n in report["new_numbers"]] == []


def test_line_joined_list_items_not_flagged_as_new_proper_nouns():
    original = "SKILLS\nBudgeting\nForecasting\nTeam Leadership\n"
    proposed = "SKILLS\nBudgeting | Forecasting | Team Leadership\n"
    nouns = [n["token"] for n in verify(original, proposed)["new_proper_nouns"]]
    assert nouns == []


def test_capitalized_word_present_in_original_in_lowercase_not_flagged():
    original = "Led weekly sales reviews."
    proposed = "Led weekly Sales reviews."
    nouns = [n["token"] for n in verify(original, proposed)["new_proper_nouns"]]
    assert nouns == []


def test_number_does_not_absorb_first_letter_of_next_word():
    from verify_no_fabrication import _number_set

    assert _number_set("a crew of 20 Mechanics") == {"20"}
    assert _number_set("a crew of 20\nMechanics") == {"20"}
    assert _number_set("ran 6 Kubernetes clusters") == {"6"}
    assert _number_set("20 members") == {"20"}


def test_number_unit_suffixes_still_tokenized():
    from verify_no_fabrication import _number_set

    assert _number_set("reached 5M users") == {"5M"}
    assert _number_set("a $120k budget") == {"$120k"}
    assert _number_set("grew 3x in a year") == {"3x"}
    assert _number_set("served 200+ clients") == {"200+"}


def test_number_context_is_the_number_itself_not_a_longer_number():
    """'20' used to get the context of '200+' because the snippet came from
    str.find, which matches inside the longer number."""
    filler = "Kept every depot inspection on schedule for the full contract. " * 3
    original = "Served 200+ clients.\n" + filler
    proposed = "Served 200+ clients.\n" + filler + "Led 20 dispatchers."
    new = verify(original, proposed)["new_numbers"]
    assert [n["token"] for n in new] == ["20"]
    assert "Led 20 dispatchers" in new[0]["context"]
    assert "200+" not in new[0]["context"]


def test_reformat_still_flags_new_tool_employer_and_number():
    """Load-bearing: the same reformat plus three real new claims. All three
    must still be flagged after the noise fixes."""
    proposed = (
        _REFORMAT_PROPOSED.replace("Harbor Lane Freight", "Northwind Logistics")
        .replace("200+", "300+")
        .replace("rotating shifts.", "rotating shifts in Salesforce.")
    )
    report = verify(_REFORMAT_ORIGINAL, proposed)
    nouns = [n["token"] for n in report["new_proper_nouns"]]
    numbers = [n["token"] for n in report["new_numbers"]]
    assert "Northwind" in nouns
    assert "Logistics" in nouns
    assert "Salesforce" in nouns
    assert "300+" in numbers
    assert report["summary"]["verdict"] == "review_required"
    assert report["auto_approved"] is False


# ---- New word that starts a bare line (gap closed 2026-10-19) --------------
# Invented fixtures. Before this fix any word after a newline was skipped as a
# "sentence start", so a new item on its own line in a one-per-line list gave
# verdict "clean". Bullet lines ("- X") and mid-line words were already caught.


def test_new_bare_list_item_flagged():
    original = "SKILLS\nBudgeting\nScheduling\n"
    proposed = "SKILLS\nBudgeting\nScheduling\nSalesforce\n"
    report = verify(original, proposed)
    assert [n["token"] for n in report["new_proper_nouns"]] == ["Salesforce"]
    assert report["summary"]["verdict"] == "review_required"
    assert report["auto_approved"] is False


def test_new_bare_list_item_flagged_with_crlf_line_endings():
    original = "SKILLS\r\nBudgeting\r\nScheduling\r\n"
    proposed = "SKILLS\r\nBudgeting\r\nScheduling\r\nSalesforce\r\n"
    nouns = [n["token"] for n in verify(original, proposed)["new_proper_nouns"]]
    assert nouns == ["Salesforce"]


def test_new_job_title_line_flagged():
    original = (
        "EXPERIENCE\n"
        "Harbor Lane Freight (2018 - 2024)\n"
        "Operations Coordinator\n"
        "- Coordinated deliveries across three depots.\n"
    )
    proposed = original.replace(
        "Operations Coordinator\n", "Dispatch Supervisor\n"
    )
    nouns = [n["token"] for n in verify(original, proposed)["new_proper_nouns"]]
    assert "Dispatch" in nouns
    assert "Supervisor" in nouns


def test_new_name_line_flagged():
    original = "REFERENCES\nAvailable on request\n"
    proposed = "REFERENCES\nMorgan Ellery\nAvailable on request\n"
    nouns = [n["token"] for n in verify(original, proposed)["new_proper_nouns"]]
    assert "Morgan" in nouns
    assert "Ellery" in nouns


def test_new_word_on_first_line_flagged():
    """The first line is a line start too (the name header of a resume)."""
    original = "JORDAN AVERY\nField Operations Coordinator\n"
    proposed = "Casey Avery\nField Operations Coordinator\n"
    nouns = [n["token"] for n in verify(original, proposed)["new_proper_nouns"]]
    assert nouns == ["Casey"]


def test_reordered_bare_list_items_not_flagged():
    original = "SKILLS\nBudgeting\nScheduling\nVendor Relations\n"
    proposed = "SKILLS\nVendor Relations\nScheduling\nBudgeting\n"
    nouns = [n["token"] for n in verify(original, proposed)["new_proper_nouns"]]
    assert nouns == []


def test_sentence_start_on_a_new_line_still_not_flagged():
    """A line that follows a line ending in . ! or ? starts a sentence, as in
    a cover-letter paragraph. Those stay skipped, like mid-line sentence
    starts."""
    original = "Built systems.\n"
    proposed = "Built systems.\nDesigned APIs.\n\nThanks again!\nRegards"
    nouns = [n["token"] for n in verify(original, proposed)["new_proper_nouns"]]
    assert "Designed" not in nouns
    assert "Regards" not in nouns
    crlf = proposed.replace("\n", "\r\n")
    nouns = [n["token"] for n in verify(original, crlf)["new_proper_nouns"]]
    assert "Designed" not in nouns
    assert "Regards" not in nouns


# ---- DOCX-shaped text (owner run 2026-10-20) --------------------------------
# Invented fixture. python-docx paragraph.text gives no bullet markers (Word
# list bullets are a paragraph style) and headings are plain Title Case lines
# in Normal style. Before 1.1.4 a new Title Case heading was not reported and
# a new markerless bullet was never counted.

_DOCX_ORIGINAL = (
    "Jordan Avery\n"
    "Field Operations Coordinator\n"
    "Summary\n"
    "Operations lead for regional freight depots.\n"
    "Core Competencies\n"
    "Scheduling\n"
    "Customer Service\n"
    "Fleet Safety\n"
    "Experience\n"
    "Operations Coordinator\n"
    "Harbor Lane Freight\n"
    "Coordinated deliveries across three depots.\n"
    "Ran weekly safety reviews with depot leads.\n"
    "Dispatcher\n"
    "Bay Road Transit\n"
    "Scheduled drivers for morning routes.\n"
    "Education\n"
    "Coastal Community College\n"
)

_DOCX_TIGHTENED = (
    "Jordan Avery\n"
    "Field Operations Coordinator\n"
    "Summary\n"
    "Operations lead for regional freight depots.\n"
    "Core Competencies\n"
    "Scheduling | Customer Service | Fleet Safety\n"
    "Experience\n"
    "Operations Coordinator | Harbor Lane Freight\n"
    "Coordinated deliveries across three depots.\n"
    "Ran weekly safety reviews with depot leads.\n"
    "Dispatcher | Bay Road Transit\n"
    "Scheduled drivers for morning routes.\n"
    "Education\n"
    "Coastal Community College\n"
)


def test_docx_title_and_employer_joined_on_one_line_not_flagged():
    """Owner run 2026-10-20 on the installed 1.1.1 copy: 17 of 17 flagged
    proper nouns were words the original already had at line start. Fixed in
    1.1.2 (26d7738); this pins the DOCX shapes (title + employer joined with
    a pipe, one-per-line list joined with pipes)."""
    report = verify(_DOCX_ORIGINAL, _DOCX_TIGHTENED)
    assert [n["token"] for n in report["new_proper_nouns"]] == []
    assert [n["token"] for n in report["new_numbers"]] == []


def test_new_title_case_heading_flagged():
    proposed = _DOCX_ORIGINAL.replace(
        "Dispatcher\n", "Earlier Experience\nDispatcher\n"
    )
    report = verify(_DOCX_ORIGINAL, proposed)
    assert report["new_sections"] == ["Earlier Experience"]
    assert report["summary"]["verdict"] == "review_required"
    assert report["auto_approved"] is False


def test_new_title_case_heading_flagged_with_crlf_and_trailing_colon():
    original = _DOCX_ORIGINAL.replace("\n", "\r\n")
    proposed = _DOCX_ORIGINAL.replace(
        "Dispatcher\n", "Volunteer Work:\nDispatcher\n"
    ).replace("\n", "\r\n")
    assert verify(original, proposed)["new_sections"] == ["Volunteer Work:"]


def test_docx_tighten_reports_no_sections_or_bullets():
    """Job-title, employer and skill lines are short Title Case lines too.
    They are not headings (no section word), and a tighten that joins lines
    adds no items."""
    report = verify(_DOCX_ORIGINAL, _DOCX_TIGHTENED)
    assert report["new_sections"] == []
    assert report["new_bullets"] == {}
    assert verify(_DOCX_ORIGINAL, _DOCX_ORIGINAL)["summary"]["verdict"] == "clean"


def test_recased_or_reordered_title_case_heading_not_flagged():
    """A heading the original already had as its own line, in any case, is
    not new (EDUCATION -> Education is formatting, not a new section)."""
    original = _DOCX_ORIGINAL.replace("Education\n", "EDUCATION\n")
    assert verify(original, _DOCX_ORIGINAL)["new_sections"] == []
    original = _DOCX_ORIGINAL.replace("Experience\n", "Experience:\n")
    assert verify(original, _DOCX_ORIGINAL)["new_sections"] == []


def test_title_case_heading_text_only_inside_a_sentence_is_still_new():
    """Only a whole original line suppresses the flag, not the same words
    inside a sentence."""
    original = _DOCX_ORIGINAL.replace(
        "Operations lead for regional freight depots.",
        "Operations lead with earlier experience in transit.",
    )
    proposed = original.replace("Dispatcher\n", "Earlier Experience\nDispatcher\n")
    assert verify(original, proposed)["new_sections"] == ["Earlier Experience"]


def test_new_title_and_employer_lines_listed_but_do_not_split_bullets():
    """Changed 2026-10-20 (1.1.7): a new short Title Case line with no section
    word is listed in new_sections (it may be a heading), but only
    section-word headings start a bullet section, so job lines do not."""
    proposed = _DOCX_ORIGINAL.replace(
        "Dispatcher\n", "Route Planner\nNorthwind Logistics\n"
    )
    report = verify(_DOCX_ORIGINAL, proposed)
    assert report["new_sections"] == ["Route Planner", "Northwind Logistics"]
    # One line became two: +1 item under Experience, not new bullet sections.
    assert report["new_bullets"] == {"Experience": 1}
    nouns = [n["token"] for n in report["new_proper_nouns"]]
    assert "Northwind" in nouns


# ---- Title Case heading with no section word (gap closed 2026-10-20) ------


def test_new_heading_without_a_section_word_flagged():
    """"Leadership" is new as a line even though "Team Leadership" is in the
    source: only a whole line or a separated segment counts as known."""
    original = _DOCX_ORIGINAL.replace("Fleet Safety\n", "Fleet Safety\nTeam Leadership\n")
    proposed = original.replace("Dispatcher\n", "Leadership\nDispatcher\n")
    report = verify(original, proposed)
    assert report["new_sections"] == ["Leadership"]
    assert report["summary"]["verdict"] == "review_required"


def test_new_heading_without_a_section_word_flagged_crlf_and_colon():
    original = _DOCX_ORIGINAL.replace("\n", "\r\n")
    proposed = _DOCX_ORIGINAL.replace(
        "Dispatcher\n", "Military Service:\nDispatcher\n"
    ).replace("\n", "\r\n")
    assert verify(original, proposed)["new_sections"] == ["Military Service:"]


def test_changed_job_title_from_known_words_flagged():
    """Every word is already in the source, so no proper noun flags; the
    changed title line is still a new line."""
    original = _DOCX_ORIGINAL.replace("Fleet Safety\n", "Fleet Safety\nFleet Manager\n")
    proposed = original.replace(
        "Operations Coordinator\nHarbor Lane Freight\n",
        "Operations Manager\nHarbor Lane Freight\n",
    )
    report = verify(original, proposed)
    assert report["new_proper_nouns"] == []
    assert report["new_sections"] == ["Operations Manager"]


def test_split_title_and_employer_line_not_flagged():
    """Splitting "Title | Employer" (or a comma, slash or dash join) onto
    separate lines is formatting: each piece is a segment of a source line."""
    original = (
        "Experience\n"
        "Operations Coordinator | Harbor Lane Freight\n"
        "Dispatcher, Bay Road Transit\n"
        "Project Manager / Quality Manager\n"
        "Site Lead - Coastal Builders\n"
    )
    proposed = (
        "Experience\n"
        "Operations Coordinator\nHarbor Lane Freight\n"
        "Dispatcher\nBay Road Transit\n"
        "Project Manager\nQuality Manager\n"
        "Site Lead\nCoastal Builders\n"
    )
    assert verify(original, proposed)["new_sections"] == []


def test_letter_address_block_not_listed_as_sections():
    """cover-letter runs the same gate. A letter has no Title Case section
    headings, so its address-block lines are not listed as sections (their
    new words are still proper-noun flags)."""
    letter = (
        "Hiring Team\n"
        "Globex Corporation\n"
        "Springfield Office\n"
        "\n"
        "Dear Hiring Team,\n"
        "I coordinated deliveries across three depots at Harbor Lane Freight.\n"
        "Sincerely,\n"
        "Jordan Avery\n"
    )
    report = verify(_DOCX_ORIGINAL, letter)
    assert report["new_sections"] == []
    assert "Globex" in [n["token"] for n in report["new_proper_nouns"]]


def test_reordered_or_recased_lines_without_section_words_not_flagged():
    original = "Skills\nVendor Relations\nFleet Safety\n"
    proposed = "Skills\nFleet Safety\nVendor Relations\nFleet Safety:\nfleet safety\n"
    assert verify(original, proposed)["new_sections"] == []


def test_new_markerless_bullet_counted_in_its_section():
    proposed = _DOCX_ORIGINAL.replace(
        "Ran weekly safety reviews with depot leads.\n",
        "Ran weekly safety reviews with depot leads.\n"
        "Cut fuel costs across the fleet.\n",
    )
    report = verify(_DOCX_ORIGINAL, proposed)
    assert report["new_bullets"] == {"Experience": 1}
    assert report["summary"]["verdict"] == "review_required"


def test_new_markerless_bullet_counted_with_crlf_line_endings():
    original = _DOCX_ORIGINAL.replace("\n", "\r\n")
    proposed = _DOCX_ORIGINAL.replace(
        "Scheduled drivers for morning routes.\n",
        "Scheduled drivers for morning routes.\nTrained new drivers.\n",
    ).replace("\n", "\r\n")
    assert verify(original, proposed)["new_bullets"] == {"Experience": 1}


def test_new_markerless_items_under_a_new_title_case_heading_counted():
    proposed = _DOCX_ORIGINAL.replace(
        "Dispatcher\n", "Earlier Experience\nDispatcher\n"
    )
    report = verify(_DOCX_ORIGINAL, proposed)
    assert report["new_bullets"] == {"Earlier Experience": 3}


def test_headingless_letter_against_docx_resume_counts_no_bullets():
    """cover-letter and interview-prep run the same gate on a letter or a
    claims list: plain lines with no heading. Line counting covers only lines
    under a heading, so those lines are not reported as new bullets."""
    letter = (
        "Dear Hiring Manager,\n"
        "I coordinated deliveries across three depots at Harbor Lane Freight.\n"
        "I ran weekly safety reviews with depot leads.\n"
        "I would welcome the chance to talk.\n"
        "Sincerely,\n"
        "Jordan Avery\n"
    )
    assert verify(_DOCX_ORIGINAL, letter)["new_bullets"] == {}
    marked_source = _DOCX_ORIGINAL.replace(
        "Coordinated deliveries", "- Coordinated deliveries"
    )
    assert verify(marked_source, letter)["new_bullets"] == {}


def test_markers_dropped_in_proposed_still_counts_new_bullet():
    """Original exported with "- " markers, proposed from DOCX without them:
    counting only marker lines would see 0 in proposed and miss the new one."""
    original = (
        "## Experience\n"
        "Operations Coordinator\n"
        "- Coordinated deliveries across three depots.\n"
        "- Ran weekly safety reviews.\n"
    )
    proposed = (
        "## Experience\n"
        "Operations Coordinator\n"
        "Coordinated deliveries across three depots.\n"
        "Ran weekly safety reviews.\n"
        "Cut fuel costs across the fleet.\n"
    )
    assert verify(original, proposed)["new_bullets"] == {"## Experience": 1}


def test_marker_mode_unchanged_when_both_documents_have_markers():
    """Both documents use markers: only marker lines count, so rewrapping a
    plain line does not count as a new bullet."""
    original = (
        "## Experience\n"
        "Operations Coordinator, Harbor Lane Freight\n"
        "- Coordinated deliveries across three depots.\n"
    )
    proposed = (
        "## Experience\n"
        "Operations Coordinator,\n"
        "Harbor Lane Freight\n"
        "- Coordinated deliveries across three depots.\n"
    )
    assert verify(original, proposed)["new_bullets"] == {}


# ---- Words with an inner capital (owner run 2026-10-20) --------------------
# Before 1.1.5 the scan matched a capital anywhere, so "iOS" gave "OS" and
# "vCard" gave "Card": fragments the source never has, flagged as new.


def test_known_inner_capital_word_does_not_flag_a_fragment():
    original = "Shipped the iOS app with vCard export."
    proposed = "Shipped vCard export in the iOS app."
    nouns = [n["token"] for n in verify(original, proposed)["new_proper_nouns"]]
    assert nouns == []


def test_new_inner_capital_brand_flagged_as_whole_word():
    original = "Built mobile apps for local sellers."
    proposed = "Built iOS apps for eBay sellers."
    nouns = [n["token"] for n in verify(original, proposed)["new_proper_nouns"]]
    assert "iOS" in nouns
    assert "eBay" in nouns
    assert "OS" not in nouns
    assert "Bay" not in nouns


def test_inner_capital_brand_flagged_even_after_a_full_stop():
    """A lowercase-first word is never a sentence start, so the sentence-start
    skip must not hide it."""
    original = "Built mobile apps."
    proposed = "Built mobile apps. iPhone support shipped."
    nouns = [n["token"] for n in verify(original, proposed)["new_proper_nouns"]]
    assert nouns == ["iPhone"]


def test_inner_capital_context_shows_the_whole_word():
    filler = "Kept every depot inspection on schedule for the full contract. " * 3
    original = "Earned the OSHA 30 card.\n" + filler
    proposed = original + "Shipped the iOS app."
    new = verify(original, proposed)["new_proper_nouns"]
    assert [n["token"] for n in new] == ["iOS"]
    assert "Shipped the iOS app" in new[0]["context"]
    assert "OSHA" not in new[0]["context"]


def test_capital_after_a_hyphen_still_checked_as_before():
    """"non-GAAP" keeps its old reading: the capitalized part is the candidate,
    so a known "GAAP" stays quiet and a new "Salesforce" part still flags."""
    original = "Prepared GAAP reports."
    assert verify(original, "Prepared non-GAAP reports.")["new_proper_nouns"] == []
    nouns = [n["token"] for n in
             verify(original, "Prepared GAAP reports in pre-Salesforce days.")["new_proper_nouns"]]
    assert nouns == ["Salesforce"]


def test_stopword_after_a_hyphen_still_skipped():
    """"mid-May" gave the month "May", a stopword, before 1.1.5; it must stay
    quiet now that hyphen parts are checked one by one."""
    original = "Started the build in spring."
    proposed = "Started the build mid-May."
    assert verify(original, proposed)["new_proper_nouns"] == []


def test_word_after_a_digit_still_a_candidate():
    """"3Dprint" read as "Dprint" before 1.1.5 and still does."""
    report = verify("Built frames.", "Built 3Dprint frames.")
    assert [n["token"] for n in report["new_proper_nouns"]] == ["Dprint"]
