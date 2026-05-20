# Install: OpenClaw

OpenClaw loads agentskills.io-compliant skills from `~/.openclaw/skills/` ([docs](https://docs.openclaw.ai/tools/skills)).

## Option 1 — Clone

```bash
mkdir -p ~/.openclaw/skills
git clone https://github.com/wexxwuther/job-hunter.git ~/.openclaw/skills/job-hunter
```

## Option 2 — Download the zip

1. Go to the [latest Release](https://github.com/wexxwuther/job-hunter/releases/latest).
2. Download `job-hunter-vX.Y.Z.zip`.
3. Extract it into `~/.openclaw/skills/` so the final path is `~/.openclaw/skills/job-hunter/SKILL.md`.

## Option 3 — One-shot installer

The cross-platform installers at [install/install.sh](install.sh) and [install/install.ps1](install.ps1) install to all four supported harness paths by default, including OpenClaw.

## Verify

Restart your OpenClaw session and ask it to find jobs matching your background. If the skill auto-activates and walks you through the profile questions, you're set.

## Project-scoped install

OpenClaw also supports project-scoped skills at `<workspace>/.openclaw/skills/`. Use that path instead of `~/.openclaw/skills/` if you want this skill scoped to a single workspace.

## Uninstall

```bash
rm -rf ~/.openclaw/skills/job-hunter
```
