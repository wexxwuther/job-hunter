# Install: OpenAI Codex

Codex loads agentskills.io skills from `~/.agents/skills/`. job-hunter is a family of 8
skills (the `job-hunter` orchestrator plus 7 members); install all 8.

## Option 1, one-shot installer (recommended)

Copies all 8 skills to `~/.agents/skills/<skill>/` (and to the Claude Code and Hermes
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

For an in-app uploader, the release also has 8 `-codex.zip` files, one skill each.

## Verify

Start a new Codex session and ask:

```
What nurse practitioner jobs near Austin would I be a strong fit for?
```

You should be asked the North-Star profile questions on first use.

## Notes on Codex compatibility

- The skills use no Codex-specific APIs.
- If your Codex reads a different skills directory, copy the 8 folders from
  `~/.agents/skills/` there.
- Open an Issue if you hit a Codex-specific bug.

## Uninstall

```bash
for s in job-hunter career-profile job-search resume-tailor cover-letter application-tracker interview-prep outcome-learning; do rm -rf ~/.agents/skills/$s; done
```

This also removes them from OpenClaw, which shares `~/.agents/skills/`.
