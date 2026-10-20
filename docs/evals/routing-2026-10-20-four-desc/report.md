# job-hunter family routing evals (live claude -p)

- Model(s): claude-opus-4-8[1m]
- Queries: 86 (73 positive, 13 negative scored; 0 errored, not scored); completed: 85
- Positive strict: 66/73 (90%); lenient (orchestrator ok): 70/73 (96%)
- Negative (no family skill): 13/13 (100%)
- Cost (CLI-reported, completed calls only): $3.26; early-stopped at first skill call (cost not reported): 73

## Misses

| # | query | expected | routed | lenient | sources |
|---|---|---|---|---|---|
| 5 | I'm starting a job hunt and want to do it properly end to end | job-hunter | (none) | NO | job-hunter#5:T |
| 14 | Let me tell you about myself and what kind of role I actually want before we search | career-profile | (none) | NO | career-profile#2:T |
| 16 | Extract the text from my resume PDF so we can use it | career-profile | pdf | NO | career-profile#4:T |
| 23 | What jobs match my resume? | job-search | job-hunter | yes | job-search#2:T |
| 29 | Find me a job | job-search | job-hunter | yes | job-search#8:T |
| 30 | Help me find work as a freelance graphic designer in NYC | job-search | job-hunter | yes | job-search#9:T |
| 31 | Are there any state government jobs in Texas I'd qualify for? | job-search | job-hunter | yes | job-search#10:T |

## Conflicts in eval expectations (query claimed by >1 member)

- Show me my application outcomes so far. -> outcome-learning, application-tracker

## Notes (manual, 2026-10-20)

- Run after `63640df` (interview-prep 1.2.0, career-profile 1.2.0, job-search 1.1.0,
  outcome-learning 1.1.0) was deployed to the installs this runner loads. This runner does
  NOT disable user hooks, so the owner's ts-judge UserPromptSubmit hook is active (as in the
  earlier routing runs).
- Negatives 13/13. Misses 29-31 match earlier runs.
- New misses resampled 3x with `--ids 5,14,16,23` (`results-resample-s*.json`), totals incl.
  the main run: 5 (job-hunter -> none) 1/4 miss = noise; 14 "Let me tell you about myself ..."
  (career-profile -> none, a direct conversational answer) 2/4 miss; 16 "Extract the text
  from my resume PDF so we can use it" (career-profile -> document-skills:pdf) 3/4 miss;
  23 "What jobs match my resume?" (job-search -> job-hunter, lenient) 2/4 miss.
- 16 with user hooks disabled (Skill-only, full install, 3x; `q16-hooks-off/`):
  career-profile 3/3. The pdf pull needs the ts-judge hook; the model said "I'll load the PDF
  skill as directed". career-profile 1.2.0 dropped the phrase "extract text from" (1.1.0 had
  "read, parse, or extract text from their resume file"); that may be what moved ts-judge.
- Raw transcripts outside the repo (`E:\tmp\jh-joint\routing-after\`, `routing-resample-s*`,
  `q16\`).
