# job-hunter family routing evals (live claude -p)

- Model(s): claude-opus-4-8[1m]
- Queries: 86 (72 positive, 13 negative scored; 1 errored, not scored); completed: 85
- Positive strict: 68/72 (94%); lenient (orchestrator ok): 71/72 (99%)
- Negative (no family skill): 13/13 (100%)
- Cost (CLI-reported, completed calls only): $3.68; early-stopped at first skill call (cost not reported): 74

## Misses

| # | query | expected | routed | lenient | sources |
|---|---|---|---|---|---|
| 29 | Find me a job | job-search | job-hunter | yes | job-search#8:T |
| 30 | Help me find work as a freelance graphic designer in NYC | job-search | job-hunter | yes | job-search#9:T |
| 31 | Are there any state government jobs in Texas I'd qualify for? | job-search | job-hunter | yes | job-search#10:T |
| 43 | Help me with my resume | resume-tailor | career-profile | NO | resume-tailor#8:T |

## Errored (CLI error result; excluded from all scores)

| # | query | error |
|---|---|---|
| 21 | Review my resume and tell me what's wrong with it | error_max_turns |

## Conflicts in eval expectations (query claimed by >1 member)

- Show me my application outcomes so far. -> outcome-learning, application-tracker

## Notes (manual, 2026-10-18)

- Run after interview-prep 1.1.0 (description change, `854e29b`) was deployed to the
  installs this runner loads. Purpose: collisions from the stronger "load it rather than
  answering from general knowledge" wording.
- interview-prep: 11/11 positives routed to interview-prep; 13/13 negatives (hiring side,
  podcast, salary, contractor interviews, ...) routed to no family skill.
- 29-31 (job-search queries routed to the orchestrator, lenient pass): same as the
  2026-10-12 run.
- 43 "Help me with my resume" -> career-profile (strict and lenient miss). Resampled 3x
  with `--ids 43`: job-hunter, resume-tailor, resume-tailor. Ambiguous query, sampling
  noise; not related to interview-prep.
- 21 errored (`error_max_turns`, allow_none query) on the run and on one retry; it hit the
  same result subtype on 2026-10-12, when the runner still scored it.
- Raw transcripts kept outside the repo (`E:\tmp\jh-interview\routing-desc-2026-10-18\raw`).
