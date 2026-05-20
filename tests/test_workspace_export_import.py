"""
Tests for scripts/export_workspace.py + scripts/import_workspace.py

Covers:
- export bundles profile + 4 learning-loop files + tracker.json
- export refuses to write to cloud-sync paths without --allow-cloud
- export errors clearly when workspace is empty (nothing to export)
- export --include-tailored-files captures Resume_*.docx + CoverLetter_*.docx
- import refuses to overwrite existing files without --overwrite
- import rejects path-traversal payloads in archive (load-bearing safety)
- import roundtrip preserves all 4 .job-hunter/ files byte-for-byte
- import --dry-run lists files without writing
- import handles archive without manifest.json gracefully
- import --show-manifest reads only the metadata

Run from skill root:
    python -m pytest tests/test_workspace_export_import.py -v
"""

import io
import json
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).parent.parent
EXPORT_SCRIPT = SKILL_ROOT / "scripts" / "export_workspace.py"
IMPORT_SCRIPT = SKILL_ROOT / "scripts" / "import_workspace.py"
sys.path.insert(0, str(EXPORT_SCRIPT.parent))

from export_workspace import _is_cloud_sync_path, export_workspace  # noqa: E402
from import_workspace import (  # noqa: E402
    _is_safe_archive_path,
    import_workspace,
    read_manifest,
)
from init_workspace import init_workspace  # noqa: E402


# ---- Helpers ----------------------------------------------------------------


def _seed_workspace(workspace: Path, with_profile: bool = True,
                    with_tracker: bool = True,
                    with_tailored: bool = False) -> None:
    """Set up a workspace with all the file types export_workspace cares about."""
    init_workspace(workspace)
    if with_profile:
        (workspace / ".job-hunter-profile.md").write_text(
            "# profile placeholder\n", encoding="utf-8"
        )
    if with_tracker:
        (workspace / "tracker.json").write_text(
            json.dumps([{"company": "Acme", "title": "PM", "status": "applied"}]),
            encoding="utf-8",
        )
    if with_tailored:
        (workspace / "Resume_Acme_PM.docx").write_bytes(b"fake docx bytes")
        (workspace / "CoverLetter_Acme_PM.docx").write_bytes(b"fake docx bytes")


# ---- Export tests -----------------------------------------------------------


def test_export_bundles_all_known_files(tmp_path: Path):
    workspace = tmp_path / "ws"
    archive = tmp_path / "backup.zip"
    _seed_workspace(workspace)
    result = export_workspace(workspace, archive)
    assert archive.is_file()
    # Profile + 4 .job-hunter/* + tracker.json
    assert result["file_count"] >= 6
    files = set(result["files"])
    assert ".job-hunter-profile.md" in files
    assert "tracker.json" in files
    assert ".job-hunter/DECISIONS.md" in files
    assert ".job-hunter/LESSONS.md" in files
    assert ".job-hunter/OUTCOMES.md" in files
    assert ".job-hunter/REJECTED_IDEAS.md" in files


def test_export_excludes_tailored_files_by_default(tmp_path: Path):
    workspace = tmp_path / "ws"
    _seed_workspace(workspace, with_tailored=True)
    result = export_workspace(workspace, tmp_path / "backup.zip", include_tailored=False)
    assert not any("Resume_" in f for f in result["files"])
    assert not any("CoverLetter_" in f for f in result["files"])


def test_export_with_include_tailored_captures_resumes(tmp_path: Path):
    workspace = tmp_path / "ws"
    _seed_workspace(workspace, with_tailored=True)
    result = export_workspace(workspace, tmp_path / "backup.zip", include_tailored=True)
    assert any("Resume_Acme_PM" in f for f in result["files"])
    assert any("CoverLetter_Acme_PM" in f for f in result["files"])


def test_export_writes_manifest_inside_archive(tmp_path: Path):
    workspace = tmp_path / "ws"
    archive = tmp_path / "backup.zip"
    _seed_workspace(workspace)
    export_workspace(workspace, archive)
    with zipfile.ZipFile(archive) as zf:
        assert "manifest.json" in zf.namelist()
        manifest = json.loads(zf.read("manifest.json"))
    assert "exported_at" in manifest
    assert manifest["source_workspace"] == str(workspace.resolve())
    assert manifest["include_tailored_files"] is False


def test_export_errors_on_empty_workspace(tmp_path: Path):
    """No profile, no .job-hunter/, no tracker → clear error, not empty zip."""
    workspace = tmp_path / "empty-ws"
    workspace.mkdir()
    with pytest.raises(FileNotFoundError) as excinfo:
        export_workspace(workspace, tmp_path / "out.zip")
    assert "nothing to export" in str(excinfo.value).lower()


def test_export_errors_on_missing_workspace(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        export_workspace(tmp_path / "does-not-exist", tmp_path / "out.zip")


# ---- Cloud-sync safety ------------------------------------------------------


@pytest.mark.parametrize("hint", ["Dropbox", "OneDrive", "iCloud Drive", "Google Drive", "Box Sync"])
def test_cloud_path_detection_catches_common_providers(tmp_path: Path, hint: str):
    """The detector should flag paths whose components contain known cloud-sync names."""
    fake_path = tmp_path / hint / "backup.zip"
    fake_path.parent.mkdir(parents=True)
    assert _is_cloud_sync_path(fake_path) is True


def test_export_refuses_cloud_sync_path_by_default(tmp_path: Path):
    workspace = tmp_path / "ws"
    _seed_workspace(workspace)
    cloud_dir = tmp_path / "Dropbox" / "backups"
    cloud_dir.mkdir(parents=True)
    out = cloud_dir / "backup.zip"
    with pytest.raises(PermissionError) as excinfo:
        export_workspace(workspace, out)
    assert "cloud-sync" in str(excinfo.value).lower()


def test_export_allow_cloud_override(tmp_path: Path):
    workspace = tmp_path / "ws"
    _seed_workspace(workspace)
    cloud_dir = tmp_path / "Dropbox" / "backups"
    cloud_dir.mkdir(parents=True)
    out = cloud_dir / "backup.zip"
    # Should NOT raise with allow_cloud=True
    result = export_workspace(workspace, out, allow_cloud=True)
    assert out.is_file()
    assert result["file_count"] >= 6


# ---- Import safety ----------------------------------------------------------


def test_import_rejects_absolute_paths():
    assert _is_safe_archive_path("/etc/passwd") is False
    assert _is_safe_archive_path("\\Windows\\System32\\boot.ini") is False


def test_import_rejects_parent_traversal():
    assert _is_safe_archive_path("../../etc/passwd") is False
    assert _is_safe_archive_path(".job-hunter/../../etc/passwd") is False


def test_import_rejects_unknown_prefixes():
    """Files outside the allowed prefix set are rejected even if path-safe."""
    assert _is_safe_archive_path("some_random_file.txt") is False
    assert _is_safe_archive_path("home/user/.ssh/id_rsa") is False


def test_import_allows_documented_prefixes():
    assert _is_safe_archive_path(".job-hunter-profile.md") is True
    assert _is_safe_archive_path(".job-hunter/DECISIONS.md") is True
    assert _is_safe_archive_path(".job-hunter/LESSONS.md") is True
    assert _is_safe_archive_path("tracker.json") is True
    assert _is_safe_archive_path("tailored/Resume_Acme_PM.docx") is True


def test_import_skips_manifest():
    """manifest.json is metadata, not a restorable file."""
    assert _is_safe_archive_path("manifest.json") is False


def test_import_rejects_traversal_payload_in_archive(tmp_path: Path):
    """Construct a malicious archive with a path-traversal entry. Import must
    skip it AND list it under rejected_unsafe."""
    archive = tmp_path / "evil.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr(".job-hunter-profile.md", "legit")
        zf.writestr("../../../tmp/pwned", "evil")
    workspace = tmp_path / "ws"
    result = import_workspace(archive, workspace)
    assert ".job-hunter-profile.md" in result["restored"]
    assert any("pwned" in r for r in result["rejected_unsafe"])
    # Confirm the malicious file did NOT land
    assert not (tmp_path.parent / "tmp" / "pwned").exists()


# ---- Roundtrip integrity ----------------------------------------------------


def test_roundtrip_preserves_file_contents_byte_for_byte(tmp_path: Path):
    """Export → import to new workspace → all files match the originals exactly."""
    src_ws = tmp_path / "src"
    dst_ws = tmp_path / "dst"
    archive = tmp_path / "backup.zip"
    _seed_workspace(src_ws, with_tailored=True)
    # Add some user content to LESSONS.md to simulate a real lived-in workspace
    lessons_path = src_ws / ".job-hunter" / "LESSONS.md"
    lessons_path.write_text(
        lessons_path.read_text(encoding="utf-8")
        + "\n## 2026-06-15 — User pattern\n\n**Pattern:** something specific\n",
        encoding="utf-8",
    )
    export_workspace(src_ws, archive, include_tailored=True)
    import_workspace(archive, dst_ws)

    # Profile
    assert (dst_ws / ".job-hunter-profile.md").read_bytes() == \
           (src_ws / ".job-hunter-profile.md").read_bytes()
    # All 4 learning-loop files
    for name in ("DECISIONS.md", "LESSONS.md", "OUTCOMES.md", "REJECTED_IDEAS.md"):
        assert (dst_ws / ".job-hunter" / name).read_bytes() == \
               (src_ws / ".job-hunter" / name).read_bytes()
    # tracker.json
    assert (dst_ws / "tracker.json").read_bytes() == \
           (src_ws / "tracker.json").read_bytes()
    # Tailored files (under tailored/ in archive)
    assert (dst_ws / "tailored" / "Resume_Acme_PM.docx").read_bytes() == \
           (src_ws / "Resume_Acme_PM.docx").read_bytes()


def test_import_preserves_existing_without_overwrite(tmp_path: Path):
    src_ws = tmp_path / "src"
    dst_ws = tmp_path / "dst"
    archive = tmp_path / "backup.zip"
    _seed_workspace(src_ws)
    export_workspace(src_ws, archive)

    # Seed dst with existing different profile
    dst_ws.mkdir()
    (dst_ws / ".job-hunter-profile.md").write_text("existing dst content", encoding="utf-8")

    result = import_workspace(archive, dst_ws)
    assert ".job-hunter-profile.md" in result["skipped_existing"]
    # Existing content survives
    assert (dst_ws / ".job-hunter-profile.md").read_text(encoding="utf-8") == "existing dst content"


def test_import_overwrite_replaces_existing(tmp_path: Path):
    src_ws = tmp_path / "src"
    dst_ws = tmp_path / "dst"
    archive = tmp_path / "backup.zip"
    _seed_workspace(src_ws)
    export_workspace(src_ws, archive)

    dst_ws.mkdir()
    (dst_ws / ".job-hunter-profile.md").write_text("existing dst content", encoding="utf-8")

    result = import_workspace(archive, dst_ws, overwrite=True)
    assert ".job-hunter-profile.md" in result["restored"]
    # Restored content
    assert (dst_ws / ".job-hunter-profile.md").read_text(encoding="utf-8") != "existing dst content"


def test_import_dry_run_writes_nothing(tmp_path: Path):
    src_ws = tmp_path / "src"
    dst_ws = tmp_path / "dst"
    archive = tmp_path / "backup.zip"
    _seed_workspace(src_ws)
    export_workspace(src_ws, archive)

    result = import_workspace(archive, dst_ws, dry_run=True)
    assert len(result["restored"]) >= 6
    # dst should still be empty
    assert not (dst_ws / ".job-hunter-profile.md").exists()


# ---- Manifest reading -------------------------------------------------------


def test_read_manifest_returns_dict(tmp_path: Path):
    src_ws = tmp_path / "src"
    archive = tmp_path / "backup.zip"
    _seed_workspace(src_ws)
    export_workspace(src_ws, archive)

    manifest = read_manifest(archive)
    assert "exported_at" in manifest
    assert "source_workspace" in manifest
    assert "files" in manifest


def test_read_manifest_missing_manifest_returns_empty(tmp_path: Path):
    """Archive lacking manifest.json (older/hand-built) returns {} without error."""
    archive = tmp_path / "no-manifest.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr(".job-hunter-profile.md", "x")
    assert read_manifest(archive) == {}


# ---- CLI tests --------------------------------------------------------------


def test_cli_export_then_import_roundtrip(tmp_path: Path):
    src_ws = tmp_path / "src"
    dst_ws = tmp_path / "dst"
    archive = tmp_path / "backup.zip"
    _seed_workspace(src_ws)

    # Export
    r = subprocess.run(
        [sys.executable, str(EXPORT_SCRIPT),
         "--workspace", str(src_ws), "--out", str(archive)],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, f"export stderr: {r.stderr}"
    assert archive.is_file()

    # Import
    r = subprocess.run(
        [sys.executable, str(IMPORT_SCRIPT),
         "--archive", str(archive), "--workspace", str(dst_ws)],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, f"import stderr: {r.stderr}"
    payload = json.loads(r.stdout)
    assert ".job-hunter-profile.md" in payload["restored"]


def test_cli_show_manifest(tmp_path: Path):
    src_ws = tmp_path / "src"
    archive = tmp_path / "backup.zip"
    _seed_workspace(src_ws)
    export_workspace(src_ws, archive)
    r = subprocess.run(
        [sys.executable, str(IMPORT_SCRIPT),
         "--archive", str(archive), "--workspace", str(tmp_path / "unused"),
         "--show-manifest"],
        capture_output=True, text=True,
    )
    assert r.returncode == 0
    manifest = json.loads(r.stdout)
    assert "files" in manifest


# ---- Load-bearing safety: archive integrity --------------------------------


def test_export_privacy_banner_prints_to_stderr(tmp_path: Path):
    """The privacy banner is on every run; it's how the user is reminded
    the archive contains personal data."""
    src_ws = tmp_path / "src"
    _seed_workspace(src_ws)
    r = subprocess.run(
        [sys.executable, str(EXPORT_SCRIPT),
         "--workspace", str(src_ws), "--out", str(tmp_path / "out.zip")],
        capture_output=True, text=True,
    )
    assert r.returncode == 0
    assert "personal" in r.stderr.lower(), (
        "privacy banner must mention 'personal' so the user is reminded "
        "the archive contains private data"
    )
