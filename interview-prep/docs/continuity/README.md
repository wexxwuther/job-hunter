# Continuity, interview-prep (job-hunter family member)

This skill is a member of the **job-hunter family**. The shared continuity stack lives at the
repo root in `docs/continuity/`. Read that first.

Member-specific notes:
- Added in v1.0.0 (2026-10-18) as the 8th family member. It was deferred in 2026-05 (v4, v5.1)
  for sibling-collision risk with generic interview skills; it is a separate member that reads
  the tracker archive, not a phase inside another skill.
- It reuses resume-tailor's `verify_no_fabrication.py` (bundled byte-identical, parity test).
- The pack format is the safety contract: every line the user would say is a `> ` blockquote,
  and `build_prep_pack.py claims` feeds exactly those lines to the gate.
- It never writes `tracker.json`; application-tracker owns it.
