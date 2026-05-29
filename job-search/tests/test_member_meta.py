import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
def test_member_declares_family():
    m = json.loads((ROOT / "_meta.json").read_text(encoding="utf-8"))
    assert m["family"] == "job-hunter"
    assert m["family_role"] == "search"
    assert "job-hunter" in m["sister_skills"]
def test_skill_md_has_name_and_description():
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert "name: job-search" in text
    assert "description:" in text
