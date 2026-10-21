# Install: OpenClaw

job-hunter is a family of 8 agentskills.io skills (the `job-hunter` orchestrator plus 7
members); install all 8. The installer puts them in `~/.agents/skills/`, which OpenClaw
shares with Codex ([OpenClaw skills docs](https://docs.openclaw.ai/tools/skills)).

## Option 1, one-shot installer (recommended)

```bash
# macOS / Linux
curl -fsSL https://raw.githubusercontent.com/wexxwuther/job-hunter/main/install/install.sh | bash
```

```powershell
# Windows
iwr https://raw.githubusercontent.com/wexxwuther/job-hunter/main/install/install.ps1 -UseBasicParsing | iex
```

## Option 2, offline

Download `job-hunter-FAMILY-installer-only-v6.0.0.zip` from the
[latest release](https://github.com/wexxwuther/job-hunter/releases/latest), unzip it, and run
`bash job-hunter/install/install.sh` (Windows: `install\install.ps1` in the same folder).

## Project-scoped install

OpenClaw also reads project-scoped skills from `<workspace>/.openclaw/skills/`. To scope the
family to one workspace, copy the 8 skill folders there instead.

## Verify

Start a new OpenClaw session and ask it to find jobs matching your background. If the skills
load and you are asked the profile questions, you're set.

## Uninstall

```bash
for s in job-hunter career-profile job-search resume-tailor cover-letter application-tracker interview-prep outcome-learning; do rm -rf ~/.agents/skills/$s; done
```

This also removes them from Codex, which shares `~/.agents/skills/`.
