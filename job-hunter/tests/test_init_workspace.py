"""
Tests for scripts/init_workspace.py

Covers:
- init creates .job-hunter/ with all 4 template files
- init is idempotent: existing files are preserved by default
- --force overwrites existing files
- Templates contain the expected headings and privacy notices
- exists subcommand returns 0 only when all 4 files present
- status subcommand emits structured JSON with per-file presence
- Load-bearing safety: no .job-hunter/ exists inside the skill directory itself

Run from skill root:
    python -m pytest tests/test_init_workspace.py -v
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).parent.parent
SCRIPT = SKILL_ROOT / "scripts" / "init_workspace.py"
sys.path.insert(0, str(SCRIPT.parent))

from init_workspace import (  # noqa: E402
    DIRNAME,
    TEMPLATE_FILES,
    init_workspace,
    workspace_status,
)


# ---- Direct API tests --------------------------------------------------------


def test_init_creates_directory_and_all_four_files(tmp_path: Path):
    result = init_workspace(tmp_path)
    target = tmp_path / DIRNAME
    assert target.is_dir(), f".job-hunter/ not created at {target}"
    for filename in TEMPLATE_FILES:
        assert (target / filename).is_file(), f"missing template: {filename}"
    assert set(result["created"]) == set(TEMPLATE_FILES)
    assert result["preserved"] == []


def test_init_is_idempotent_preserves_existing(tmp_path: Path):
    init_workspace(tmp_path)
    # Mutate one file to simulate user content
    user_content = "## 2026-06-01 — applied to Acme\n**Reason:** good cv_match\n"
    (tmp_path / DIRNAME / "DECISIONS.md").write_text(user_content, encoding="utf-8")
    # Re-init without --force
    result = init_workspace(tmp_path)
    assert "DECISIONS.md" in result["preserved"], "DECISIONS.md should be preserved"
    # User content survives
    assert (tmp_path / DIRNAME / "DECISIONS.md").read_text(encoding="utf-8") == user_content


def test_init_force_overwrites_existing(tmp_path: Path):
    init_workspace(tmp_path)
    user_content = "user content I don't want to lose"
    (tmp_path / DIRNAME / "LESSONS.md").write_text(user_content, encoding="utf-8")
    # Re-init WITH --force
    result = init_workspace(tmp_path, force=True)
    assert "LESSONS.md" in result["created"]
    assert (tmp_path / DIRNAME / "LESSONS.md").read_text(encoding="utf-8") != user_content


def test_init_raises_if_template_source_missing(tmp_path: Path, monkeypatch):
    """If the skill assets/templates dir is broken, init should error clearly,
    not silently produce empty files."""
    import init_workspace as mod
    monkeypatch.setattr(mod, "_templates_dir", lambda: tmp_path / "nonexistent")
    with pytest.raises(FileNotFoundError) as excinfo:
        init_workspace(tmp_path / "ws")
    assert "template missing" in str(excinfo.value).lower()


# ---- Template content tests ------------------------------------------------


@pytest.mark.parametrize("filename", TEMPLATE_FILES)
def test_template_contains_privacy_notice(tmp_path: Path, filename: str):
    """Every template must include the 'never sent off-machine' privacy line so
    a user opening any file alone understands the trust model."""
    init_workspace(tmp_path)
    text = (tmp_path / DIRNAME / filename).read_text(encoding="utf-8")
    assert "never sent off-machine" in text, \
        f"{filename} missing privacy notice"
    assert "never committed to the public skill repository" in text, \
        f"{filename} missing repo-commitment privacy notice"


def test_decisions_template_documents_format():
    src = SKILL_ROOT / "assets" / "templates" / "DECISIONS.template.md"
    text = src.read_text(encoding="utf-8")
    assert "**Context:**" in text
    assert "**Chosen:**" in text
    assert "**Reason:**" in text


def test_lessons_template_documents_cold_start_guard():
    src = SKILL_ROOT / "assets" / "templates" / "LESSONS.template.md"
    text = src.read_text(encoding="utf-8")
    assert "5 closed-loop outcomes" in text, \
        "LESSONS template must document the 5-outcome cold-start guard"


def test_outcomes_template_documents_outcome_enum():
    """The outcomes template must list the recognized outcome values so the
    agent and user agree on the enum."""
    src = SKILL_ROOT / "assets" / "templates" / "OUTCOMES.template.md"
    text = src.read_text(encoding="utf-8")
    for outcome in ("accepted_offer", "rejected_after_screen", "no_response_after_21d"):
        assert outcome in text, f"OUTCOMES template missing outcome value: {outcome}"


def test_rejected_ideas_template_says_agent_does_not_auto_add():
    """REJECTED_IDEAS is the user's veto list, not the agent's pattern guesses.
    The template must make this explicit."""
    src = SKILL_ROOT / "assets" / "templates" / "REJECTED_IDEAS.template.md"
    text = src.read_text(encoding="utf-8")
    assert "should NOT add entries here on its own" in text


# ---- Status / exists tests -------------------------------------------------


def test_status_reports_missing_directory(tmp_path: Path):
    status = workspace_status(tmp_path)
    assert status["directory_exists"] is False
    assert status["complete"] is False
    assert all(v is False for v in status["files"].values())


def test_status_reports_complete_after_init(tmp_path: Path):
    init_workspace(tmp_path)
    status = workspace_status(tmp_path)
    assert status["directory_exists"] is True
    assert status["complete"] is True
    assert all(v is True for v in status["files"].values())


def test_status_reports_partial(tmp_path: Path):
    init_workspace(tmp_path)
    (tmp_path / DIRNAME / "LESSONS.md").unlink()
    status = workspace_status(tmp_path)
    assert status["directory_exists"] is True
    assert status["complete"] is False
    assert status["files"]["LESSONS.md"] is False
    assert status["files"]["DECISIONS.md"] is True


# ---- CLI tests --------------------------------------------------------------


def test_cli_init_creates_files(tmp_path: Path):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "init", "--workspace", str(tmp_path)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    payload = json.loads(result.stdout)
    # init emits {workspace, directory, created, preserved} — verify all 4 templates landed
    assert set(payload["created"]) == set(TEMPLATE_FILES), \
        f"expected all 4 templates created, got: {payload['created']}"
    assert payload["preserved"] == []
    for filename in TEMPLATE_FILES:
        assert (tmp_path / DIRNAME / filename).is_file()


def test_cli_exists_exit_codes(tmp_path: Path):
    # Before init: exit 1
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "exists", "--workspace", str(tmp_path)],
        capture_output=True, text=True,
    )
    assert result.returncode == 1
    # After init: exit 0
    subprocess.run(
        [sys.executable, str(SCRIPT), "init", "--workspace", str(tmp_path)],
        capture_output=True, text=True,
    )
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "exists", "--workspace", str(tmp_path)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0


def test_cli_status_emits_json(tmp_path: Path):
    init_workspace(tmp_path)
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "status", "--workspace", str(tmp_path)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["complete"] is True
    assert set(payload["files"].keys()) == set(TEMPLATE_FILES)


# ---- Load-bearing safety tests ---------------------------------------------


def test_no_job_hunter_directory_in_skill_dir():
    """Load-bearing safety test (PII vector prevention): a .job-hunter/
    directory must never appear inside the skill installation itself.
    The directory belongs in the user's workspace, never in the skill.

    If this test fails, the most likely cause is that someone copied a
    populated .job-hunter/ into the repo for testing and forgot to remove
    it. Delete it; the workspace is the only correct location.
    """
    assert not (SKILL_ROOT / DIRNAME).exists(), (
        f".job-hunter/ found inside skill directory at {SKILL_ROOT / DIRNAME}; "
        f"the learning-loop files belong in user workspaces, never in the skill."
    )


def test_no_sample_lessons_in_skill_directory():
    """Load-bearing safety test: the LESSONS template must not contain any
    sample lessons (entries below the appended-below-this-line marker).
    Sample lessons would be applied as if they were user-confirmed patterns
    and pollute scoring."""
    src = SKILL_ROOT / "assets" / "templates" / "LESSONS.template.md"
    text = src.read_text(encoding="utf-8")
    # Find the marker; everything after it should be empty (just whitespace)
    marker = "<!-- Confirmed lessons appended below this line -->"
    assert marker in text, f"LESSONS template missing the append marker"
    after_marker = text.split(marker, 1)[1].strip()
    assert after_marker == "", (
        f"LESSONS template contains content after the marker — this would be "
        f"applied as a user-confirmed lesson without confirmation:\n{after_marker[:200]}"
    )


def test_template_filenames_match_workspace_filenames():
    """Sanity check: the template files in assets/templates/ must align with
    the TEMPLATE_FILES list in init_workspace.py."""
    templates_dir = SKILL_ROOT / "assets" / "templates"
    for filename in TEMPLATE_FILES:
        base = filename.rsplit(".", 1)[0]
        template_path = templates_dir / f"{base}.template.md"
        assert template_path.is_file(), (
            f"missing template asset: {template_path} "
            f"(workspace filename: {filename})"
        )
