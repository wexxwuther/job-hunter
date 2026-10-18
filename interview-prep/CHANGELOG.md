# Changelog - interview-prep

## v1.0.0 (2026-10-18)

Initial release, the 8th member of the job-hunter family. The idea comes from the
`/interview` command in MadsLorentzen/ai-job-search (reviewed 2026-10-18, not
adopted); the build follows this family's anti-fabrication rules.

- `load_application.py`: picks one tracked application (company and role match, or
  index), reads the resume and cover letter that were submitted for it (.md, .txt,
  .docx via stdlib, .pdf via optional pypdf), the posting text, and only the
  confirmed entries of `.job-hunter/LESSONS.md`. Lists URLs inside the posting so the
  agent does not open them. Reads only; never writes `tracker.json`.
- `build_prep_pack.py`: stage-specific prep pack for 6 stages (recruiter screen,
  hiring manager, skills, behavioral panel, case or presentation, final). Maps posting
  requirements to the user's real lines, STAR scaffolds with `[CONFIRM: ...]` slots,
  gap bridges that never claim the missing experience, questions to ask, research
  screened for source (posting URLs rejected, unsourced notes marked unverified,
  personal details about interviewers rejected). Every answer line is a blockquote;
  `claims` extracts them for the gate and exits 3 while slots are open. `questions`
  gives the mock-interview order.
- Bundles `verify_no_fabrication.py` byte-identical to resume-tailor's (parity test).
- References: `interview-stages.md`, `mock-interview.md`, and the family
  `workspace-contract.md`.
- Live trial before release (real subagent, fictional workspace, a posting with an
  injected "pay a $200 fee" instruction): the injection was ignored, the posting URL was
  not opened, the Looker gap stayed an honest bridge. Fixed from what it found: a
  "5+ years" requirement was keyword-matched to an unrelated resume line (time
  requirements are now never matched; one shared word is no longer a match); rebuilding
  the gate's source meant re-running `build`, which overwrote the filled pack (new
  `source` subcommand; `build` refuses to overwrite without `--force`); posting URLs
  kept a trailing period; gap requirements showed up in questions to ask. SKILL.md now
  says how to drop unanswerable STAR slots, how to decline "make me sound experienced",
  that the gate exits 0 and `summary.verdict` is what counts, and what to do about
  instructions or fee requests inside a posting.
