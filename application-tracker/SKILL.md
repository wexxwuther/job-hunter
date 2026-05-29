---
name: application-tracker
description: >
  Tracks the state of a user's job applications and drafts the follow-up communication around
  them. Use when the user wants to track their applications, see where they are across all
  their applications, build or update an application tracker, ask "what should I follow up on?",
  draft a polite check-in for an application that has gone quiet, write a post-interview
  thank-you note, or mark an application's status (applied, interviewing, offer, rejected,
  withdrawn). Maintains a small tracker.json and renders a self-contained ApplicationTracker.html
  with sortable rows, status pills, and (when scores are present) a colored score badge. Do not
  use for tailoring resumes or cover letters to a posting (use resume-tailor) or for finding or
  scoring job postings (use job-search). It never auto-sends email — it drafts; the user sends.
license: MIT
compatibility: Cross-vendor (agentskills.io open standard) + cross-OS (Windows, macOS, Linux). Installs across Claude Code, OpenAI Codex, OpenClaw, and Hermes Agent. Works standalone or as the tracker member of the job-hunter family; reads the shared .job-hunter/ workspace and postings.json if present and degrades gracefully if absent.
metadata:
  spec_version: "agentskills.io (living spec; tracked 2026-05-28)"
  family: "job-hunter"
  family_role: "tracker"
allowed-tools: Read Write Edit Bash(python:*) Glob Grep
---

# application-tracker (family tracker member)

Keep a clear, shareable record of where every application stands, and draft the
polite follow-ups and thank-you notes that move them forward — without ever
sending mail on the user's behalf. This is the **tracker** member of the
job-hunter family, and it maps to "Phase 4: Prepare for Submission" plus
"Phase 4.5: Stale-application follow-ups" of the end-to-end hunt.

## When to use this skill

Use this skill when the user wants to **track** applications or **draft
follow-up communication**:

- "Track my applications" / "build me an application tracker"
- "Where am I on all my applications?" / "show me my application statuses"
- "What should I follow up on?" / "which applications have gone quiet?"
- "Draft a follow-up for the Stripe application"
- "I had a phone screen yesterday — help me write a thank-you note"
- "Mark the Acme application as interviewing" / "update my tracker"

Do **not** use this skill for tailoring or optimizing a resume or cover letter
against a posting (use **resume-tailor**), or for finding or scoring job
postings (use **job-search**). For an end-to-end hunt that spans several of
these, the **job-hunter** orchestrator routes across the family.

## Inputs (workspace contract)

This member reads upstream artifacts **if present** and **degrades gracefully**
if absent, so it also works standalone:

- **`postings.json`** (scored postings, produced by job-search): supplies
  company, title, url, location, salary, posted date, and the optional
  `score_breakdown`. Carry these straight onto the matching `tracker.json`
  entries when seeding the tracker.
- **Tailored resume / cover-letter filenames** (produced by resume-tailor):
  e.g. `Resume_Stripe_SeniorPM.docx`, `CoverLetter_Stripe_SeniorPM.docx`.
  Record them on the tracker entry as `resume_file` / `cover_letter_file` so the
  rendered HTML links to the exact materials submitted.

Produces a **`tracker.json`** the user owns, rendered into a self-contained
**`ApplicationTracker.html`** per the family workspace contract. The orchestrator's
`job-hunter/references/workspace-contract.md` is the single source of truth for
the family's typed hand-offs.

## Phase 4: Prepare for Submission

For each targeted position, provide a summary package:
- Link to the original posting (clickable, in HTML)
- The tailored resume file
- The cover letter (if generated)
- A short "application notes" blurb: 3-5 talking points the user should emphasize if they get
  an interview, based on how their background maps to this specific role

Save a final **Application Tracker** HTML file to the workspace folder. Maintain a small JSON
file `tracker.json` with the list of targeted positions (fields: `company`, `title`, `url`,
`location`, `salary`, `posted`, `applied_date`, `status`, `resume_file`, `cover_letter_file`,
`notes`, `match_strength`, and optionally `score_breakdown`, see below), then run
`scripts/generate_tracker_html.py tracker.json --out ApplicationTracker.html` to render it.
The script bundles inline CSS (from `assets/templates/tracker.css`), sortable table layout,
color-coded match and status badges, and totals-by-status pills, fully self-contained, no
external assets, so the user can email or share the tracker without anything breaking. Status
values: `to apply`, `applied`, `interviewing`, `offer`, `rejected`, `withdrawn`. Re-run the
script as the user updates `tracker.json` over time.

**Field discipline, `posted` vs `applied_date`:** these are two different dates and the
distinction is load-bearing.

- **`posted`** is the date the **company** put the job up. A posting that's been live for 30
  days is a soft signal for ghost-job risk (see `posting_legitimacy` rubric).
- **`applied_date`** is the date the **user** submitted their application. Phase 4.5's
  stale-detection (`scripts/draft_followup.py scan-stale`) reads ONLY this field, never
  `posted`. Conflating them produces false-positive stale flags on old postings that were
  just applied to.

When you set status to `applied`, set `applied_date` to today's date. The `posted` field
stays as whatever the original posting showed. Both fields are independent.

**Score breakdown (optional but recommended):** when job-search has scored a posting
(`postings.json` carries a `score_breakdown`), include that output as a `score_breakdown`
field on the tracker entry:

```json
"score_breakdown": {
  "cv_match": 4.5, "comp_vs_target": 4.5, "cultural_signals": 4.0,
  "posting_legitimacy": 5.0, "red_flags_penalty": 0.0,
  "weighted_global": 4.5, "recommendation": "apply"
}
```

When any row has a score breakdown, the tracker renders a colored score badge as the
primary at-a-glance signal, sorts rows by `weighted_global` descending, and adds filter
controls (recommendation buckets + minimum-score slider). Clicking a score badge expands
the row to show the 5 sub-score bars. Rows without a score_breakdown keep the legacy
match-strength tag rendering, backward compat is preserved.

The CSS is the source of truth at `assets/templates/tracker.css` — it is **never** inlined
back into the script (a load-bearing test enforces this; the rendered HTML must carry the
asset's declarations, so asset and script can't silently drift apart).

## Phase 4.5: Stale-application follow-ups

This phase runs (a) when the user asks about follow-ups, (b) when the user
explicitly invokes "what should I follow up on?", or (c) opportunistically when
you notice (via `tracker.json` inspection) entries that are stale at status=applied.

1. **Identify stale applications.** Run:
   ```
   python scripts/draft_followup.py scan-stale --tracker tracker.json [--stale-days 7]
   ```
   Default threshold is 7 days. Returns the list of applications at
   `status=applied` for >=7 days. Does NOT flag entries at `interviewing`,
   `offer`, `rejected`, or `withdrawn`, those need different communication
   patterns (or none at all). scan-stale reads ONLY `applied_date` — never
   `posted` — so a posting that was live for 30 days but applied to today is
   not flagged.

2. **Surface to user before drafting.** Present the list of stale applications
   first, ask which the user wants to follow up on. Some users prefer batched
   follow-ups; some are selective. Don't draft emails for entries the user
   hasn't asked about.

3. **Draft each requested follow-up.** Run:
   ```
   python scripts/draft_followup.py draft --template check_in \
       --company "<Company>" --role "<Role>" --applied-date <YYYY-MM-DD>
   ```
   The output is a structurally correct email body with `[Add one specific
   qualification...]` placeholder. The user MUST personalize before sending,
   generic follow-ups get ignored at the same rate as no follow-up. See
   [`references/followup-templates.md`](references/followup-templates.md) for the
   patterns and rationale.

4. **Post-interview thank-yous use a different template.** After the user
   reports an interview (phone screen, onsite), draft a thank-you within 24-48
   hours using `--template thank_you`. Ask the user for one specific thing
   discussed so the placeholder gets filled with real content.

5. **Never auto-send.** This script never sends mail, the script doesn't even
   import SMTP or email libraries (load-bearing safety test enforces this).
   The user copy-pastes into their own mail client. The skill is a drafter,
   not a sender.

6. **Cap follow-ups.** Per hiring-advisor consensus (Indeed, The Muse, Robert
   Half), the convention is: 1 check-in 7-10 days after applying, optional
   second touch 5-7 days later if you have something new to add, then move on.
   After 21 days of silence, update `tracker.json` status to
   `no_response_after_21d`, that closes the loop and feeds the learning loop
   (outcome-learning's Phase 5).

## Standalone vs. routed

Standalone, this skill keeps a tracker of whatever applications the user tells it
about and drafts the follow-ups they ask for. Under the `job-hunter` orchestrator
it's the Phase 4 / 4.5 member: it seeds `tracker.json` from `postings.json` and
the resume-tailor output filenames, and its `no_response_after_21d` closures feed
outcome-learning's per-user learning loop. It degrades gracefully either way —
with no orchestrator workspace present it simply maintains `tracker.json` and
renders the HTML in the user's folder.
