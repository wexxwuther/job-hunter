#!/usr/bin/env python3
"""
init_workspace.py

Initialize the per-user learning-loop directory in a workspace. Creates
`.job-hunter/` (if not present) and drops the four template files:
  - DECISIONS.md       (log of meaningful per-session choices)
  - LESSONS.md         (user-confirmed patterns about preferences)
  - OUTCOMES.md        (what actually happened post-application)
  - REJECTED_IDEAS.md  (hard constraints — "do not do X again")

Idempotent: if a file already exists, it is preserved (the user's content
takes precedence). Pass --force to overwrite all four templates.

Three subcommands:
  init    - create .job-hunter/ and drop missing templates
  exists  - exit 0 if .job-hunter/ exists with ALL 4 files, exit 1 otherwise
  status  - emit a JSON status report of which files are present

Templates are read from a fixed `assets/templates/` directory relative to
the script (the skill installation). They are NEVER bundled into the user's
workspace pre-filled — only the template scaffold goes in. This mirrors
init_profile.py's privacy discipline (load-bearing safety test:
test_no_sample_lessons_in_skill_directory).

Usage:
    python init_workspace.py init --workspace /path/to/workspace
    python init_workspace.py exists --workspace /path/to/workspace
    python init_workspace.py status --workspace /path/to/workspace
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DIRNAME = ".job-hunter"
TEMPLATE_FILES = ("DECISIONS.md", "LESSONS.md", "OUTCOMES.md", "REJECTED_IDEAS.md")


def _templates_dir() -> Path:
    """Resolve assets/templates/ relative to this script's location.
    The skill installs as a directory containing scripts/ and assets/, so
    parent-of-parent gets us to the skill root."""
    return Path(__file__).resolve().parent.parent / "assets" / "templates"


def _workspace_dir(workspace: Path) -> Path:
    return workspace / DIRNAME


def _template_path(filename: str) -> Path:
    """Return path to the template file in the skill's assets directory.
    The template file is named <BASENAME>.template.md (e.g., DECISIONS.template.md);
    we strip the .template suffix when copying into the user's workspace."""
    base = filename.rsplit(".", 1)[0]
    return _templates_dir() / f"{base}.template.md"


def _all_files_present(target_dir: Path) -> bool:
    return target_dir.is_dir() and all((target_dir / f).is_file() for f in TEMPLATE_FILES)


def init_workspace(workspace: Path, force: bool = False) -> dict:
    """Create .job-hunter/ in the given workspace and drop missing template
    files. Returns a status dict with which files were created / preserved.

    - If a file already exists and force=False, it is preserved.
    - If a file already exists and force=True, it is overwritten.
    - If a template source file is missing from the skill assets, raise FileNotFoundError.
    """
    workspace.mkdir(parents=True, exist_ok=True)
    target = _workspace_dir(workspace)
    target.mkdir(parents=True, exist_ok=True)

    created = []
    preserved = []

    for filename in TEMPLATE_FILES:
        src = _template_path(filename)
        if not src.is_file():
            raise FileNotFoundError(
                f"template missing in skill assets: {src} "
                f"(expected at {_templates_dir()})"
            )
        dst = target / filename
        if dst.exists() and not force:
            preserved.append(filename)
            continue
        dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        created.append(filename)

    return {
        "workspace": str(workspace),
        "directory": str(target),
        "created": created,
        "preserved": preserved,
    }


def workspace_status(workspace: Path) -> dict:
    """Report which learning-loop files are present in the workspace's .job-hunter/."""
    target = _workspace_dir(workspace)
    if not target.is_dir():
        return {
            "workspace": str(workspace),
            "directory": str(target),
            "directory_exists": False,
            "files": {f: False for f in TEMPLATE_FILES},
            "complete": False,
        }
    files = {f: (target / f).is_file() for f in TEMPLATE_FILES}
    return {
        "workspace": str(workspace),
        "directory": str(target),
        "directory_exists": True,
        "files": files,
        "complete": all(files.values()),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="create .job-hunter/ and drop missing templates")
    p_init.add_argument("--workspace", required=True, type=Path,
                        help="user's workspace folder (where .job-hunter/ will live)")
    p_init.add_argument("--force", action="store_true",
                        help="overwrite existing learning-loop files if present")

    p_exists = sub.add_parser("exists", help="exit 0 if all 4 files exist, exit 1 otherwise")
    p_exists.add_argument("--workspace", required=True, type=Path)

    p_status = sub.add_parser("status", help="JSON report of which files are present")
    p_status.add_argument("--workspace", required=True, type=Path)

    args = parser.parse_args(argv)

    if args.cmd == "init":
        try:
            result = init_workspace(args.workspace, force=args.force)
        except FileNotFoundError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        except OSError as e:
            print(f"error: cannot write learning-loop files: {e}", file=sys.stderr)
            return 2
        print(f"initialized .job-hunter/ at {result['directory']}", file=sys.stderr)
        if result["created"]:
            print(f"created: {', '.join(result['created'])}", file=sys.stderr)
        if result["preserved"]:
            print(f"preserved existing: {', '.join(result['preserved'])}", file=sys.stderr)
        print(json.dumps(result, indent=2))
        return 0

    if args.cmd == "exists":
        return 0 if _all_files_present(_workspace_dir(args.workspace)) else 1

    if args.cmd == "status":
        print(json.dumps(workspace_status(args.workspace), indent=2))
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
