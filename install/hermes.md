# Install: Hermes Agent

Hermes Agent loads agentskills.io skills from `~/.hermes/skills/`
([docs](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills)). job-hunter is
a family of 8 skills (the `job-hunter` orchestrator plus 7 members); install all 8.

## Option 1, one-shot installer (recommended)

Copies all 8 skills to `~/.hermes/skills/<skill>/` (and to the Claude Code and Codex/OpenClaw
directories too):

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

## Verify

Start a new Hermes session and ask it to find jobs matching your background. If the skills
load and you are asked the profile questions, you're set.

## Uninstall

```bash
for s in job-hunter career-profile job-search resume-tailor cover-letter application-tracker interview-prep outcome-learning; do rm -rf ~/.hermes/skills/$s; done
```
