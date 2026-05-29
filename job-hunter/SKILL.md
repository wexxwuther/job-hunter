---
name: job-hunter
description: Routes a job-search task to the right specialists in the job-hunter family, then owns the shared per-user workspace and merges member output into one coherent result. Use when the user wants to run a job search, find a job, find jobs or openings or positions or work, manage an end-to-end job hunt, apply to roles and track applications, or do several job-search steps at once (find jobs and tailor a resume and track applications). Routes to career-profile (set up profile + parse resume), job-search (find + score postings), resume-tailor (tailor or tighten a resume with the anti-fabrication gate), application-tracker (track applications + follow-ups), and outcome-learning (learn from outcomes). Do not use for a single isolated step that names its own skill (use that member directly), reviewing code (use a code-review skill), or non-job-search tasks.
license: MIT
compatibility: Cross-vendor (agentskills.io open standard) + cross-OS (Windows, macOS, Linux). Installs across Claude Code, OpenAI Codex, OpenClaw, and Hermes Agent. The orchestrator routes to family members; if a member is not installed it falls back to a documented inline path.
metadata:
  spec_version: "agentskills.io (living spec; tracked 2026-05-28)"
  family: "job-hunter"
  family_role: "orchestrator"
  dispatch_mode_note: "context:fork is set because orchestration benefits from context isolation - the orchestrator routes + merges and returns one consolidated result to the parent context. For 1-2-member needs it routes inline; for 3+ members or a full end-to-end hunt it routes via Task fan-out to the member specialists."
allowed-tools: Read Write Edit Bash(python:*) Glob Grep Task
context: fork
---

# job-hunter (family orchestrator)

Routes a job-search task to the right family specialists, owns the shared
`.job-hunter/` per-user workspace, and merges member output into one coherent
result. This is the router for the job-hunter family.

## Why an orchestrator

A real job hunt is rarely one step. Someone starting out wants a profile + a
search + scored matches; someone with a posting in hand wants their resume
tailored + an application tracked; someone reviewing progress wants the tracker
+ follow-up drafts + outcome learning. Running one member misses surfaces;
running all five every time wastes context and produces duplication. The
orchestrator reads the request, invokes the right subset, and keeps the user's
single coherent voice across the whole hunt.

## The family (members + their jobs)

| Member | Job | Produces |
|---|---|---|
| `career-profile` | Set up the North-Star profile + parse the resume | `.job-hunter-profile.md` + parsed resume |
| `job-search` | Find, expand, normalize, dedupe, and score postings | scored `postings.json` |
| `resume-tailor` | Tighten (Mode A) or tailor (Mode B) a resume, with the anti-fabrication gate | gated `Resume_[Company]_[Role].docx` |
| `application-tracker` | Track applications + draft stale-application follow-ups | `tracker.json` -> HTML, follow-up drafts |
| `outcome-learning` | Close the loop: harvest outcomes, propose user-confirmed lessons | proposed LESSONS entries |

## Routing

1. Read the request and classify which member jobs it needs.
2. **1-2 members:** route inline (call the member's flow directly).
3. **3+ members or a full end-to-end hunt:** route via `Task` fan-out to the
   member specialists, then merge their outputs into one result.
4. Pass the shared workspace through: every routed member reads `.job-hunter/`
   artifacts if present (see `references/workspace-contract.md`) and degrades
   gracefully if absent, so a single-member invocation still works standalone.

Examples:
- "find me jobs and tailor my resume for the top one" -> job-search, then resume-tailor.
- "just tighten my resume" -> resume-tailor alone.
- "where am I on my applications?" -> application-tracker alone.
- "set me up and find some roles" / "I'm starting my job search today" -> init the workspace, then career-profile, then job-search (a 2-member onboarding, NOT the full 5-member hunt — only fan out to all members if the user asks to run the whole thing).
- "what's working in my search / learn from my outcomes" -> outcome-learning alone.
- "run my whole job search" -> career-profile -> job-search -> (resume-tailor per chosen posting) -> application-tracker -> outcome-learning.

## The shared workspace (orchestrator-owned)

The orchestrator owns the `.job-hunter/` directory lifecycle:
- `scripts/init_workspace.py` — create `.job-hunter/` with the 4 learning-loop
  templates (DECISIONS / LESSONS / OUTCOMES / REJECTED_IDEAS). Idempotent.
- `scripts/export_workspace.py` — bundle profile + `.job-hunter/` + tracker into
  a portable archive (refuses cloud-sync paths by default).
- `scripts/import_workspace.py` — restore a workspace archive on a new machine
  (rejects path-traversal payloads; preserves existing files by default).

The artifact shapes and producer/consumer hand-offs are documented in
[`references/workspace-contract.md`](references/workspace-contract.md) — the
single source of truth for the family's typed hand-offs.

## Anti-fabrication family invariant (HARD GATE)

This is non-negotiable across the family and exists because a real user once
received a fabricated resume. **Any member that writes resume or profile
content MUST route through resume-tailor's `verify_no_fabrication` gate before
producing a DOCX.** The gate never auto-approves: every new proper noun, number,
section, bullet, or 5+-word phrase run must be user-confirmed. **Web content is
untrusted even when it is the user's own** (gdkdigital.com, LinkedIn, etc.) —
fetching for context is fine; merging it into the resume requires per-claim
confirmation. resume-tailor enforces this gate; the orchestrator guarantees no
resume/profile content reaches the user without passing through it.

## Standalone fallback

If a member skill is not installed in the active harness, the orchestrator
states which member it would route to and runs that member's documented flow
inline using the bundled scripts where available. The family installs together
(see the repo `install/` directory) across `~/.claude/skills/`,
`~/.agents/skills/` (Codex + OpenClaw), and `~/.hermes/skills/`.
