# `.job-hunter/` Workspace Contract

The single source of truth for the artifacts the job-hunter family members
produce and consume. The orchestrator (`job-hunter`) owns the `.job-hunter/`
directory lifecycle (create via `init_workspace.py`, move via
`export_workspace.py` / `import_workspace.py`). Every member reads upstream
artifacts **if present** and **degrades gracefully** if absent, so each member
also works standalone.

## Directory layout

```
.job-hunter/                     (per-user, created by the orchestrator; gitignored in user projects)
├── DECISIONS.md                 per-session decisions log     (template owned by orchestrator)
├── LESSONS.md                   user-confirmed patterns       (template owned by orchestrator)
├── OUTCOMES.md                  closed-loop outcomes          (template owned by orchestrator)
├── REJECTED_IDEAS.md            user-only hard constraints    (template owned by orchestrator)
├── profile.md                   North-Star profile            (produced by career-profile)
├── postings.json                scored postings               (produced by job-search)
└── tracker.json                 application tracker            (produced by application-tracker)
```

`profile.md` lives at `.job-hunter-profile.md` (dot-prefixed) per
`init_profile.py`'s contract; the parsed-resume text is transient (passed
between members, not persisted by default).

## Artifact hand-offs (producer → consumer)

| Artifact | Producer | Consumed by | Degrade-if-absent behavior |
|---|---|---|---|
| `.job-hunter-profile.md` (North-Star profile) + parsed resume text | **career-profile** (`init_profile.py`, `parse_resume.py`) | job-search (match scoring), resume-tailor (base resume) | job-search scores on explicitly-provided criteria; resume-tailor works from a pasted resume |
| `postings.json` (scored) | **job-search** (`score_posting.py` et al.) | resume-tailor (pick a posting to tailor for), application-tracker (seed tracked apps) | resume-tailor tailors for a JD the user pastes; tracker tracks manually-entered apps |
| `Resume_[Company]_[Role].docx` (gated) | **resume-tailor** (`extract_ats_keywords.py`, `verify_no_fabrication.py`) | application-tracker (records the tailored-resume filename) | tracker records apps without a tailored file |
| `CoverLetter_[Company]_[Role].md` (gated) | **cover-letter** (`draft_cover_letter.py`, `verify_no_fabrication.py`) | application-tracker (records the cover-letter filename) | cover-letter drafts from a pasted resume + posting if no workspace |
| `tracker.json` → HTML | **application-tracker** (`generate_tracker_html.py`, `draft_followup.py`) | outcome-learning (reads closed outcomes) | outcome-learning cold-start guard (needs ≥5 closed) |
| proposed LESSONS entries | **outcome-learning** (`harvest_outcomes.py`, `propose_lessons.py`) | the user (opt-in confirmation), future career-profile/job-search runs | no-op below the cold-start threshold |

## `postings.json` scored shape (produced by job-search/score_posting.py)

Each posting carries these sub-scores (1-5) plus a weighted global score and a
recommendation. Sub-score keys:

- `cv_match` — how well the posting fits the user's resume/profile (heaviest weight)
- `comp_vs_target` — compensation vs the user's target
- `cultural_signals` — culture/values fit signals
- `posting_legitimacy` — is it a real, active opening (ghost-job axis)
- `red_flags_penalty` — severity-graded penalty that can torpedo a high score

(See job-search's `references/match-quality-rubric.md` and
`posting-legitimacy-rubric.md` for the rubrics behind these.)

## `tracker.json` shape (produced by application-tracker/generate_tracker_html.py)

Per-application records carry: `company`, role, the sub-scores above,
`applied_date` (when the USER applied — distinct from `posted`, when the company
posted; the v5.1.1 fix), `cover_letter_file`, tailored-resume `files`, and a
status used for the active/applied filters. **Follow-up staleness reads ONLY
`applied_date`, never `posted`** (load-bearing — `draft_followup.py`'s
`test_scan_stale_does_NOT_fall_back_to_posted_field`).

## The anti-fabrication invariant (family-wide)

Any member that writes resume or profile **content** MUST route through
resume-tailor's `verify_no_fabrication.py` gate before producing a DOCX. The
gate never auto-approves; every new proper noun / number / section / bullet /
5+-word phrase run must be user-confirmed. Web content is untrusted even when
it is the user's own (gdkdigital.com, LinkedIn, etc.) — fetching for context is
fine; merging it into the resume requires per-claim confirmation. This is the
v5.2.0 fabrication-incident remediation and is non-negotiable across the family.
