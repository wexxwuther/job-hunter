import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import build_prep_pack as bpp  # noqa: E402


def test_member_declares_family():
    m = json.loads((ROOT / "_meta.json").read_text(encoding="utf-8"))
    assert m["family"] == "job-hunter"
    assert m["family_role"] == "interview-prep"
    assert "job-hunter" in m["sister_skills"]


def test_skill_md_has_name_and_description():
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert "name: interview-prep" in text
    assert "description:" in text


def test_description_fits_the_spec_limit_and_names_the_collision_guards():
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    block = re.search(r"description: >\n(.*?)\nlicense:", text, re.S).group(1)
    desc = " ".join(line.strip() for line in block.splitlines())
    assert len(desc) <= 1024
    for guard in ("hiring side", "application-tracker", "resume-tailor", "cover-letter",
                  "salary negotiation"):
        assert guard in desc, f"description lost its do-not-use clause for {guard}"


def test_ships_the_workspace_contract():
    assert (ROOT / "references" / "workspace-contract.md").exists()


def test_every_stage_is_documented_in_the_stage_reference():
    ref = (ROOT / "references" / "interview-stages.md").read_text(encoding="utf-8")
    for stage in bpp.STAGES:
        assert f"### {stage}" in ref, f"references/interview-stages.md has no section for {stage}"


def test_skill_md_lists_every_stage():
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    for stage in bpp.STAGES:
        assert f"`{stage}`" in text


def test_load_bearing_tests_exist():
    m = json.loads((ROOT / "_meta.json").read_text(encoding="utf-8"))
    names = set()
    for path in (ROOT / "tests").glob("test_*.py"):
        names |= set(re.findall(r"^def (test_\w+)", path.read_text(encoding="utf-8"), re.M))
    missing = [t for t in m["load_bearing_safety_tests"] if t not in names]
    assert not missing, f"_meta.json lists load-bearing tests that do not exist: {missing}"
