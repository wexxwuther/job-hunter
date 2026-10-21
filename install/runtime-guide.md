# Runtime capabilities and workspace handling

Read this before using a generated ChatGPT or OpenClaw package. These host rules
qualify the local-workspace assumptions in the member workflows.

- Resolve every `scripts/`, `references/`, and `assets/` path relative to the
  workflow file being read, not the current working directory. Use absolute
  script paths and pass user input/output paths explicitly. In the ChatGPT
  package, a member's base is `members/<member>/`; its instructions are in
  `WORKFLOW.md`. The orchestrator's base is the package root.
- Use the host's actual file-reading, Python execution, search/browser, and
  document tools. `Read`, `Bash`, `Task`, and `context: fork` are Claude-specific
  names, not prerequisites or permissions. Do not invent missing tools.
- With no subagents, read the selected workflows and execute them sequentially.
  Keep profile -> search -> selected posting -> documents -> tracker dependencies.
  Follow the member's disclosed same-context reviewer fallback. Review is advisory;
  it never replaces the mandatory fabrication gate or user confirmation of flags.
- With no Python execution or missing parsing libraries, ask for readable resume
  text or provide preliminary analysis. Do not silently install dependencies,
  simulate script output, call an unrun gate passed, or finalize a gated document.
- With no live search, work from supplied postings and label freshness and
  legitimacy unverified. Do not fabricate openings, URLs, salaries, or source dates.
- Keep user artifacts in a separate writable workspace, never inside the installed
  skill. Use only files supplied or authorized by the user. Do not scan a home
  directory or assume access to a desktop, previous chat, or installed sibling.

## ChatGPT

The generated package contains one discoverable skill plus the seven member
workflows and their resources. Read only the workflows needed for the request.
Use a writable session directory offered by the host and keep the same workspace
throughout the run. No fixed `/mnt/data` path or shell tool is assumed.

ChatGPT-hosted uploads and generated files are processed in the hosting product.
Statements in member workflows about "local-only", "never uploaded", or "out of
the cloud" describe local agents; they do not promise device-only processing in
ChatGPT. Apply the account/workspace's actual privacy and retention settings.
Do not send resume contents to an additional external service without authorization.

Do not promise that session files persist. Before closing a stateful hunt, use
the bundled `scripts/export_workspace.py` to produce a downloadable workspace
archive and separately offer `postings.json`, approved documents, interview packs,
and tracker HTML (the export helper does not include all of these). On resumption,
ask for the saved archive/files and restore via `scripts/import_workspace.py`;
never infer missing state from model memory. If export/execution is unavailable,
provide the available state as downloadable files or copyable text and say what
was not saved. Treat all exports as personal data; do not publish them.

## OpenClaw

Extract the family archive's eight skill directories into `<workspace>/skills/`
for one workspace, or the active state's `skills/` directory for managed sharing
(`~/.openclaw/skills/` by default). `~/.agents/skills/` is also supported in the
default state and shared with Codex. A custom `OPENCLAW_STATE_DIR` excludes that
home-scoped personal root. Do not use `<workspace>/.openclaw/skills/`.

Run `openclaw skills list`, `openclaw skills info job-hunter`, and
`openclaw skills check` in the intended profile; verify all eight names are loaded
and eligible, then start a new session. Discovery is distinct from execution:
Python, file access, and browsing must also be permitted by that agent's policy.
Do not change gateway settings, allowlists, credentials, or messaging permissions
to make a skill work. Draft applications and follow-ups; sending or submitting
still requires the user's authorization.
