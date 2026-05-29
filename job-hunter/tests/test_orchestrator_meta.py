"""Orchestrator family-metadata + routing-surface contract tests."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
META = ROOT / "_meta.json"
SKILL = ROOT / "SKILL.md"

MEMBERS = ["career-profile", "job-search", "resume-tailor",
           "cover-letter", "application-tracker", "outcome-learning"]


def test_orchestrator_declares_family():
    m = json.loads(META.read_text(encoding="utf-8"))
    assert m["family"] == "job-hunter"
    assert m["family_role"] == "orchestrator"
    assert set(m["sister_skills"]) == set(MEMBERS)


def test_orchestrator_skill_routes_to_all_members():
    text = SKILL.read_text(encoding="utf-8")
    for member in MEMBERS:
        assert member in text, f"orchestrator SKILL.md must reference {member}"


def test_orchestrator_states_antifabrication_invariant():
    text = SKILL.read_text(encoding="utf-8").lower()
    assert "verify_no_fabrication" in text
    assert "invariant" in text and "hard gate" in text


def test_orchestrator_version_is_major_six():
    m = json.loads(META.read_text(encoding="utf-8"))
    assert m["version"].startswith("6."), "family orchestrator is v6.x (breaking structural change)"
