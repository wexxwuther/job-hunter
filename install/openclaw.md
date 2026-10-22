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

Download `job-hunter-FAMILY-installer-only-v6.1.0.zip` from the
[latest release](https://github.com/wexxwuther/job-hunter/releases/latest), unzip it, and run
`bash job-hunter/install/install.sh` (Windows: `install\install.ps1` in the same folder).

## Project-scoped install

OpenClaw reads workspace skills from `<workspace>/skills/` and project agent skills
from `<workspace>/.agents/skills/`. To scope the family to one workspace, copy the
8 skill folders into either supported root, preserving their names.

For the compatibility build with Claude-only frontmatter removed:

```sh
python tools/build_runtime_packages.py --target openclaw
```

Extract the eight skill folders from `dist/compatibility/job-hunter-v6.1.0-openclaw.zip`
into `<workspace>/skills/` or the active state's managed `skills/` directory
(`~/.openclaw/skills/` by default). The archive also includes a root `bundle.json`
with file hashes; it is not a skill directory. This build is local, not an asset
of the existing GitHub release. Existing directories should be backed up and
compared before replacement.

With a custom `OPENCLAW_STATE_DIR`, home-scoped `~/.agents/skills/` is excluded;
use workspace skills or that state's managed directory instead. See
[OpenClaw's loading order](https://docs.openclaw.ai/tools/skills).

## Verify

Run `openclaw skills list`, `openclaw skills info job-hunter`, and
`openclaw skills check` in the intended profile. Check that all eight family names
are eligible, then start a new session. Ask for profile intake and a supplied
posting, exercise the fabrication gate with an invented claim, and export/restore
the workspace. Python, file access and browsing depend on the active agent's tool
policy. Discovery alone does not prove the full workflow works. See the
[runtime guide](runtime-guide.md) and [OpenClaw CLI reference](https://docs.openclaw.ai/cli/skills).

The [dated acceptance record](../docs/evals/runtime-acceptance-2026-10-21.md)
records the exact packages, runtime versions and tested capabilities. Our isolated
host uses OpenClaw 2026.10.5 and Node 24.16.0. For the optional Codex backend,
follow OpenClaw's [official Codex harness setup](https://docs.openclaw.ai/plugins/codex-harness).
Use its managed npm registry installation; a bare npm install plus
`plugins.load.paths`, or a local path link, did not establish the official
provenance required to register that harness. Check
`openclaw plugins inspect codex --runtime --json` before launching a test:
`agentHarnessIds` must include `codex`, with no error diagnostics.

## Uninstall

```bash
for s in job-hunter career-profile job-search resume-tailor cover-letter application-tracker interview-prep outcome-learning; do rm -rf ~/.agents/skills/$s; done
```

This also removes them from Codex, which shares `~/.agents/skills/`.
