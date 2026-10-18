# interview-prep routing check, 2026-10-18 (PROXY, not a live harness run)

## What was attempted first

`tools/run_routing_evals.py --ids 62,63,73-86` against the real `claude -p` CLI after the
8-skill family was installed. Every call returned `"result": "Not logged in - Please run
/login"` (`is_error: true`, cost 0), so that run measured nothing. The runner scored those
error results as "routed to (none)" instead of failing them; that is a runner bug (see
`docs/continuity/open-questions.md`). The live run is still to do once the CLI is logged in.

## Proxy method

A fresh Sonnet subagent (no other context, no tools besides reading two files) was given:

- the exact frontmatter descriptions of all 8 family skills, read from the SKILL.md files at
  commit `c01d73c`;
- 9 likely competitors shown by name only, the way they appear in the real skill listing
  (`human-resources:interview-prep`, `human-resources:recruiting-pipeline`,
  `human-resources:draft-offer`, `sales:call-prep`, `common-room:call-prep`,
  `legal:meeting-briefing`, `anthropic-skills:job-hunter`, `document-skills:docx`,
  `brainstorming`) plus a "(none)" option;
- 18 shuffled queries: all 16 interview-prep trigger evals plus application-tracker's two
  interview-adjacent evals (#6 thank-you note, #7 mark as interviewing).

It picked one skill per query, judging each on its own.

## Result

18/18 as expected (`results.json`):

- 7/7 candidate-prep queries -> interview-prep.
- Hiring-side queries (2) -> `human-resources:interview-prep`, not ours.
- Thank-you notes and status changes (4) -> application-tracker.
- Podcast, salary negotiation, kitchen contractors, banana bread -> no skill.
- The resume control -> resume-tailor.

For comparison, the builder's keyword mock runner scored 14/16 (it ignores do-not-use
clauses and fired on the thank-you and podcast negatives).

## Limits

One sample per query; a model reading 18 options is not the real environment with ~300
skills and the full system prompt; competitors had no descriptions. Treat this as a sanity
check of the description wording, not a measured trigger rate.
