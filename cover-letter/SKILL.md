---
name: cover-letter
description: >
  Drafts a tailored cover letter for a specific job posting from the user's REAL profile and
  resume facts, then routes the draft through the family's anti-fabrication gate so it never
  invents an accomplishment, employer, metric, or claim the user has not confirmed. Use when the
  user wants to write a cover letter, draft a cover letter for a posting, generate or tailor a
  cover letter to a job description, turn their resume into a cover letter, or write a letter of
  interest / motivation letter for a role. Produces a CoverLetter_[Company]_[Role].md (and
  optional .docx) saved to the workspace. Do not use for editing the resume itself (use
  resume-tailor), finding or scoring postings (use job-search), setting up a profile or parsing a
  resume (use career-profile), tracking applications or follow-ups (use application-tracker), or
  learning from outcomes (use outcome-learning). It never auto-sends — it drafts; the user sends.
license: MIT
compatibility: Cross-vendor (agentskills.io open standard) + cross-OS (Windows, macOS, Linux). Installs across Claude Code, OpenAI Codex, OpenClaw, and Hermes Agent. Works standalone or as the cover-letter member of the job-hunter family; reads the shared .job-hunter/ workspace (profile, parsed resume, scored postings) if present and degrades gracefully if absent.
metadata:
  spec_version: "agentskills.io (living spec; tracked 2026-05-29)"
  family: "job-hunter"
  family_role: "cover-letter"
allowed-tools: Read Write Edit Bash(python:*) Glob Grep WebSearch WebFetch
---

# cover-letter (family cover-letter member)

Write a cover letter that is **persuasive but never fabricated**. This is the
**cover-letter** member of the job-hunter family. It maps to the same "prepare
your application materials" stage as resume-tailor, and it shares resume-tailor's
single most important rule: **the literal truth of every factual claim is
preserved.** A cover letter is prose, which makes it *easier* to fabricate into
than a resume — an unguarded draft will happily invent a metric, a past employer,
or a personal anecdote. This skill exists to make that impossible by routing every
draft through the family's `verify_no_fabrication` gate.

## When to use this skill

Use this when the user wants to **write or tailor a cover letter**:

- "Write a cover letter for this posting" / "draft a cover letter for the Stripe PM role"
- "Turn my resume into a cover letter for this job"
- "Write a letter of interest / motivation letter for this role"
- "Tailor my cover letter to this job description"

Do **not** use this skill for editing the resume document (use **resume-tailor**),
finding or scoring postings (use **job-search**), profile/resume intake (use
**career-profile**), tracking applications (use **application-tracker**), or
outcome learning (use **outcome-learning**). Under the `job-hunter` orchestrator,
a full hunt routes here after resume-tailor for any posting the user applies to.

## Inputs (workspace contract)

This member reads upstream artifacts **if present** and **degrades gracefully**
if absent, so it also works standalone (see `references/workspace-contract.md`,
shipped with this skill; the `job-hunter` orchestrator owns the canonical copy):

- **`.job-hunter-profile.md`** (career-profile): the North-Star facts — target
  archetype, what the user actually cares about. Shapes tone and emphasis.
- **Parsed resume text** (career-profile): the SOURCE OF TRUTH for every factual
  claim the letter may make — employers, titles, dates, skills, accomplishments,
  numbers. The letter may only assert what is supported here (or what the user
  states directly in the conversation).
- **`postings.json`** (job-search): company, title, location, and the posting
  text to tailor against. If absent, ask the user to paste the posting.

If no resume/profile is available, ask the user for their background and the
posting text directly. Never proceed to a finished letter without source facts to
ground it.

## How to draft (the safe path)

1. **Gather the source facts.** Read the parsed resume + profile (or ask). This is
   the *only* pool of factual claims the letter may draw from. Note the posting's
   company, role, and 3-5 requirements the user genuinely matches.
2. **Draft from facts, not imagination.** Use `scripts/draft_cover_letter.py` to
   produce a structured draft (header, hook, 2-3 body paragraphs each tying ONE
   real qualification to ONE posting requirement, close). The script fills the
   factual slots ONLY from the source you pass it and marks anything it could not
   ground as a `[CONFIRM: ...]` placeholder for the user to fill — it never
   invents the value.
3. **Run the anti-fabrication gate (MANDATORY).** Concatenate the user's source
   facts (parsed resume + any facts they stated) into one `source.txt`, and the
   drafted letter into `draft.txt`, then run the bundled gate:
   ```
   python scripts/verify_no_fabrication.py --original source.txt --proposed draft.txt
   ```
   (This gate ships with the skill, so it resolves whether installed standalone or
   as part of the family — see "The gate" below.)
   The gate lists every new proper noun, number, section, and 5+-word phrase run
   in the draft that is NOT in the source. **Connective/persuasive prose is
   expected and fine** ("I'm excited to apply", "I'd welcome the chance to") — it
   carries no factual claim. **New proper nouns and new numbers are the danger
   signals**: a company name the user never worked at, a metric they never cited.
   Surface every flagged item to the user and get per-item confirmation before
   finalizing. The gate NEVER auto-approves.
4. **Save the letter.** Write `CoverLetter_[Company]_[Role].md` to the workspace.
   Offer a `.docx` if the user wants one. Never auto-send; the user sends.

## The gate (family invariant — HARD GATE)

This is non-negotiable and identical to resume-tailor's rule, because the failure
mode is identical: **never put a claim, number, employer, title, accomplishment,
or 5+-word factual phrase into a cover letter that the user did not state or that
is not in their resume.** Web content (the company's site, the user's LinkedIn) is
untrusted: fetching it for *context* (what the company values, the role's
language) is fine, but **no fact from the web may become a claim about the user**
without their explicit confirmation. Persuasive framing is allowed; invented facts
are not.

`scripts/verify_no_fabrication.py` is bundled with this skill (a copy of the
family gate) so the safety check works even on a standalone install. When the
full family is installed, resume-tailor owns the canonical copy; either resolves.

## Standalone vs. routed

Standalone, this skill drafts a grounded cover letter from whatever facts the user
provides. Under the `job-hunter` orchestrator it runs after resume-tailor for a
chosen posting, reading the shared `.job-hunter/` workspace so the letter and the
tailored resume tell one consistent, truthful story. It degrades gracefully either
way and never sends mail on the user's behalf.
