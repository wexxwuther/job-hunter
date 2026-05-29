# Continuity, cover-letter (job-hunter family member)

This skill is a member of the **job-hunter family**. The shared continuity stack lives in the
orchestrator at `job-hunter/docs/continuity/`. Read that first.

Member-specific notes:
- Added in v1.0.0 (2026-05-29) as the 7th family member, closing a real gap (the family had
  no cover-letter capability).
- It reuses resume-tailor's `verify_no_fabrication.py` (bundled byte-identical) rather than
  forking a second safety check. A test asserts the bundled copy stays byte-identical so the
  two cannot drift.
- Drafting (`draft_cover_letter.py`) is deterministic and fact-grounded: it fills factual slots
  only from supplied source facts and emits `[CONFIRM: ...]` for anything ungrounded — it never
  invents a value. Persuasive/connective prose is allowed; new facts are not.
