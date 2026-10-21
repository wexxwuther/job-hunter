# Changelog - resume-tailor

## v1.1.6 (2026-10-20)

- Gate fix (canonical copy): verify_no_fabrication.py: on Windows a pipe uses the console code page (cp1252), so the printed JSON report came out in cp1252 (an em dash as byte 0x97, which a UTF-8 reader rejects; a check mark crashed the script with UnicodeEncodeError), and `--original-stdin` / `--proposed-stdin` read UTF-8 input as cp1252 mojibake. Stdin is now read as UTF-8 bytes, like the files; the printed JSON is pure ASCII (\u escapes, restored by any JSON parser); the `--out` file stays UTF-8 with the real characters. 4 regression tests in `tests/test_verify_no_fabrication.py`.

## v1.1.5 (2026-10-20)

- Gate fix (canonical copy): verify_no_fabrication.py: a capital letter inside a word was read as the start of a new proper noun, so `iOS` gave `OS` and `vCard` gave `Card`: fragments the source never has, flagged as new (found finalizing the owner's resume, 2026-10-20). Candidates are now whole words: a lowercase-first word with an inner capital (iOS, vCard, eBay, iPhone) is checked as a whole and is never skipped as a sentence start; its hyphen parts are still checked one by one, so "non-GAAP" still gives "GAAP" and "mid-May" stays quiet. 7 regression tests in `tests/test_verify_no_fabrication.py` (invented fixtures).

## v1.1.4 (2026-10-20)

- Gate fix (canonical copy): verify_no_fabrication.py, DOCX-shaped text (python-docx paragraph text has no bullet markers, and headings are plain Title Case lines in Normal style). (1) A new Title Case heading (`Earlier Experience`) was not reported: only markdown and ALL CAPS headings were. A short Title Case line (1-5 words, optional colon) with a resume-section word (Experience, Education, Skills, ...) now counts as a heading, and is new only if no source line has the same text in any case. Job-title, employer and skill lines are not headings; a heading with no section word is still missed. (2) `new_bullets` counted only lines that start with a marker, so a new markerless bullet was never counted. When either document has no markers, every non-blank line under a heading now counts in both; lines before the first heading do not, so a headingless letter or claims list stays quiet. Found by the owner's resume reassessment (2026-10-20). That run used the installed 1.1.1 copy; its other two findings (line-start proper nouns flagged after a reformat, `20` shown with the context of `200+`) were already fixed in 1.1.2 but not deployed. 13 regression tests in `tests/test_verify_no_fabrication.py` (invented DOCX-shaped fixture).

## v1.1.3 (2026-10-19)

- Gate fix (canonical copy): verify_no_fabrication.py: a new word that starts a bare line was never a proper-noun candidate, because any word after a line break was skipped as a sentence start. So a new tool added as its own line in a one-per-line list (`SKILLS` / `Budgeting` / `Scheduling` / `Salesforce`) gave verdict `clean`. A word that starts a line, the first line included, is now a candidate unless the text before it ends with . ! or ?; it flags only if the source has it nowhere, in any case, so a truthful reformat stays quiet. Bullet lines and mid-line words were already caught. Pre-existing gap, found while verifying the 26d7738 fix. Regression tests in `tests/test_verify_no_fabrication.py` (invented fixtures).

## v1.1.2 (2026-10-19)

- Gate fix (canonical copy): verify_no_fabrication.py: two kinds of reformat noise. (1) A word already in the source was flagged as a new proper noun when a reformat moved it mid-line or capitalized it (one-per-line competencies joined with " | ": Budgeting, Sales, Team). Proposed proper nouns are now compared case-insensitively against every word of the source, wherever it sits. (2) A unit letter (k, M, b) took the first letter of the next word, even across a line break ("20 Mechanics" -> "20 M"), so a rewrapped line changed the token and an old number was flagged as new; the context snippet then came from the first substring match, so "20" showed the context of "200+". Units now count only when no letter follows, and context is taken from a whole-token match. "200+" was already one token. New tools, employers and numbers still flag. Found by the owner's Mode A run (2026-10-19). Regression tests in `tests/test_verify_no_fabrication.py` (synthetic fixture).

## v1.1.1 (2026-10-18)

- Gate fix (canonical copy): verify_no_fabrication.py: a comma right after a number ("In 2023, four new") was kept as part of the token, so a number or year already in the source was flagged as new ("2023,", "40,"). Trailing commas are now stripped; inner commas ("1,200") are kept and truly new numbers are still flagged. Found by the first live outcome-eval run of interview-prep (2026-10-18). Regression tests in `tests/test_verify_no_fabrication.py`.

## v1.1.0 (2026-10-18)

Fresh-context drafter-reviewer pass for Mode B (new step 5), adapted from the reviewer agent
in MadsLorentzen/ai-job-search (idea only; no code taken):

- `scripts/review_pass.py packet` builds the reviewer prompt from the source facts, the
  posting and the draft. Each block gets a random per-packet marker, and the posting is
  marked untrusted.
- A subagent with no other context returns JSON findings. On harnesses without subagents
  the review runs as a separate same-context step, and the user is told it is weaker.
- `scripts/review_pass.py check` validates the reply. A quote counts only where it really
  appears: `location` in the draft, `source_evidence` in the source (never the posting or
  the draft), `posting_evidence` in the posting. Every unaddressed requirement goes to the
  user, even with a related source quote. Employer claims must be verified or removed.
- Advisory only. `verify_no_fabrication.py` stays mandatory and runs last, on the revised
  draft. At most two rounds.
- First live trial: the reviewer quoted "2021-2024" for a "5+ years" requirement, and
  "built SQL reports" for "advanced SQL". That is why `missed_requirement` always asks the
  user. Regression test added.
- 26 new tests (7 load-bearing), mutation-checked (9/9 mutants killed).

## v1.0.0 (2026-05-28)

Established as the **resume-tailor** member of the job-hunter family (v6.0.0 split of
the former job-hunter monolith). This member owns its phase's scripts + evals
and is routed by the `job-hunter` orchestrator; it also works standalone.
Reads/writes the shared `.job-hunter/` workspace per
`job-hunter/references/workspace-contract.md` and degrades gracefully when
run alone. See the family continuity stack at `job-hunter/docs/continuity/`.
