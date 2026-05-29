"""
Tests for scripts/init_profile.py

Covers:
- Template rendering produces all 5 question headings
- Round-trip: init then read returns the canonical structure
- Refuses to overwrite existing profile without --force
- Idempotent read of an unfilled template returns null answers (no placeholder leakage)
- exists subcommand exit codes
- Filled-in answers parse correctly back to the dict

Run from skill root:
    python -m pytest tests/test_init_profile.py -v
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "scripts" / "init_profile.py"
sys.path.insert(0, str(SCRIPT.parent))

from init_profile import (  # noqa: E402
    PROFILE_FILENAME,
    QUESTIONS,
    init_profile,
    parse_profile,
    read_profile,
    render_template,
)


# ---- Template tests --------------------------------------------------------


def test_template_contains_all_five_headings():
    text = render_template()
    for _, heading, _ in QUESTIONS:
        assert f"## {heading}" in text, f"missing heading: {heading}"


def test_template_contains_privacy_notice():
    text = render_template()
    assert "NOT committed" in text
    assert "dot-prefix" in text.lower() or "dot-prefix" in text


def test_template_contains_optional_notes_section():
    text = render_template()
    assert "## Notes" in text


def test_questions_count_is_five():
    """Load-bearing: profile-questions.md says 'Five questions'. If a question is added
    or removed, this test must be updated AND profile-questions.md must be updated, in
    the same commit, otherwise the docs lie."""
    assert len(QUESTIONS) == 5


# ---- init subcommand tests -------------------------------------------------


def test_init_writes_file(tmp_path):
    path = init_profile(tmp_path)
    assert path.exists()
    assert path.name == PROFILE_FILENAME


def test_init_refuses_overwrite(tmp_path):
    init_profile(tmp_path)
    with pytest.raises(FileExistsError):
        init_profile(tmp_path)


def test_init_force_overwrites(tmp_path):
    path = init_profile(tmp_path)
    # Modify the file
    path.write_text("modified content", encoding="utf-8")
    init_profile(tmp_path, force=True)
    # Modified content should be gone
    assert "modified content" not in path.read_text(encoding="utf-8")
    assert "## Target archetype" in path.read_text(encoding="utf-8")


def test_init_creates_workspace_dir(tmp_path):
    nested = tmp_path / "new" / "workspace"
    init_profile(nested)
    assert (nested / PROFILE_FILENAME).exists()


# ---- parse tests -----------------------------------------------------------


def test_parse_empty_template_returns_nulls():
    """Right after init, before the user has filled anything in, all answers should be
    None (NOT the placeholder text). This prevents the agent from feeding placeholder
    text into scoring."""
    text = render_template()
    parsed = parse_profile(text)
    assert parsed["archetype"] is None
    assert parsed["deal_breakers"] is None
    assert parsed["company_size"] is None
    assert parsed["mission_vs_comp"] is None
    assert parsed["tolerance"] is None


def test_parse_filled_answers():
    """User-filled answers should round-trip through parse correctly."""
    text = render_template()
    text = text.replace(
        "**Answer:** [your answer here, or \"unknown\" if you'd rather not say]",
        "**Answer:** Tech lead, occasional IC work",
        1,
    )
    parsed = parse_profile(text)
    assert parsed["archetype"] == "Tech lead, occasional IC work"
    # Other answers still None
    assert parsed["deal_breakers"] is None


def test_parse_handles_multiline_answer():
    text = """# North-Star Profile

**Last updated:** 2026-05-19

## Target archetype

> What kind of role?

**Answer:** I want technical leadership roles where I still write code
some of the time, not pure people management.

## Deal-breakers

> What won't work?

**Answer:** [your answer here]
"""
    parsed = parse_profile(text)
    assert "technical leadership" in parsed["archetype"]
    assert "still write code" in parsed["archetype"]
    assert parsed["deal_breakers"] is None


def test_parse_extracts_last_updated_date():
    text = render_template(created="2026-05-19")
    parsed = parse_profile(text)
    assert parsed["_last_updated"] == "2026-05-19"


def test_parse_notes_section():
    text = render_template()
    text = text.replace(
        "[Anything else the agent should know that isn't covered above. Industries you care about,\n"
        "specific companies on a target list, geographic constraints beyond city, etc.]",
        "Target list: Stripe, Vercel, Replicate. Avoid: anything ad-tech.",
    )
    parsed = parse_profile(text)
    assert "Target list" in parsed["notes"]
    assert "Avoid" in parsed["notes"]


def test_parse_blank_notes_returns_none():
    text = render_template()
    parsed = parse_profile(text)
    assert parsed["notes"] is None


# ---- read + roundtrip tests ------------------------------------------------


def test_read_missing_profile_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_profile(tmp_path)


def test_init_then_read_roundtrip(tmp_path):
    init_profile(tmp_path)
    data = read_profile(tmp_path)
    assert set(data.keys()) >= {q[0] for q in QUESTIONS}
    # Every question returns None until the user fills it in
    for key, _, _ in QUESTIONS:
        assert data[key] is None


# ---- CLI tests -------------------------------------------------------------


def test_cli_init(tmp_path):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "init", "--workspace", str(tmp_path)],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0, result.stderr
    parsed = json.loads(result.stdout)
    assert parsed["path"].endswith(PROFILE_FILENAME)
    assert len(parsed["questions"]) == 5


def test_cli_init_refuses_existing(tmp_path):
    subprocess.run(
        [sys.executable, str(SCRIPT), "init", "--workspace", str(tmp_path)],
        capture_output=True, text=True, timeout=10, check=True,
    )
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "init", "--workspace", str(tmp_path)],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 2
    assert "already exists" in result.stderr


def test_cli_read(tmp_path):
    subprocess.run(
        [sys.executable, str(SCRIPT), "init", "--workspace", str(tmp_path)],
        capture_output=True, text=True, timeout=10, check=True,
    )
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "read", "--workspace", str(tmp_path)],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0, result.stderr
    parsed = json.loads(result.stdout)
    assert "archetype" in parsed


def test_cli_exists_yes(tmp_path):
    subprocess.run(
        [sys.executable, str(SCRIPT), "init", "--workspace", str(tmp_path)],
        capture_output=True, text=True, timeout=10, check=True,
    )
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "exists", "--workspace", str(tmp_path)],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0


def test_cli_exists_no(tmp_path):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "exists", "--workspace", str(tmp_path)],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 1


# ---- Privacy / drift tests -------------------------------------------------


def test_profile_filename_is_dot_prefixed():
    """Load-bearing: the dot-prefix is part of the privacy story. If a refactor changes
    this to 'job-hunter-profile.md' without the leading dot, users will start accidentally
    committing the file via 'git add .' patterns."""
    assert PROFILE_FILENAME.startswith(".")


def test_no_sample_profile_in_skill_directory():
    """Load-bearing safety test: the skill MUST NOT ship with an example profile in its
    own directory. That would be a PII vector (the example would either be empty/useless
    or contain real preferences the author bled in). If anyone adds a sample, this test
    fails immediately."""
    skill_root = Path(__file__).parent.parent
    for p in skill_root.rglob(PROFILE_FILENAME):
        # Allow the file inside test tmp directories; reject anywhere else.
        if "tests" in p.parts or ".pytest_cache" in p.parts:
            continue
        pytest.fail(
            f"a {PROFILE_FILENAME} was found inside the skill directory at {p}. "
            f"The profile is supposed to live in the USER'S workspace, not in the skill. "
            f"Delete it before committing."
        )
