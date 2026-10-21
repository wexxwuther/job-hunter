"""Exercise the actual generated archives outside the source tree."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile

import pytest

from tools.build_runtime_packages import DESCRIPTION, MEMBERS, REPO, build, package_entries, split_skill


@pytest.mark.parametrize("target", ["chatgpt", "openclaw"])
def test_archive_inventory_hashes_and_resource_links(tmp_path, target):
    archive = build(REPO, tmp_path, target)
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        assert z.testzip() is None
        assert len(names) == len(set(names))
        skills = [n for n in names if n.endswith("/SKILL.md")]
        assert len(skills) == (1 if target == "chatgpt" else 8)
        assert not any(part in {"__pycache__", ".pytest_cache", "tests", "docs", "evals"}
                       for n in names for part in Path(n).parts)
        assert not any(n.endswith((".pyc", ".pyo")) or ".." in Path(n).parts for n in names)
        assert len(names) <= 500
        manifest = json.loads(z.read("job-hunter/bundle.json" if target == "chatgpt" else "bundle.json"))
        assert set(manifest["files"]) == set(names) - {"job-hunter/bundle.json" if target == "chatgpt" else "bundle.json"}
        assert set(manifest["members"]) == set(MEMBERS)
        for name, digest in manifest["files"].items():
            assert hashlib.sha256(z.read(name)).hexdigest() == digest
        for name in skills:
            header, body = split_skill(z.read(name).decode("utf-8"))
            assert "allowed-tools:" not in header and "context:" not in header
            assert "dispatch_mode_note:" not in header
            assert "references/runtime-guide.md" in body
            if name == "job-hunter/SKILL.md":
                description = next(line for line in header.splitlines() if line.startswith("description:"))
                # JSON string scalars are valid YAML, including colon-space and quotes.
                assert json.loads(description.split(":", 1)[1]) == DESCRIPTION
        workflows = skills + [n for n in names if n.endswith("/WORKFLOW.md")]
        for name in workflows:
            for link in re.findall(r"\]\(([^)]+)\)", z.read(name).decode("utf-8")):
                if link.startswith(("references/", "assets/", "members/")):
                    assert (Path(name).parent / link).as_posix() in names, (name, link)
        for member in ("resume-tailor", "cover-letter", "interview-prep"):
            base = member if target == "openclaw" else f"job-hunter/members/{member}"
            gate = f"{base}/scripts/verify_no_fabrication.py"
            assert z.read(gate) == (REPO / member / "scripts/verify_no_fabrication.py").read_bytes()


@pytest.mark.parametrize("target", ["chatgpt", "openclaw"])
def test_extracted_package_executes_without_source_tree(tmp_path, target):
    archive = build(REPO, tmp_path / "out", target)
    installed = tmp_path / "installed"
    with zipfile.ZipFile(archive) as z:
        z.extractall(installed)
    workspace = tmp_path / "user files"
    workspace.mkdir()
    def script(member, filename):
        base = installed / member if target == "openclaw" or member == "job-hunter" else installed / "job-hunter/members" / member
        return base / "scripts" / filename
    def run(member, filename, *args):
        result = subprocess.run([sys.executable, str(script(member, filename)), *map(str, args)],
                                cwd=workspace, capture_output=True, text=True, encoding="utf-8")
        assert result.returncode == 0, result.stderr
        return result
    run("job-hunter", "init_workspace.py", "init", "--workspace", workspace)
    run("career-profile", "init_profile.py", "init", "--workspace", workspace)
    assert (workspace / ".job-hunter/LESSONS.md").is_file()
    assert (workspace / ".job-hunter-profile.md").is_file()
    original = workspace / "source.txt"
    proposed = workspace / "draft.txt"
    original.write_text("# Experience\n- Supported customers at Acme.\n", encoding="utf-8")
    proposed.write_text("# Experience\n- Supported customers at Acme.\n- Won 12 awards at Globex.\n", encoding="utf-8")
    report = json.loads(run("resume-tailor", "verify_no_fabrication.py", "--original", original, "--proposed", proposed).stdout)
    assert report["auto_approved"] is False
    assert "Globex" in json.dumps(report)
    backup = workspace / "backup.zip"
    run("job-hunter", "export_workspace.py", "--workspace", workspace, "--out", backup)
    restored = tmp_path / "restored"
    run("job-hunter", "import_workspace.py", "--archive", backup, "--workspace", restored)
    assert (restored / ".job-hunter/LESSONS.md").read_bytes() == (workspace / ".job-hunter/LESSONS.md").read_bytes()
    assert not any(installed.rglob(".job-hunter-profile.md"))


def test_reproducible_build_and_no_overwrite(tmp_path):
    first = build(REPO, tmp_path / "one", "chatgpt")
    second = build(REPO, tmp_path / "two", "chatgpt")
    assert first.read_bytes() == second.read_bytes()
    with pytest.raises(FileExistsError):
        build(REPO, tmp_path / "one", "chatgpt")


def test_unknown_target_rejected():
    with pytest.raises(ValueError):
        package_entries(REPO, "unknown")
