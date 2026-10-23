# Changelog - job-outreach

## v1.0.1 (2026-10-22)

- Description only: the do-not-use clause names thank-you notes after an interview, which stay
  with application-tracker. Live routing had sent one such query here.

## v1.0.0 (2026-10-22)

- New member: recruiter, hiring-manager, and contact outreach (email, LinkedIn connection notes and
  DMs, replies, follow-ups to those contacts) in the user's own voice. It drafts; the user sends.
- Reads the contact's history before drafting (tracker, contact records, communications log), so it
  never repeats an ask, re-introduces the user, or requests a LinkedIn connection that exists.
- `scripts/check_voice.py`: deterministic voice checker. Rules come from the user's own
  `voice/rules.json`; rule types `chars`, `phrases`, `regex`, `opening`, `max_count`; per-channel
  levels; an allowlist for approved sentences; LinkedIn and subject-line length limits. Exit 0 pass,
  1 failing finding, 2 usage or rules error. Never edits the draft.
- The rules loader rejects a JSON backspace inside a regex (a single `\b` in JSON), which would
  otherwise compile and silently never match.
- `references/rules-starter.json`: a person-neutral starting rules file.
- Bundles `verify_no_fabrication.py` byte-identical from resume-tailor, and the family workspace
  contract.
