# Changelog - career-profile

## v1.2.0 (2026-10-20)

- Description only (owner-approved 2026-10-20). Signal: "Read [my resume] and pull out the key facts" loaded career-profile 6/9 in a family-only install; misses read the file directly and saved no profile. Draft v2 (v1 collided with job-search case 1): case 3 6/6; joint sweep 3/3 (+3/3); cases 1-2 still route to job-hunter as before. Evidence: docs/evals/trigger-2026-10-18-career-profile-case3/.
- Joint family-only sweep with all four 2026-10-20 description changes applied together: all 40 outcome-eval turn-1 cases x3 match the earlier per-member probes except job-search case 1 (7/9, the 2 misses routed to the job-hunter orchestrator; 9/9 before).

## v1.1.0 (2026-10-13)

`parse_resume.py` fixes found by testing on Word-authored DOCX/PDF resumes:

- DOCX: page headers/footers and text boxes are now read (contact details there were dropped).
- DOCX: body is read in document order, tables included (tables used to be appended at the
  end, filing an experience table under CERTIFICATIONS).
- DOCX: horizontally merged table cells are read once (were repeated per grid column);
  layout-table cells keep each paragraph on its own line so headings are detected.
- Any format: empty extraction is now an error (exit 2) telling the agent to ask the user
  for a DOCX/TXT/pasted copy, instead of silently returning empty text (scanned PDFs).
- SKILL.md usage now shows `uv run`; plain `python` needs python-docx/pypdf installed.
- tests/test_parse_resume.py + tests/fixtures/resumes/ (fictional resume, Word-authored).

## v1.0.0 (2026-05-28)

Established as the **profile-intake** member of the job-hunter family (v6.0.0 split of
the former job-hunter monolith). This member owns its phase's scripts + evals
and is routed by the `job-hunter` orchestrator; it also works standalone.
Reads/writes the shared `.job-hunter/` workspace per
`job-hunter/references/workspace-contract.md` and degrades gracefully when
run alone. See the family continuity stack at `job-hunter/docs/continuity/`.
