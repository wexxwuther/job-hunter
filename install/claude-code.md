# Install: Claude Code

`job-hunter` is an agentskills.io-compliant skill. Claude Code auto-loads any skill placed in `~/.claude/skills/`.

## Option 1, Clone

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/wexxwuther/job-hunter.git ~/.claude/skills/job-hunter
```

## Option 2, Download the zip

1. Go to the [latest Release](https://github.com/wexxwuther/job-hunter/releases/latest).
2. Download `job-hunter-vX.Y.Z.zip`.
3. Extract it into `~/.claude/skills/` so the final path is `~/.claude/skills/job-hunter/SKILL.md`.

## Option 3, One-shot installer

```bash
# macOS / Linux
curl -fsSL https://raw.githubusercontent.com/wexxwuther/job-hunter/main/install/install.sh | bash
```

```powershell
# Windows
iwr https://raw.githubusercontent.com/wexxwuther/job-hunter/main/install/install.ps1 -UseBasicParsing | iex
```

## Verify

Restart Claude Code, then ask:

```
Find me senior software engineering jobs in Boston, remote-friendly, $200k+
```

The skill should auto-activate. You'll know it worked when Claude starts walking you through the North-Star profile questions on first use.

## Uninstall

```bash
rm -rf ~/.claude/skills/job-hunter
```

Your `.job-hunter-profile.md` lives in your **workspace**, not in the skill folder, so uninstalling the skill does not delete your profile. To remove that too, delete `.job-hunter-profile.md` from each workspace where you used the skill.
