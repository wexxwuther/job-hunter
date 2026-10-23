# Install: Claude Code

job-hunter is a family of 9 agentskills.io skills: the `job-hunter` orchestrator plus
`career-profile`, `job-search`, `resume-tailor`, `cover-letter`, `application-tracker`,
`interview-prep`, `outcome-learning`, and `job-outreach`. Install all 9.

## Option 1, the plugin (recommended)

Inside Claude Code:

```
/plugin marketplace add wexxwuther/job-hunter
/plugin install job-hunter@gdk-skills
```

That installs all 9 skills as `/job-hunter:job-hunter`, `/job-hunter:career-profile`, and so
on. Update later with `/plugin marketplace update gdk-skills`.

## Option 2, one-shot installer

Copies all 9 skills to `~/.claude/skills/<skill>/` (and to the Codex/OpenClaw and Hermes
directories too):

```bash
# macOS / Linux
curl -fsSL https://raw.githubusercontent.com/wexxwuther/job-hunter/main/install/install.sh | bash
```

```powershell
# Windows
iwr https://raw.githubusercontent.com/wexxwuther/job-hunter/main/install/install.ps1 -UseBasicParsing | iex
```

Offline: download `job-hunter-FAMILY-installer-only-v6.1.0.zip` from the
[latest release](https://github.com/wexxwuther/job-hunter/releases/latest), unzip it, and run
`bash job-hunter/install/install.sh` (Windows: `install\install.ps1` in the same folder).

The v6.1.0 release assets (this offline zip, Option 3, and the Claude.ai uploads below) predate
`job-outreach` and contain the other 8 skills. Use Option 1 or the online installer to get all 9.

## Option 3, one session without installing

Download `job-hunter-PLUGIN-v6.1.0.zip` from the latest release, then:

```bash
claude --plugin-dir job-hunter-PLUGIN-v6.1.0.zip
```

## Claude.ai or Claude Desktop

Their skill uploader takes one skill per zip. From the latest release, upload the 8
`-claude-code.zip` files one at a time (the orchestrator is
`job-hunter-orchestrator-v6.1.0-claude-code.zip`).

## Verify

Start a new session and ask:

```
Find me senior software engineering jobs in Boston, remote-friendly, $200k+
```

The skills should load on their own. On first use you are walked through the North-Star
profile questions.

## Uninstall

Plugin: `/plugin uninstall job-hunter@gdk-skills`.

Installer copies:

```bash
for s in job-hunter career-profile job-search resume-tailor cover-letter application-tracker interview-prep outcome-learning job-outreach; do rm -rf ~/.claude/skills/$s; done
```

Your `.job-hunter-profile.md` and `.job-hunter/` folder live in your **workspace**, not in
the skill folders, so uninstalling does not delete them. Delete them from each workspace
yourself if you want them gone.
