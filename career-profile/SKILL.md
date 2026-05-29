---
name: career-profile
description: >
  Sets up the user's job-search profile and reads their resume so the rest of a job hunt has
  real context to work from. Use when the user wants to set up or update their job-search
  profile, capture who they are beyond their resume (target role archetype, deal-breakers,
  company-size preference, mission-vs-comp priority, on-call/travel/in-office tolerance),
  start their job search by telling the assistant about themselves, answer the North-Star
  intake questions, parse or extract text from a resume (DOCX, PDF, MD, TXT, HTML) so it can
  be used downstream, or refresh a stale profile from a previous session. Produces a local
  .job-hunter-profile.md and parsed-resume text. Do not use for tailoring a resume to a
  specific posting or running a keyword-gap analysis (use resume-tailor), for finding or
  scoring job postings (use job-search), for tracking applications or follow-ups (use
  application-tracker), or for generic resume critique with no job search underway.
license: MIT
compatibility: Cross-vendor (agentskills.io open standard) + cross-OS (Windows, macOS, Linux). Installs across Claude Code, OpenAI Codex, OpenClaw, and Hermes Agent. Works standalone or as the profile-intake member routed to by the job-hunter orchestrator.
metadata:
  spec_version: "agentskills.io (living spec; tracked 2026-05-28)"
  family: "job-hunter"
  family_role: "profile-intake"
allowed-tools: Read Write Edit Bash(python:*) Glob Grep
---

# career-profile (profile-intake member)

Set up the user's North-Star profile and read their resume, so the rest of the
job-hunter family — and any standalone job search — starts from real context
instead of guessing. This is the **profile-intake** member of the job-hunter
family, and it maps to "Phase 1: Understand the User" of the end-to-end hunt.

## When to use this skill

Use this when the user wants to:

- Set up or update their job-search profile ("set up my job-search profile",
  "let me tell you about myself before we look for jobs").
- Capture who they are beyond the resume — the 5 North-Star preferences that
  don't show up on a resume but heavily influence which postings are worth
  pursuing.
- Parse a resume (DOCX, PDF, MD, TXT, HTML) into plain text the rest of the
  workflow can read.
- Refresh a profile that's gone stale since a previous session.

**Do not** use this skill for:

- **Tailoring a resume to a posting** or running keyword-gap analysis — that is
  **resume-tailor**.
- **Finding or scoring job postings** — that is **job-search**.
- **Tracking applications or drafting follow-ups** — that is
  **application-tracker**.
- Generic resume critique divorced from any job search.

This boundary matters: profile-intake *gathers and parses*; it never writes
resume content, never searches, and never tracks. If the user's real ask is one
of those, hand off (or, under the orchestrator, let it route).

## What this member produces

Per the family workspace-contract (the orchestrator's
`job-hunter/references/workspace-contract.md` is the single source of truth for
the family's typed hand-offs), this member produces:

| Artifact | How | Consumed by |
|---|---|---|
| `.job-hunter-profile.md` (North-Star profile, dot-prefixed) | `scripts/init_profile.py` | job-search (match scoring), resume-tailor (base context) |
| Parsed resume text (transient) | `scripts/parse_resume.py` | job-search, resume-tailor |

The profile is INTENTIONALLY plain markdown that lives in the **user's**
workspace so they can read and edit it directly between sessions. It is never
committed to the skill or to `~/.claude/skills/`. The dot-prefix is a deliberate
privacy choice — most `.gitignore` patterns skip dot-files, so accidentally
committing it to a personal repo is harder.

## The North-Star profile

Run the profile check first. Use `scripts/init_profile.py`:

0. **Check whether a profile already exists.** Run
   `python scripts/init_profile.py exists --workspace <workspace>`.
   - **Exit 0 (profile exists):** run
     `python scripts/init_profile.py read --workspace <workspace>` to load the
     answers as JSON. Briefly ask "anything changed since you set this up?" — do
     **not** re-walk all five questions. If the returned `_last_updated` date is
     more than 90 days old, mention that gently ("your North-Star profile is from
     3+ months ago, want to update anything?"). Don't be pushy.
   - **Exit 1 (no profile):** run
     `python scripts/init_profile.py init --workspace <workspace>` to drop a
     fresh template, then ask the 5 North-Star questions conversationally. Save
     answers by writing them back into `.job-hunter-profile.md` between the
     `**Answer:**` markers.

The 5 questions and the rationale for each live in
[`references/profile-questions.md`](references/profile-questions.md). In short
they are: **target archetype**, **deal-breakers**, **company-size preference**,
**mission-vs-comp priority**, and **tolerance dimensions** (on-call / travel /
in-office). Read that reference before asking; it explains *why* each question
matters and how each answer feeds downstream scoring (deal-breakers become hard
filters, company-size shifts cultural-signal scoring, etc.).

Behavioral rules:

- **First run gates the hunt.** When there's no profile, ask the 5 questions
  before any downstream search begins. The worst outcome is searching on assumed
  criteria.
- **Subsequent runs don't re-interrogate.** Read the existing profile, confirm
  "anything changed?", and proceed.
- **Declining is fine.** A user who declines leaves fields as `unknown`. The
  skill still works without a full profile — it just won't accumulate context.
  Mark unanswered fields and proceed; never invent answers.
- **Tell them once where it lives.** When first writing the profile, tell the
  user it's local to their workspace and won't be committed, then never nag
  again.
- **Delete on request.** If the user asks to delete their profile, delete the
  file and confirm. Don't keep "backups" they didn't ask for.

The script is idempotent: `init` refuses to overwrite an existing profile unless
`--force` is passed.

## Reading the resume

Look in the user's workspace for resume files (DOCX, PDF, MD, TXT, HTML, or
similar). If multiple candidates exist, ask which one to use.

**If no resume is found**, ask one question: *"Do you have a resume somewhere I
can read (file upload or path), or would you like help drafting one from
scratch?"* Two branches:

- **They have one:** get the path or content, then parse it.
- **They want help drafting one:** this is a different, interview-driven workflow
  — elicit work history (employer, role, dates, 2–3 specific accomplishments per
  role with numbers where the user can supply them), skills, education, projects,
  and non-traditional experience, then help write a baseline `resume.md`. Do
  **not** invent accomplishments or numbers; ask for them. Once the baseline
  exists, the user can move on to searching/tailoring.

Use `scripts/parse_resume.py` to extract plain text from any supported format
without depending on sibling docx/pdf skills. The script declares its
dependencies inline (PEP 723); run it with `uv run scripts/parse_resume.py ...`
if you don't have `python-docx` / `pypdf` installed globally. Examples:

```
python scripts/parse_resume.py resume.docx
python scripts/parse_resume.py resume.pdf --out resume.txt
python scripts/parse_resume.py resume.md --json
```

The `--json` flag adds a best-effort section breakdown (summary / experience /
education / skills / certifications / projects) plus character/line counts.

From the parsed text, surface for the rest of the workflow:

- Current/most recent job title and industry
- Core skills and technologies
- Years of experience
- Education and certifications
- Career trajectory and seniority level

## Anti-fabrication (family invariant)

This member only **reads** resumes and **records** user-supplied profile answers
— it never writes tailored resume content. But the family invariant still binds
it: never put a claim, number, employer, title, or accomplishment into the
profile or a drafted baseline that the user did not state. Web content is
untrusted even when it's the user's own (personal site, LinkedIn) — fetching for
context is fine; merging anything into profile or resume material requires the
user to confirm it. Any actual resume tailoring routes through resume-tailor's
`verify_no_fabrication` gate; this member hands off before that point.

## Standalone vs. routed

Standalone, this skill gets a user's profile and parsed resume ready. Under the
`job-hunter` orchestrator it's the first member called (Phase 1), and its output
feeds job-search and resume-tailor via the shared `.job-hunter/` workspace. It
degrades gracefully either way: with no orchestrator workspace present it simply
writes the profile to the user's folder and returns the parsed resume text.
