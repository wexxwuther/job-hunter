"""The family installer must install all 6 members to all harness roots,
cross-OS (no hardcoded drive letters in the posix installer; PowerShell derives
from $HOME)."""
from pathlib import Path

INSTALL = Path(__file__).resolve().parent
MEMBERS = ["job-hunter", "career-profile", "job-search",
           "resume-tailor", "application-tracker", "outcome-learning"]


def test_sh_installs_all_members_to_all_harnesses():
    sh = (INSTALL / "install.sh").read_text(encoding="utf-8")
    for m in MEMBERS:
        assert m in sh, f"install.sh missing member {m}"
    for h in [".claude/skills", ".agents/skills", ".hermes/skills"]:
        assert h in sh, f"install.sh missing harness path {h}"
    # No Windows drive letters in the posix installer.
    assert "C:\\" not in sh and "E:\\" not in sh


def test_ps1_installs_all_members_to_all_harnesses():
    ps1 = (INSTALL / "install.ps1").read_text(encoding="utf-8")
    for m in MEMBERS:
        assert m in ps1, f"install.ps1 missing member {m}"
    for h in [".claude", ".agents", ".hermes"]:
        assert h in ps1, f"install.ps1 missing harness {h}"
    # Derives from home, not a hardcoded drive.
    assert "$HOME" in ps1


def test_sh_has_valid_shebang_lf():
    raw = (INSTALL / "install.sh").read_bytes()
    assert raw.startswith(b"#!"), "install.sh needs a shebang"
    assert b"\r\n" not in raw, "install.sh must be LF (CRLF breaks the shebang on macOS/Linux)"
