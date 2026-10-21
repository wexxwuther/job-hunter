# Changelog - interview-prep

## v1.2.2 (2026-10-20)

- Gate fix (bundled copy, re-synced byte-identical from resume-tailor 1.1.5): verify_no_fabrication.py: a capital letter inside a word was read as the start of a new proper noun, so `iOS` gave `OS` and `vCard` gave `Card`: fragments the source never has, flagged as new (found finalizing the owner's resume, 2026-10-20). Candidates are now whole words: a lowercase-first word with an inner capital (iOS, vCard, eBay, iPhone) is checked as a whole and is never skipped as a sentence start; its hyphen parts are still checked one by one, so "non-GAAP" still gives "GAAP" and "mid-May" stays quiet.

## v1.2.1 (2026-10-20)

- Gate fix (bundled copy, re-synced byte-identical from resume-tailor 1.1.4): verify_no_fabrication.py, DOCX-shaped text (python-docx paragraph text has no bullet markers, and headings are plain Title Case lines in Normal style). (1) A new Title Case heading (`Earlier Experience`) was not reported: only markdown and ALL CAPS headings were. A short Title Case line (1-5 words, optional colon) with a resume-section word (Experience, Education, Skills, ...) now counts as a heading, and is new only if no source line has the same text in any case. Job-title, employer and skill lines are not headings; a heading with no section word is still missed. (2) `new_bullets` counted only lines that start with a marker, so a new markerless bullet was never counted. When either document has no markers, every non-blank line under a heading now counts in both; lines before the first heading do not, so a headingless letter or claims list stays quiet. Found by the owner's resume reassessment (2026-10-20).

## v1.2.0 (2026-10-20)

- Description only (owner-approved 2026-10-20). Signal: after cover-letter 1.2.0, the "make me sound like I know Looker" interview ask loaded interview-prep 0/12 in a family-only install (3/3 before); reverting only cover-letter restored it to 11/12. The description now claims the ask to sound experienced in a skill the user lacks in an interview, and says to load the skill rather than answer or refuse from general knowledge. Draft probe: case 2 12/12; joint sweep 18/18 (+3/3 more on cases 2, 3). Evidence: docs/evals/trigger-2026-10-18-interview-prep-case2/.
- Joint family-only sweep with all four 2026-10-20 description changes applied together: all 40 outcome-eval turn-1 cases x3 match the earlier per-member probes except job-search case 1 (7/9, the 2 misses routed to the job-hunter orchestrator; 9/9 before).

## v1.1.2 (2026-10-19)

- Gate fix (bundled copy, re-synced byte-identical from resume-tailor): verify_no_fabrication.py: a new word that starts a bare line was never a proper-noun candidate, because any word after a line break was skipped as a sentence start. So a new tool added as its own line in a one-per-line list (`SKILLS` / `Budgeting` / `Scheduling` / `Salesforce`) gave verdict `clean`. A word that starts a line, the first line included, is now a candidate unless the text before it ends with . ! or ?; it flags only if the source has it nowhere, in any case, so a truthful reformat stays quiet. Bullet lines and mid-line words were already caught. Pre-existing gap, found while verifying the 26d7738 fix.

## v1.1.1 (2026-10-19)

- Gate fix (bundled copy, re-synced byte-identical from resume-tailor): verify_no_fabrication.py: two kinds of reformat noise. (1) A word already in the source was flagged as a new proper noun when a reformat moved it mid-line or capitalized it (one-per-line competencies joined with " | ": Budgeting, Sales, Team). Proposed proper nouns are now compared case-insensitively against every word of the source, wherever it sits. (2) A unit letter (k, M, b) took the first letter of the next word, even across a line break ("20 Mechanics" -> "20 M"), so a rewrapped line changed the token and an old number was flagged as new; the context snippet then came from the first substring match, so "20" showed the context of "200+". Units now count only when no letter follows, and context is taken from a whole-token match. "200+" was already one token. New tools, employers and numbers still flag. Found by the owner's Mode A run (2026-10-19).

## v1.1.0 (2026-10-18)

- Description only (owner-approved). Signal: with the normal tool set and no user hooks, three in-domain prompts ("make me sound like I have [a tool]", "Research Globex before my interview", "Mock interview me for the behavioral panel") loaded the skill in 1 of 9 samples, in both a full install and a family-only install, and the base model scripted unverified experience for the user. The description now names company research, practice answers, mock interviews and sounding experienced in a skill the user lacks, and says to load the skill rather than answer from general knowledge. Probe with the new text: 9/9 (controls 3/3). Do-not-use clauses unchanged. See `docs/evals/trigger-2026-10-18-interview-prep/`.

## v1.0.1 (2026-10-18)

- Gate fix (bundled copy, re-synced byte-identical from resume-tailor): verify_no_fabrication.py: a comma right after a number ("In 2023, four new") was kept as part of the token, so a number or year already in the source was flagged as new ("2023,", "40,"). Trailing commas are now stripped; inner commas ("1,200") are kept and truly new numbers are still flagged. Found by the first live outcome-eval run of interview-prep (2026-10-18).

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
