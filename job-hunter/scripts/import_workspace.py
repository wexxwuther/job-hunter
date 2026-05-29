#!/usr/bin/env python3
"""
import_workspace.py

Restore a workspace from an archive produced by `export_workspace.py`.
Extracts files to their original locations within a target workspace,
preserving the dot-prefix convention for .job-hunter-profile.md and the
.job-hunter/ directory structure.

DEFAULT POLICY: refuses to overwrite existing files. The user must pass
`--overwrite` to replace existing profile or learning-loop content. This
protects against accidental clobber of a workspace that already has its
own job-hunter state.

The script reads the manifest.json inside the archive to validate the
archive came from export_workspace.py and to list what it will restore.

Usage:
    python import_workspace.py --archive backup.zip --workspace /new/workspace
    python import_workspace.py --archive backup.zip --workspace /new/workspace --overwrite
    python import_workspace.py --archive backup.zip --workspace /new/workspace --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path

MANIFEST_FILENAME = "manifest.json"
# Files outside this set are NOT restored, even if the archive contains them.
# This is a safety boundary against an attacker handing the user a malicious
# zip with path-traversal payloads (e.g., "../../../../etc/passwd").
_ALLOWED_PREFIXES = (".job-hunter-profile.md", ".job-hunter/", "tracker.json", "tailored/")


def _is_safe_archive_path(name: str) -> bool:
    """True if the archive member is one we'll restore. Rejects absolute paths,
    parent-traversal segments, and anything outside our allowed prefixes."""
    if name.startswith("/") or name.startswith("\\"):
        return False
    if ".." in Path(name).parts:
        return False
    if name == MANIFEST_FILENAME:
        return False  # manifest is metadata, not a restorable file
    return any(name == p.rstrip("/") or name.startswith(p) for p in _ALLOWED_PREFIXES)


def read_manifest(archive_path: Path) -> dict:
    """Read manifest.json from an export archive. Returns {} if missing
    (we treat missing manifest as a warning, not an error — older archives
    or hand-crafted zips may not have one)."""
    if not archive_path.is_file():
        raise FileNotFoundError(f"archive not found: {archive_path}")
    with zipfile.ZipFile(archive_path, "r") as zf:
        if MANIFEST_FILENAME not in zf.namelist():
            return {}
        try:
            return json.loads(zf.read(MANIFEST_FILENAME).decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {}


def import_workspace(archive_path: Path, workspace: Path,
                     overwrite: bool = False,
                     dry_run: bool = False) -> dict:
    """Restore archive contents into workspace. Returns a status dict listing
    what was restored, what was skipped, and what was rejected for safety."""
    if not archive_path.is_file():
        raise FileNotFoundError(f"archive not found: {archive_path}")

    workspace.mkdir(parents=True, exist_ok=True)

    restored: list[str] = []
    skipped_existing: list[str] = []
    rejected_unsafe: list[str] = []

    with zipfile.ZipFile(archive_path, "r") as zf:
        for member in zf.namelist():
            if member == MANIFEST_FILENAME:
                continue
            if not _is_safe_archive_path(member):
                rejected_unsafe.append(member)
                continue
            # Skip directory entries (some zip writers include them)
            if member.endswith("/"):
                continue

            dst = workspace / member
            if dst.exists() and not overwrite:
                skipped_existing.append(member)
                continue

            if dry_run:
                restored.append(member)
                continue

            dst.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(member) as src_f:
                dst.write_bytes(src_f.read())
            restored.append(member)

    return {
        "archive": str(archive_path),
        "workspace": str(workspace),
        "dry_run": dry_run,
        "overwrite": overwrite,
        "restored": restored,
        "skipped_existing": skipped_existing,
        "rejected_unsafe": rejected_unsafe,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=Path,
                        help="path to the .zip archive produced by export_workspace.py")
    parser.add_argument("--workspace", required=True, type=Path,
                        help="destination workspace folder")
    parser.add_argument("--overwrite", action="store_true",
                        help="replace existing profile / learning-loop files if present "
                             "(default: preserve existing files)")
    parser.add_argument("--dry-run", action="store_true",
                        help="show what would be restored without writing anything")
    parser.add_argument("--show-manifest", action="store_true",
                        help="just print the archive's manifest.json and exit")
    args = parser.parse_args(argv)

    if args.show_manifest:
        try:
            manifest = read_manifest(args.archive)
        except FileNotFoundError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        print(json.dumps(manifest, indent=2))
        return 0

    try:
        result = import_workspace(
            archive_path=args.archive,
            workspace=args.workspace,
            overwrite=args.overwrite,
            dry_run=args.dry_run,
        )
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    except OSError as e:
        print(f"error: cannot restore archive: {e}", file=sys.stderr)
        return 2

    msg_prefix = "DRY RUN: would restore" if args.dry_run else "restored"
    print(f"{msg_prefix} {len(result['restored'])} file(s) to {args.workspace}", file=sys.stderr)
    if result["skipped_existing"]:
        print(f"skipped {len(result['skipped_existing'])} existing file(s) "
              f"(pass --overwrite to replace)", file=sys.stderr)
    if result["rejected_unsafe"]:
        print(f"REJECTED {len(result['rejected_unsafe'])} unsafe archive entries: "
              f"{result['rejected_unsafe']}", file=sys.stderr)

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
