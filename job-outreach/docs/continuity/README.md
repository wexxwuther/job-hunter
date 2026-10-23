# Continuity, job-outreach (job-hunter family member)

This skill is a member of the **job-hunter family**. The shared continuity stack is the repo-root
`docs/continuity/` (https://github.com/wexxwuther/job-hunter/tree/main/docs/continuity). Read that
first.

Member-specific notes:
- Added in v1.0.0 (2026-10-22) as the 9th skill (8th member). Built from a real owner's job search,
  where agent-drafted recruiter messages repeated an ask, framed the owner in a role he was moving
  away from, and drafted a LinkedIn connection note to someone he was already connected to.
- The voice checker is person-neutral. Every rule lives in the USER'S `voice/rules.json`; the skill
  ships only `references/rules-starter.json`, and a test keeps that starter free of personal data.
- It reuses resume-tailor's `verify_no_fabrication.py` (bundled byte-identical; a test enforces it).
- Ownership: application check-in timing and thank-you notes stay with application-tracker; messages
  to recruiters, hiring managers and contacts (including follow-ups to them) and voice checks of any
  draft belong here.
