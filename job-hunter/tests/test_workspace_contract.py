"""Contract test: the workspace-contract reference documents every shared
artifact + names every producer member. Guards the family hand-off spec."""
from pathlib import Path

CONTRACT = Path(__file__).resolve().parent.parent / "references" / "workspace-contract.md"


def test_contract_documents_every_shared_artifact():
    text = CONTRACT.read_text(encoding="utf-8")
    for artifact in ["profile.md", "postings.json", "tracker.json", ".job-hunter/"]:
        assert artifact in text, f"workspace-contract.md must document {artifact}"


def test_contract_names_every_producer_member():
    text = CONTRACT.read_text(encoding="utf-8")
    for member in ["career-profile", "job-search", "resume-tailor",
                   "cover-letter", "application-tracker", "outcome-learning"]:
        assert member in text, f"contract must name producer {member}"


def test_contract_states_antifabrication_invariant():
    text = CONTRACT.read_text(encoding="utf-8").lower()
    assert "verify_no_fabrication" in text
    assert "invariant" in text
