#!/usr/bin/env python3
"""Build local ChatGPT (one skill) and OpenClaw (nine skills) compatibility ZIPs.

No install, network, dependency changes, or user workspace data. Existing output
archives are refused. Sources remain canonical; generated adapters omit Claude
frontmatter and include explicit host capability/persistence guidance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zipfile

REPO = Path(__file__).resolve().parents[1]
MEMBERS = ("job-hunter", "career-profile", "job-search", "resume-tailor",
           "cover-letter", "application-tracker", "interview-prep", "outcome-learning",
           "job-outreach")
RESOURCE_DIRS = ("scripts", "references", "assets")
DESCRIPTION = (
    "Manage a job hunt: build a career profile, find and score postings, tailor a "
    "resume, draft cover letters, track applications, prepare for interviews, write "
    "recruiter outreach in your own voice, and learn from outcomes. Use for one or several of these tasks, or to back up or "
    "restore a job-hunter workspace. Uses bundled workflows and mandatory "
    "anti-fabrication checks for career documents."
)


def split_skill(text: str) -> tuple[str, str]:
    """Split the source's YAML header, refusing missing/unterminated headers."""
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise ValueError("SKILL.md is missing frontmatter")
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            return "".join(lines[1:i]), "".join(lines[i + 1:]).lstrip()
    raise ValueError("SKILL.md frontmatter is unterminated")


def adapt_skill(text: str, *, orchestrator: bool) -> str:
    header, body = split_skill(text)
    # All existing Claude-only fields are single-line top-level scalars except
    # dispatch_mode_note, whose complete single-line value is nested in metadata.
    header = "".join(line for line in header.splitlines(keepends=True)
                     if not line.startswith(("allowed-tools:", "context:"))
                     and not line.lstrip().startswith("dispatch_mode_note:"))
    header = "\n".join(
        ("compatibility: ChatGPT or OpenClaw with file access and Python execution; see bundled runtime-guide.md for capability limits."
         if line.startswith("compatibility:") else line)
        for line in header.splitlines()
    ) + "\n"
    if orchestrator:
        lines = header.splitlines()
        lines = [f"description: {json.dumps(DESCRIPTION)}" if line.startswith("description:")
                 else line for line in lines]
        header = "\n".join(lines) + "\n"
    preamble = (
        "Read [runtime capabilities](references/runtime-guide.md) before this "
        "workflow. Resolve resource paths relative to this skill/workflow, and "
        "use a separate writable user workspace.\n\n"
    )
    return f"---\n{header}---\n\n{preamble}{body}"


def resources(repo: Path, member: str) -> dict[str, bytes]:
    result = {}
    base = repo / member
    for directory in RESOURCE_DIRS:
        for file in sorted((base / directory).rglob("*")):
            relative = file.relative_to(base)
            if (file.is_file() and not file.is_symlink()
                    and not any(p.startswith(".") or p == "__pycache__" for p in relative.parts)
                    and file.suffix not in (".pyc", ".pyo")):
                result[relative.as_posix()] = file.read_bytes()
    return result


def package_entries(repo: Path, target: str) -> dict[str, bytes]:
    if target not in ("chatgpt", "openclaw"):
        raise ValueError(f"Unsupported target: {target}")
    guide = (repo / "install/runtime-guide.md").read_bytes()
    entries: dict[str, bytes] = {}
    for member in MEMBERS:
        is_root = member == "job-hunter"
        base = member if target == "openclaw" or is_root else f"job-hunter/members/{member}"
        source = (repo / member / "SKILL.md").read_text(encoding="utf-8")
        if target == "chatgpt" and not is_root:
            _, workflow = split_skill(source)
            entries[f"{base}/WORKFLOW.md"] = workflow.encode("utf-8")
        else:
            skill = adapt_skill(source, orchestrator=is_root)
            if target == "chatgpt":
                table = "\n## Bundled member workflows\n\n" + "\n".join(
                    f"- [{m}](members/{m}/WORKFLOW.md)" for m in MEMBERS if m != "job-hunter"
                ) + "\n\nRead the needed workflow here instead of requiring separately installed skills.\n"
                skill += table
            entries[f"{base}/SKILL.md"] = skill.encode("utf-8")
        entries.update({f"{base}/{name}": data for name, data in resources(repo, member).items()})
        entries[f"{base}/references/runtime-guide.md"] = guide
        entries[f"{base}/LICENSE"] = (repo / "LICENSE").read_bytes()
    version = json.loads((repo / "job-hunter/_meta.json").read_text(encoding="utf-8"))["version"]
    manifest = {
        "target": target, "family_version": version, "members": list(MEMBERS),
        "status": "local compatibility build; live host acceptance pending",
        "files": {name: hashlib.sha256(data).hexdigest() for name, data in sorted(entries.items())},
    }
    manifest_path = "job-hunter/bundle.json" if target == "chatgpt" else "bundle.json"
    entries[manifest_path] = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
    if target == "chatgpt" and (len(entries) > 500 or sum(n.endswith("/SKILL.md") for n in entries) != 1):
        raise ValueError("ChatGPT bundle must have one SKILL.md and at most 500 files")
    if any(len(data) > 25 * 1024 * 1024 for data in entries.values()):
        raise ValueError("Bundle contains a file larger than 25 MiB")
    return entries


def build(repo: Path, output: Path, target: str) -> Path:
    entries = package_entries(repo, target)
    version = json.loads((repo / "job-hunter/_meta.json").read_text(encoding="utf-8"))["version"]
    output.mkdir(parents=True, exist_ok=True)
    path = output / f"job-hunter-v{version}-{target}.zip"
    with zipfile.ZipFile(path, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(entries.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 21, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=REPO / "dist/compatibility")
    parser.add_argument("--target", choices=("chatgpt", "openclaw", "all"), default="all")
    args = parser.parse_args()
    targets = ("chatgpt", "openclaw") if args.target == "all" else (args.target,)
    for target in targets:
        print(build(REPO, args.out.resolve(), target))


if __name__ == "__main__":
    main()
