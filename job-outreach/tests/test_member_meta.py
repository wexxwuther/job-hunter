import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_member_declares_family():
    m = json.loads((ROOT / "_meta.json").read_text(encoding="utf-8"))
    assert m["family"] == "job-hunter"
    assert m["family_role"] == "outreach"
    assert "job-hunter" in m["sister_skills"]


def test_skill_md_has_name_and_description():
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert "name: job-outreach" in text
    assert "description:" in text


def test_description_fits_the_spec_limit_and_names_the_collision_guards():
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    block = re.search(r"description: >\n(.*?)\nlicense:", text, re.S).group(1)
    desc = " ".join(line.strip() for line in block.splitlines())
    assert len(desc) <= 1024
    for guard in ("cover-letter", "resume-tailor", "application-tracker", "interview-prep", "the user sends"):
        assert guard in desc, f"description lost its do-not-use clause for {guard}"


def test_ships_the_workspace_contract():
    assert (ROOT / "references" / "workspace-contract.md").exists()


def test_skill_md_names_its_scripts():
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    for script in ("check_voice.py", "verify_no_fabrication.py", "rules-starter.json"):
        assert script in text


def test_load_bearing_tests_exist():
    m = json.loads((ROOT / "_meta.json").read_text(encoding="utf-8"))
    names = set()
    for path in (ROOT / "tests").glob("test_*.py"):
        names |= set(re.findall(r"^def (test_\w+)", path.read_text(encoding="utf-8"), re.M))
    missing = [t for t in m["load_bearing_safety_tests"] if t not in names]
    assert not missing, f"_meta.json lists load-bearing tests that do not exist: {missing}"
