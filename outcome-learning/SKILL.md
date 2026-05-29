---
name: outcome-learning
description: Closes the per-user learning loop for the job hunt — harvests patterns from real application outcomes and proposes durable lessons the user confirms. Use when the user wants to learn from their job-search outcomes, asks "what's working in my search" or "what have you learned about me", wants to close the loop on applications, harvest lessons from rejections and offers, surface patterns across closed-loop outcomes, reset what the skill remembers about their preferences, or review the accumulated DECISIONS / LESSONS / OUTCOMES / REJECTED_IDEAS notes in their workspace. Reads the user's local .job-hunter/ learning-loop files and translates signals into suggested lessons, gated behind a 5-closed-outcome cold-start guard and an opt-in confirmation step (never auto-writes). Do not use for searching jobs (use job-search), tracking applications or drafting follow-ups (use application-tracker), tailoring a resume to a posting (use resume-tailor), or setting up the North-Star profile (use career-profile).
license: MIT
compatibility: Cross-vendor (agentskills.io open standard) + cross-OS (Windows, macOS, Linux). Installs across Claude Code, OpenAI Codex, OpenClaw, and Hermes Agent. Works standalone or as the learning-loop member of the job-hunter family; reads the shared .job-hunter/ workspace if present and reports honestly when it is absent or under the cold-start threshold.
metadata:
  spec_version: "agentskills.io (living spec; tracked 2026-05-28)"
  family: "job-hunter"
  family_role: "learning-loop"
allowed-tools: Read Write Edit Bash(python:*) Glob Grep
---

# outcome-learning (family learning-loop member)

Remember what works for *this* user across sessions, while keeping every byte of
that memory in their workspace and out of the cloud. This is the **learning-loop**
member of the job-hunter family: the read side of the per-user memory layer that
keeps the family from re-litigating settled preferences and that surfaces durable
patterns — but only ones the user has confirmed.

See `references/learning-loop-guide.md` for the full design.

## When to use this skill

Use this skill when the user wants to **learn from outcomes** or **inspect the
per-user memory**:

- "What have you learned about me from my job search so far?"
- "What's working in my search?" / "What patterns do you see?"
- "Close the loop on my applications" / "Harvest lessons from my outcomes"
- "Show me my application outcomes so far"
- "Reset what you know about my preferences"

Do **not** use this skill for **finding** or **scoring** job postings (use
**job-search**), tracking applications or drafting follow-up / thank-you emails
(use **application-tracker**), tailoring or optimizing a resume against a posting
(use **resume-tailor**), or setting up the North-Star profile / parsing a resume
(use **career-profile**). For an end-to-end hunt that spans several of these, the
**job-hunter** orchestrator routes across the family.

## Inputs (workspace contract)

This member **reads** the four per-user learning-loop files. They live under
`<your-workspace>/.job-hunter/` and are written by the user and, with the user's
confirmation, by the agent:

| File | Who writes | Purpose |
|---|---|---|
| **REJECTED_IDEAS.md** | User only, agent never writes here | Hard constraints ("no defense contractors", "no commission-only comp"). Filters, not preferences. |
| **LESSONS.md** | User, confirmed via agent suggestions | Durable patterns that adjust how sub-scores are *graded* for this user. |
| **DECISIONS.md** | Agent (with the user's reasons) + user | Per-session record of meaningful choices, for continuity. |
| **OUTCOMES.md** | Agent (on tracker status changes) + user | What actually happened: accepted, rejected after onsite, no response after 21 days. |

**Workspace ownership.** The `.job-hunter/` directory and its four template files
are **owned by the orchestrator's `init_workspace.py`**, not by this member.
outcome-learning does not create or template the workspace — it **reads** the
files the orchestrator (or the user) has already created, per the family
workspace-contract. If the workspace does not exist, this skill reports that
honestly and points the user at the orchestrator to initialize it; it does not
fabricate the files itself.

## Phase 0: Load the per-user learning loop

**Run this once at the start of every session, before doing anything else.** The
learning loop is the per-user memory layer that keeps the skill from re-litigating
settled preferences and that surfaces durable patterns across sessions.

1. **Check the workspace state.** Confirm `<workspace>/.job-hunter/` exists with
   the four files (DECISIONS.md, LESSONS.md, OUTCOMES.md, REJECTED_IDEAS.md).
   - **If it does not exist:** the workspace has not been initialized. The
     `.job-hunter/` directory is owned by the orchestrator's `init_workspace.py`,
     not by this member. Tell the user there is nothing to learn from yet and
     point them at the job-hunter orchestrator (or `job-search`) to set up the
     workspace and start applying. Do not fabricate the files here.
   - **If it exists:** proceed to read the four files.

2. **Read the four files in priority order:**
   - **`.job-hunter/REJECTED_IDEAS.md` (HARD constraints)**: read first. Any entry
     here is a hard filter the user has explicitly told the family to apply. Do NOT
     re-ask about these, and never auto-add entries — only the user adds rejected
     ideas.
   - **`.job-hunter/LESSONS.md` (durable preferences)**: these are user-confirmed
     patterns about how the user evaluates postings. They influence how downstream
     members *grade* the five sub-scores (cv_match, comp_vs_target,
     cultural_signals, posting_legitimacy, red_flags_penalty) — they do NOT change
     the weights in `score_posting.py` (owned by job-search; those stay constant
     for all users). When a lesson applies, cite it so the user can audit.
   - **`.job-hunter/DECISIONS.md` (recent context)**: skim the last 5-10 entries
     for continuity. If the user previously gave a reason for a choice, prefer the
     same reasoning unless context has changed.
   - **`.job-hunter/OUTCOMES.md` (closed-loop history)**: count the closed entries.
     If ≥5, you may run Phase 5 to surface patterns.

3. **Cold-start respect.** On a brand-new workspace, the four files are empty
   templates. Do NOT pretend to have lessons or rejected ideas. Report the honest
   state and suggest applying to more roles so outcomes accumulate.

## Phase 5: Close the loop (per-user learning)

This phase runs (a) when the user updates a tracker.json status past `applied`
(the orchestrator or application-tracker appends the outcome; this member then
harvests), (b) at end of session if at least one outcome changed, or (c) when the
user asks "what have you learned about me?" / similar. See
`references/learning-loop-guide.md` for the full design.

1. **Append outcomes.** When a tracker.json status moves to `interviewing`,
   `offer`, `rejected`, or `withdrawn`, a properly formatted entry should be
   appended to `.job-hunter/OUTCOMES.md` (format documented in the template).
   Always include the agent recommendation at time of apply (`apply` /
   `apply_if_specific_reason` / `skip`) so calibration analysis works. If the user
   gives a reason, include it; if not, leave the reason field blank rather than
   guessing. (Outcome capture on status changes is owned by the orchestrator /
   application-tracker; this member reads the result.)

2. **Harvest signals.** When `.job-hunter/OUTCOMES.md` has ≥5 closed entries, run:
   ```
   python scripts/harvest_outcomes.py --workspace <workspace> --out signals.json
   ```
   The script enforces a **cold-start guard**: if fewer than 5 closed outcomes
   exist, it returns `no_op_reason: "need >=5 closed-loop outcomes, have N"`. Do
   NOT fabricate lessons from thin data. If the cold-start guard fires and the user
   asks what you've learned, report the honest count and suggest concrete next
   steps (apply to more roles, update tracker.json status as outcomes land).

3. **Translate signals to suggestions.** When the harvest returns signals, run:
   ```
   python scripts/propose_lessons.py --signals signals.json --out proposal.json
   ```
   The output is a list of suggested LESSONS.md entries, each with evidence and a
   confidence tier. The translation is deterministic — the same signals always
   produce the same suggestions, and each suggestion's reason line is anchored in
   the observed evidence count, never paraphrased.

4. **Surface to user, with evidence, for confirmation.** For each suggestion in
   the proposal:
   - Present the pattern + the underlying evidence (e.g., "4 of 5 rejections cite
     comp as the reason").
   - Ask explicitly: *"Want me to remember this?"*
   - If confirmed, append the suggestion's `lesson_block` to
     `.job-hunter/LESSONS.md` verbatim (the script formatted it properly). Add a
     `**Confirmed:** <date>` marker on the line right after the heading.
   - If rejected, do NOT append. Do NOT re-propose the same pattern next session
     unless new evidence makes it stronger (e.g., 4 of 5 → 7 of 8).

5. **Never auto-write to LESSONS.md.** The opt-in confirmation gate is
   load-bearing. The user owns the lessons log. The agent suggests; the user
   decides. (`propose_lessons.py` itself never writes to LESSONS.md — its
   `application_guidance` field always reminds the agent of this contract.)

6. **Never auto-write to REJECTED_IDEAS.md.** This file is the user's veto list,
   not the agent's pattern guesses. Only entries the user has explicitly stated
   (e.g., "stop suggesting government jobs", "I told you no commission-only roles")
   should land here.

## The signals harvest produces

`harvest_outcomes.py` reads `OUTCOMES.md` (and `DECISIONS.md` as a secondary
signal) and classifies closed-loop outcomes into deterministic signals:

- **`rejection_dominant_reason`** — one reason (comp, culture, size, remote,
  responsibilities, no_response) cited in ≥50% of rejections.
- **`recommendation_calibration`** — how often the agent's `apply` recommendation
  actually led to a positive outcome (precision), surfaced only when ≥5 entries
  carry both an `agent_rec` and an `outcome`.

`propose_lessons.py` then maps each signal to a category-specific suggested
LESSONS.md entry, with a confidence tier that escalates with evidence count
(≥10 → high, ≥5 → medium, otherwise low). A well-calibrated agent (precision ≥
0.7) yields no calibration lesson — there is nothing to fix.

## Privacy and reset

- Everything is **local-only**: no telemetry, no phone-home. The `.job-hunter/`
  directory lives in the user's workspace; the scripts read local files only.
- `signals.json` and `proposal.json` written by the scripts contain workspace
  data — treat them as user-private.
- The user can **delete `.job-hunter/`** at any time without breaking the family
  (the orchestrator re-initializes empty templates on the next run). Reasons:
  career pivot where past lessons no longer apply, a privacy reset on a shared
  workspace, or a suspicion that a confirmed lesson is wrong (faster to nuke +
  rebuild than to edit entry-by-entry).

## Key principles

- **Cold-start guard.** No lessons proposed until at least 5 closed-loop outcomes.
  Pattern detection from thin data is guessing, not learning.
- **Opt-in only.** The agent never auto-writes to LESSONS.md or REJECTED_IDEAS.md.
  Every entry there required the user to say yes.
- **Deterministic translation.** Same signals in, same suggestions out; the reason
  line is anchored in evidence, never paraphrased.
- **Bounded influence.** Lessons adjust how sub-scores are *graded* for this user.
  They do not change the scoring weights — those stay constant for everyone.
- **This member reads; the orchestrator owns the workspace.** outcome-learning
  consumes `.job-hunter/*.md`; it does not own `init_workspace.py` or the
  templates that create them.

See `references/learning-loop-guide.md` for the full design, the six guardrails,
and guidance on when to nuke and start over.
