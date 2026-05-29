#!/usr/bin/env python3
"""Generate the Claude Code plugin tree from the canonical family members.

The 6 member skill dirs (job-hunter/, career-profile/, ...) are the SINGLE SOURCE
OF TRUTH. This script assembles them into the plugin layout Claude Code expects:

    plugin/                              <- marketplace root
      .claude-plugin/marketplace.json    <- committed (one entry -> ./job-hunter)
      job-hunter/                        <- the plugin
        .claude-plugin/plugin.json       <- committed (manifest, 6 skills bundled)
        skills/<member>/...              <- GENERATED copies (gitignored)

Run:  python build_plugin.py
Then verify:  claude plugin validate plugin
Install test: claude plugin marketplace add ./plugin ; claude plugin install job-hunter@gdk-skills

The generated skills/ tree is gitignored so it never drifts from the member dirs;
regenerate it any time with this script.
"""
from __future__ import annotations
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
MEMBERS = ["job-hunter", "career-profile", "job-search", "resume-tailor",
           "application-tracker", "outcome-learning"]
PLUGIN_INNER = REPO / "plugin" / "job-hunter"
SKILLS = PLUGIN_INNER / "skills"
STRIP_DIRS = ["tests", "docs/superpowers"]


def build() -> int:
    if not (PLUGIN_INNER / ".claude-plugin" / "plugin.json").exists():
        print("error: plugin/job-hunter/.claude-plugin/plugin.json missing (committed manifest)",
              file=sys.stderr)
        return 1
    if SKILLS.exists():
        shutil.rmtree(SKILLS)
    SKILLS.mkdir(parents=True)
    for m in MEMBERS:
        src = REPO / m
        if not (src / "SKILL.md").exists():
            print(f"error: member {m} has no SKILL.md at {src}", file=sys.stderr)
            return 1
        dst = SKILLS / m
        shutil.copytree(src, dst)
        for d in STRIP_DIRS:
            p = dst / d
            if p.exists():
                shutil.rmtree(p)
        for pyc in dst.rglob("__pycache__"):
            shutil.rmtree(pyc, ignore_errors=True)
    count = len(list(SKILLS.glob("*/SKILL.md")))
    print(f"built plugin/job-hunter/skills with {count} skills: "
          + ", ".join(sorted(p.parent.name for p in SKILLS.glob('*/SKILL.md'))))
    if count != len(MEMBERS):
        print(f"error: expected {len(MEMBERS)} skills, got {count}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(build())
