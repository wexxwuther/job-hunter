# Joint natural-trigger sweep: four approved descriptions together (2026-10-20)

The owner approved four description drafts on 2026-10-20: interview-prep draft v1
(`trigger-2026-10-18-interview-prep-case2/`), career-profile draft v2
(`...-career-profile-case3/`), job-search draft v1 (`...-job-search-case6/`) and
outcome-learning draft v1 (`...-outcome-learning-case3/`). Each had been probed alone. The
cover-letter 1.2.0 regression (it stopped interview-prep loading on its case 2) showed that one
member's description can move another's routing, so all four were swept together before
shipping.

## Method

- A clone of `5f93a00` with all four blocks applied (`apply_drafts.py` logic: replace the
  frontmatter `description:` entry, YAML must read back the draft text exactly). The
  four SKILL.md files later committed are byte-identical to the swept clone.
- `tools/run_trigger_probe.py --family-only --samples 3` from the clone, for all 8 members'
  scenario files (40 cases, 120 samples), then 3 more samples on each target case and 6 more on
  job-search case 1.
- Model claude-opus-4-8[1m]; turn 1 only; stopped at the first Skill call. Every call loaded a
  skill, so no CLI cost was reported.

## Results (expected skill loaded / samples)

| member | joint sweep | per-member probe before (committed descriptions) |
|---|---|---|
| interview-prep | 18/18 (+ cases 2, 3: 3/3 each) | case 2 0/12 (after cover-letter 1.2.0), case 3 6/9 |
| career-profile | case 3 3/3 (+3/3); cases 1-2 route to job-hunter 6/6 | case 3 6/9; cases 1-2 to job-hunter |
| job-search | 20/24; case 6 3/3 (+3/3); case 2 to job-hunter 3/3; case 1 2/3 (+5/6 = 7/9) | case 6 7/9; case 2 to job-hunter; case 1 9/9 |
| outcome-learning | 15/15 (+ case 3: 3/3) | case 3 5/9 |
| cover-letter | 12/12 | (1.2.0) 12/12 incl. the fabrication case |
| resume-tailor | 15/18; case 5 (a cover-letter ask) to cover-letter 3/3 | same |
| application-tracker | 9/9 | 9/9 |
| job-hunter | 6/15; cases 1, 3, 5 go to the member directly | same |

- All five target cases: 6/6.
- The only change from the per-member baselines: job-search case 1 ("Find me senior backend
  engineer roles in Austin, $180k+. Here's my resume ...") 7/9, both misses to the job-hunter
  orchestrator (lenient pass; it routes on to job-search). With career-profile v2 alone the
  earlier cross-check saw 5/6 (job-hunter 1); committed descriptions 9/9. Recorded, not blocking.
- The job-hunter / resume-tailor / career-profile 1-2 / job-search 2 "misses" are the known
  eval-expectation mismatches (open question "Outcome evals that expect a different first skill
  than the descriptions route to"), unchanged.

## Files

`report-<member>.md` / `results-<member>.json` (40-case sweep);
`report-extra-<member>-<ids>.md` / `results-extra-...json` (extra samples). Raw transcripts and
the clone: outside the repo (`E:\tmp\jh-joint\`).
