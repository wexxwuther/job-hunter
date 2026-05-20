# Install: OpenAI Codex

Codex loads agentskills.io-compliant skills from `~/.codex/skills/`.

## Option 1 — Clone

```bash
mkdir -p ~/.codex/skills
git clone https://github.com/wexxwuther/job-hunter.git ~/.codex/skills/job-hunter
```

## Option 2 — Download the zip

1. Go to the [latest Release](https://github.com/wexxwuther/job-hunter/releases/latest).
2. Download `job-hunter-vX.Y.Z.zip`.
3. Extract it into `~/.codex/skills/` so the final path is `~/.codex/skills/job-hunter/SKILL.md`.

## Option 3 — One-shot installer

The cross-platform installer scripts at [install/install.sh](install.sh) and [install/install.ps1](install.ps1) install to **all four** supported harness paths (`~/.claude/skills/`, `~/.codex/skills/`, `~/.openclaw/skills/`, `~/.hermes/skills/`) by default, so they cover Codex automatically.

## Verify

Restart your Codex session and ask:

```
What nurse practitioner jobs near Austin would I be a strong fit for?
```

You should be prompted for the 5 North-Star profile questions on first use.

## Notes on Codex compatibility

- The skill uses no Codex-specific APIs — anything labeled "agentskills.io 2025-12-18" should run identically here.
- If your Codex install has a different skills directory, replace `~/.codex/skills/` with that path.
- Reach out via Issues if you hit a Codex-specific bug.

## Uninstall

```bash
rm -rf ~/.codex/skills/job-hunter
```
