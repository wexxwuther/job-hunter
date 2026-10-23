"""The gate and starter rules this member ships with."""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT.parent
SCRIPTS = ROOT / "scripts"


def test_fabrication_gate_is_bundled():
    assert (SCRIPTS / "verify_no_fabrication.py").exists(), \
        "job-outreach must bundle verify_no_fabrication.py so standalone installs are safe"


def test_gate_byte_identical_to_resume_tailor():
    canonical = REPO / "resume-tailor" / "scripts" / "verify_no_fabrication.py"
    assert (SCRIPTS / "verify_no_fabrication.py").read_bytes() == canonical.read_bytes(), \
        "bundled gate drifted from resume-tailor's canonical copy; re-copy it"


def test_bundled_gate_flags_an_invented_number(tmp_path):
    source = tmp_path / "source.txt"
    draft = tmp_path / "draft.txt"
    source.write_text("Jordan Reyes. Estimator at Shoreline Homes for two years.", encoding="utf-8")
    draft.write_text("Hi Dana, I have 10 years of estimating experience.", encoding="utf-8")
    r = subprocess.run([sys.executable, str(SCRIPTS / "verify_no_fabrication.py"),
                        "--original", str(source), "--proposed", str(draft)],
                       capture_output=True, text=True)
    assert r.returncode == 0
    assert "10" in r.stdout, f"gate failed to flag the invented number; stdout={r.stdout[:400]}"


def test_starter_rules_load_and_cover_the_channels():
    spec = importlib.util.spec_from_file_location("check_voice", SCRIPTS / "check_voice.py")
    cv = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cv)
    rules = cv.load_rules(ROOT / "references" / "rules-starter.json")
    assert {"email", "linkedin-note", "linkedin-dm"} <= set(rules["channels"])
    assert cv.check("x" * 301, rules, "linkedin-note")[0]["rule"] == "limit-linkedin-note"


def test_starter_rules_are_person_neutral():
    """Nothing personal ships with the skill: no names, places, employers, or allowlisted sentences."""
    data = json.loads((ROOT / "references" / "rules-starter.json").read_text(encoding="utf-8"))
    assert data["allow"] == []
    text = json.dumps(data)
    for personal in ("Greg", "Borden", "JB West", "Benton Harbor", "MWB", "Stewart", "Tavira", "Pitch Please",
                     "project manager", "15-minute", "salary"):
        assert personal.lower() not in text.lower(), f"starter rules mention {personal!r}"
    assert all(r.get("source") == "starter" for r in data["rules"])
