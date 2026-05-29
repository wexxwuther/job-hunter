import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
def test_member_declares_family():
    m = json.loads((ROOT / "_meta.json").read_text(encoding="utf-8"))
    assert m["family"] == "job-hunter"
    assert m["family_role"] == "resume-tailor"
    assert "job-hunter" in m["sister_skills"]
def test_skill_md_has_name_and_description():
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert "name: resume-tailor" in text
    assert "description:" in text
def test_load_bearing_safety_tests_present_after_move():
    t = (ROOT / "tests" / "test_verify_no_fabrication.py").read_text(encoding="utf-8")
    for name in ["test_auto_approved_field_is_always_false_on_clean_input",
                 "test_auto_approved_field_is_always_false_on_dirty_input",
                 "test_script_exports_only_detection_no_approval_helpers",
                 "test_real_world_pattern_detects_multiple_categories",
                 "test_years_NOT_flagged_as_new_numbers"]:
        assert name in t, f"load-bearing safety test {name} lost in the split"
def test_skill_md_preserves_hard_gate_and_modes():
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8").lower()
    assert "hard gate" in text or "truth-preservation" in text
    assert "mode a" in text and "mode b" in text
    assert "verify_no_fabrication" in text
    assert "untrusted" in text  # web-content rule preserved
