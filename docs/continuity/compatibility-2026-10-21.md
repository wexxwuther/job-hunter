# ChatGPT / OpenClaw compatibility handoff, 2026-10-21

This records the initial implementation checkpoint. For subsequent live ChatGPT
acceptance, OpenClaw discovery/execution, approvals and publication status, read
[the runtime acceptance record](../evals/runtime-acceptance-2026-10-21.md) and the
latest sections of `session-state.md` / `compaction-handoff.md` first. Pending-host
statements below describe that earlier checkpoint.

Goal: provide versions of the current job-hunter family for ChatGPT and OpenClaw.
Source: `E:/Git/job-hunter-public`, starting HEAD `b1d3431` (clean). Q is a
distribution catalog, not the source. Latest upstream release checked 2026-10-21:
v6.1.0. Retain current source and MIT license; no dependency or release upgrade.

## Changes and decisions

- `tools/build_runtime_packages.py`: deterministic standard-library ZIP builder.
  ChatGPT: one `job-hunter/SKILL.md` plus seven member `WORKFLOW.md` files, scripts,
  references and templates. OpenClaw: eight skill directories. Both strip Claude
  permission/context metadata, include runtime guidance, licenses and file hashes.
  Existing output archives are refused. Sources and gates are not rewritten.
- Orchestrator uses available subagents or sequential member workflows, preserving
  data dependencies. A missing member must actually be bundled or installed.
- `install/runtime-guide.md`, ChatGPT/OpenClaw guides and README document paths,
  tool gaps, hosted processing, downloadable state, and pending host acceptance.
- The shared `~/.agents/skills` path is supported by current OpenClaw in the
  default state; workspace roots are `skills/` and `.agents/skills/`, not
  `.openclaw/skills/`. Custom states exclude home-scoped personal roots.
- TypeSafe fit: exempt; exact file packaging and host-capability adaptation.
  No new semantic model, routing classifier, ranker or inference calls.

## Evidence and review

- Official docs checked 2026-10-21:
  https://help.openai.com/en/articles/20001066-skills-in-chatgpt
  https://docs.openclaw.ai/tools/skills
  https://docs.openclaw.ai/cli/skills
  https://developers.openai.com/api/docs/guides/tools-skills
- Governed task-orchestrator profile used for scoping; codebase-explorer delegate
  inspected actual source/installers/archives and independently reviewed changes.
  Tools: filesystem reads, rg, zipfile inventory, focused pytest, PyYAML parsing.
- Full CI-equivalent pytest command: 461 passed (455 existing + 6 new).
  Focused package suite: 6 passed after the description quoting fix. All 9 generated
  SKILL headers parsed with installed PyYAML. PyYAML is not a new runtime dependency.
- Reviewer found unquoted colon-space in generated description. Fixed using a
  JSON-quoted YAML scalar; regression test parses that scalar with `json.loads`.
- Each target has 71 archive entries. Link/resource checks, byte-identical gates,
  extraction into an unrelated directory, profile/workspace initialization,
  invented-claim flagging, export/restore, reproducibility and no-overwrite tested.
- Build outputs: `dist/compatibility/job-hunter-v6.1.0-{chatgpt,openclaw}.zip`.
  Q copies are staged under `Q:/skills/job-hunter/compatibility-preview/`, separate
  from existing v6.1.0 release assets. They are local, unreleased compatibility builds.

## Limits and pending operations

- OpenClaw CLI is absent from PATH. No live OpenClaw discovery or session test.
  ChatGPT upload/invocation has not been exercised in an account. Local archive
  tests prove contents and scripts, not target-host behavior or upload acceptance.
- No global installs, account changes, remote push, published release, applications
  or messages sent. Existing scripts, APIs, dependencies and user data unchanged.
- Elsie project resolved by exact repository identity; agent context and lifecycle
  read. Runtime doctor fails because MCP port 3012 is unreachable, while API 3013
  reports Postgres healthy. Ledger writes are deferred per doctor gate; sync this
  handoff through `runtime:closeout` after the managed runtime is repaired.
- Credential check: no `elsie_vault` binding rows returned for this project and
  `pnpm vault:doctor` reports connection_failed. Project credential storage remains
  unverified; no unlock, import or secret mutation. Package construction needs no
  product/provider credentials, so independent local work proceeded.
- Candidate durable memory: canonical compatibility builder and distinction
  between local package validation and actual host acceptance. No personal data,
  private research or raw delegate scratch is eligible for promotion.

Next step: use `install/chatgpt.md` and `install/openclaw.md` acceptance checks in
the intended hosts. Publish/install only within the user's authorization.
