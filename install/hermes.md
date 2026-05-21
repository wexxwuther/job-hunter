# Install: Hermes Agent

Hermes Agent loads agentskills.io-compliant skills from `~/.hermes/skills/` ([docs](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills)).

## Option 1, Clone

```bash
mkdir -p ~/.hermes/skills
git clone https://github.com/wexxwuther/job-hunter.git ~/.hermes/skills/job-hunter
```

## Option 2, Download the zip

1. Go to the [latest Release](https://github.com/wexxwuther/job-hunter/releases/latest).
2. Download `job-hunter-vX.Y.Z.zip`.
3. Extract it into `~/.hermes/skills/` so the final path is `~/.hermes/skills/job-hunter/SKILL.md`.

## Option 3, One-shot installer

The cross-platform installers at [install/install.sh](install.sh) and [install/install.ps1](install.ps1) install to all four supported harness paths by default, including Hermes Agent.

## Verify

Restart your Hermes session and ask it to find jobs matching your background. If the skill auto-activates and walks you through the profile questions, you're set.

## Uninstall

```bash
rm -rf ~/.hermes/skills/job-hunter
```
