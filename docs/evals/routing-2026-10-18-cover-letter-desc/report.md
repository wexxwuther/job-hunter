# job-hunter family routing evals (live claude -p)

- Model(s): claude-opus-4-8[1m]
- Queries: 86 (73 positive, 13 negative scored; 0 errored, not scored); completed: 86
- Positive strict: 71/73 (97%); lenient (orchestrator ok): 73/73 (100%)
- Negative (no family skill): 13/13 (100%)
- Cost (CLI-reported, completed calls only): $3.01; early-stopped at first skill call (cost not reported): 75

## Misses

| # | query | expected | routed | lenient | sources |
|---|---|---|---|---|---|
| 29 | Find me a job | job-search | job-hunter | yes | job-search#8:T |
| 31 | Are there any state government jobs in Texas I'd qualify for? | job-search | job-hunter | yes | job-search#10:T |

## Conflicts in eval expectations (query claimed by >1 member)

- Show me my application outcomes so far. -> outcome-learning, application-tracker

## Notes (manual, 2026-10-18)

- Run after cover-letter 1.2.0 (description change, `123bc51`) was deployed to the
  installs this runner loads (full user environment). Purpose: collisions from the wider
  "write, tailor, or change a cover letter ... add a claim, skill, or amount of experience"
  and "load it rather than answering from general knowledge" wording.
- cover-letter: 6/6 positives (42, 48-52) routed to cover-letter; no query outside
  cover-letter's own positives routed to it. resume-tailor: all 13 of its positives
  stayed on resume-tailor (no pull to cover-letter). Negatives: 13/13 routed to no family
  skill.
- 29, 31 (job-search queries routed to the orchestrator, lenient pass): same as the
  2026-10-12 and interview-prep 1.1.0 runs. 30 and 43, misses in the 1.1.0 run, passed
  here (sampling noise); 21 completed this time (was `error_max_turns`).
- Raw transcripts kept outside the repo (`E:\tmp\jh-cl3\routing\raw`).
