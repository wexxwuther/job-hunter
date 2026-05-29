#!/usr/bin/env python3
"""
export_workspace.py

Bundle the user's job-hunter workspace state into a single .zip archive for
backup or migration. Includes:

  - .job-hunter-profile.md     (5 North-Star answers)
  - .job-hunter/               (the 4 learning-loop files in their entirety)
  - tracker.json               (if present)
  - Optionally: Resume_*.docx / CoverLetter_*.docx tailored outputs

Output is a single .zip the user can move to another machine, back up,
or store offline. Pair with `import_workspace.py` to restore.

PRIVACY WARNING: this archive contains your resume context, decisions,
lessons, and outcomes. Treat it as personal data. Do NOT upload to a
public location. The script prints a privacy banner on every run and
will refuse to write to common cloud-sync directories by default
(override with --allow-cloud).

Usage:
    python export_workspace.py --workspace /path/to/workspace --out backup.zip
    python export_workspace.py --workspace /path/to/workspace --out backup.zip \\
        --include-tailored-files
"""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from datetime import datetime
from pathlib import Path

# Cloud-sync directories that we refuse to write into without --allow-cloud,
# because doing so silently uploads the archive to a third party.
_CLOUD_SYNC_DIR_HINTS = (
    "dropbox",
    "onedrive",
    "icloud",
    "google drive",
    "googledrive",
    "box sync",
    "syncthing",
)

# Filename patterns for tailored outputs that --include-tailored-files captures
_TAILORED_PATTERNS = ("Resume_*.docx", "Resume_*.pdf", "CoverLetter_*.docx", "CoverLetter_*.pdf")


def _is_cloud_sync_path(p: Path) -> bool:
    """Heuristic: does any path component contain a known cloud-sync directory name?"""
    parts_lower = [part.lower() for part in p.resolve().parts]
    return any(any(hint in part for hint in _CLOUD_SYNC_DIR_HINTS) for part in parts_lower)


def _files_to_export(workspace: Path, include_tailored: bool) -> list[tuple[Path, str]]:
    """Return [(absolute_path, archive_relative_path), ...] tuples to include.
    Skips files that don't exist (e.g., no tracker.json yet, no profile yet)."""
    pairs: list[tuple[Path, str]] = []

    # Profile (single dot-prefixed file)
    profile = workspace / ".job-hunter-profile.md"
    if profile.is_file():
        pairs.append((profile, ".job-hunter-profile.md"))

    # .job-hunter/ directory (all 4 templates + any user edits)
    learning_dir = workspace / ".job-hunter"
    if learning_dir.is_dir():
        for child in sorted(learning_dir.iterdir()):
            if child.is_file():
                pairs.append((child, f".job-hunter/{child.name}"))

    # tracker.json
    tracker = workspace / "tracker.json"
    if tracker.is_file():
        pairs.append((tracker, "tracker.json"))

    # Tailored outputs (optional)
    if include_tailored:
        for pattern in _TAILORED_PATTERNS:
            for match in sorted(workspace.glob(pattern)):
                pairs.append((match, f"tailored/{match.name}"))

    return pairs


def export_workspace(workspace: Path, out_path: Path,
                     include_tailored: bool = False,
                     allow_cloud: bool = False) -> dict:
    """Write a zip archive of the workspace's job-hunter state to out_path.
    Returns a status dict describing what was included."""
    if not workspace.is_dir():
        raise FileNotFoundError(f"workspace does not exist: {workspace}")

    if not allow_cloud and _is_cloud_sync_path(out_path):
        raise PermissionError(
            f"refusing to write export to a cloud-sync path: {out_path}. "
            f"This archive contains personal job-search data. "
            f"Pass --allow-cloud to override if you intentionally want to "
            f"sync this to a cloud provider."
        )

    pairs = _files_to_export(workspace, include_tailored)
    if not pairs:
        raise FileNotFoundError(
            f"nothing to export from {workspace}: no profile, no .job-hunter/, "
            f"no tracker.json. Has the workspace been initialized?"
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Manifest goes inside the zip so future-you can verify integrity
    manifest = {
        "exported_at": datetime.now().isoformat(timespec="seconds"),
        "source_workspace": str(workspace.resolve()),
        "include_tailored_files": include_tailored,
        "files": [arc_name for _, arc_name in pairs],
    }

    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest, indent=2))
        for src, arc_name in pairs:
            zf.write(src, arc_name)

    return {
        "out": str(out_path),
        "file_count": len(pairs),
        "files": [arc_name for _, arc_name in pairs],
        "size_bytes": out_path.stat().st_size,
    }


_PRIVACY_BANNER = (
    "⚠  This archive contains personal job-search data: profile answers, "
    "decisions, lessons, outcomes, and (optionally) tailored resumes. "
    "Treat it like a backup of your private notes."
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, type=Path,
                        help="user's workspace folder (where .job-hunter/ lives)")
    parser.add_argument("--out", required=True, type=Path,
                        help="path to write the .zip archive to")
    parser.add_argument("--include-tailored-files", action="store_true",
                        help="also include Resume_*.docx / CoverLetter_*.docx files")
    parser.add_argument("--allow-cloud", action="store_true",
                        help="permit writing to a cloud-sync path (Dropbox/OneDrive/etc.); "
                             "refused by default to protect against accidental upload")
    args = parser.parse_args(argv)

    # Always print the privacy banner so the user is reminded
    print(_PRIVACY_BANNER, file=sys.stderr)

    try:
        result = export_workspace(
            workspace=args.workspace,
            out_path=args.out,
            include_tailored=args.include_tailored_files,
            allow_cloud=args.allow_cloud,
        )
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    except PermissionError as e:
        print(f"error: {e}", file=sys.stderr)
        return 3
    except OSError as e:
        print(f"error: cannot write archive: {e}", file=sys.stderr)
        return 2

    print(f"wrote {result['file_count']} file(s) to {result['out']} "
          f"({result['size_bytes']} bytes)", file=sys.stderr)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
