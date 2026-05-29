"""Family-wiring verification: every member exists with required files, every
sister_skills reference resolves, the whole set is one family, exactly one
orchestrator. The structural integrity check for the job-hunter family."""
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent  # E:/Git/job-hunter-public
MEMBERS = ["job-hunter", "career-profile", "job-search",
           "resume-tailor", "cover-letter", "application-tracker", "outcome-learning"]


def _meta(m):
    return json.loads((REPO / m / "_meta.json").read_text(encoding="utf-8"))


def test_all_members_exist_with_required_files():
    for m in MEMBERS:
        d = REPO / m
        assert (d / "SKILL.md").exists(), f"{m} missing SKILL.md"
        assert (d / "_meta.json").exists(), f"{m} missing _meta.json"
        assert (d / "evals" / "trigger-evals.json").exists(), f"{m} missing trigger-evals"
        assert (d / "evals" / "outcome-evals.json").exists(), f"{m} missing outcome-evals"


def test_sister_skills_resolve():
    known = set(MEMBERS)
    for m in MEMBERS:
        for sister in _meta(m).get("sister_skills", []):
            assert sister in known, f"{m} references unknown sister {sister}"
            assert sister != m, f"{m} lists itself as a sister"


def test_every_member_in_same_family():
    fams = {_meta(m)["family"] for m in MEMBERS}
    assert fams == {"job-hunter"}, f"members not in one family: {fams}"


def test_exactly_one_orchestrator():
    roles = [_meta(m)["family_role"] for m in MEMBERS]
    assert roles.count("orchestrator") == 1, f"expected 1 orchestrator, roles={roles}"


def test_each_member_has_unique_role():
    roles = [_meta(m)["family_role"] for m in MEMBERS]
    assert len(roles) == len(set(roles)), f"duplicate family_role: {roles}"


def test_every_members_evals_are_valid_json_nonempty():
    for m in MEMBERS:
        trig = json.loads((REPO / m / "evals" / "trigger-evals.json").read_text(encoding="utf-8"))
        out = json.loads((REPO / m / "evals" / "outcome-evals.json").read_text(encoding="utf-8"))
        assert len(trig) >= 1, f"{m} has no trigger evals"
        assert out.get("evals"), f"{m} has no outcome evals"
