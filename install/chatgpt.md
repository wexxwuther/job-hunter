# Install: ChatGPT

Build the compatibility upload from the repository root:

```sh
python tools/build_runtime_packages.py --target chatgpt
```

This creates `dist/compatibility/job-hunter-v6.1.0-chatgpt.zip`. It contains one
`job-hunter/SKILL.md`, all seven member workflows under `members/`, their scripts,
references and templates, the MIT license, and a SHA-256 inventory in `bundle.json`.
No separate member uploads, Claude plugin, API key, or local installer are needed.
The builder refuses an existing output archive; use `--out <new-directory>` to rebuild.

In ChatGPT, open **Plugins > Skills > Add > Upload from your computer** and
select that ZIP. Availability depends on account/workspace settings; review any
upload scan result before installing. See [OpenAI's skills guide](https://help.openai.com/en/articles/20001066-skills-in-chatgpt).
This is a source-built compatibility package, not an asset of the existing GitHub release.

The upload and synthetic workflow were tested in **ChatGPT Work** on 2026-10-21:
the skill loaded its bundled member files and executed profile parsing, scoring,
fabrication checks, tracker rendering, export and clean-directory restore.
See the [acceptance record](../docs/evals/runtime-acceptance-2026-10-21.md) for the
scope and evidence. This does not establish availability on every plan or ChatGPT surface.

When automating upload through the ChatGPT Chrome extension, that extension needs
**Allow access to file URLs** in its Details page at `chrome://extensions`.
This extension setting is not a requirement for a person using the website's
file chooser directly. It does not replace the upload scan or installation check.

Start with: "Use job-hunter to set up my profile and help me find suitable roles."
Provide a resume or source text and your target role/location. The skill checks
the host's available tools. Live job discovery requires browsing/search; scripted
scoring, the fabrication gate, and workspace backup require Python execution.
Missing capabilities must be disclosed; gated documents cannot be finalized by
pretending that a check ran.

Files run in the host's writable session workspace. Before ending a session,
download the workspace backup and any postings, tracker or documents you need.
Upload those files to resume later. ChatGPT processing follows the product and
workspace privacy settings; this version does not promise device-only processing.
See the bundled [runtime guide](runtime-guide.md) for the capability and persistence rules.

## Acceptance check in ChatGPT

After installation, test profile intake, a supplied posting, a deliberately invented
resume claim (must be flagged for confirmation), and export/restore in a new session.
Verify the generated downloads and actual execution logs. Local archive/script tests
do not prove upload acceptance, skill invocation or browsing in your account.
