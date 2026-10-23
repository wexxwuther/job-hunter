# job-hunter family routing evals (live claude -p)

- Model(s): claude-opus-4-8[1m]
- Queries: 100 (85 positive, 14 negative scored; 1 errored, not scored); completed: 99
- Positive strict: 79/85 (93%); lenient (orchestrator ok): 82/85 (96%)
- Negative (no family skill): 14/14 (100%)
- Cost (CLI-reported, completed calls only): $4.12; early-stopped at first skill call (cost not reported): 87

## Misses

| # | query | expected | routed | lenient | sources |
|---|---|---|---|---|---|
| 3 | Find me some backend roles and tailor my resume for the best one | job-hunter | job-search | NO | job-hunter#3:T |
| 16 | Extract the text from my resume PDF so we can use it | career-profile | pdf | NO | career-profile#4:T |
| 29 | Find me a job | job-search | job-hunter | yes | job-search#8:T |
| 30 | Help me find work as a freelance graphic designer in NYC | job-search | job-hunter | yes | job-search#9:T |
| 68 | Reset what the job hunter has learned about my job-search preferences. | outcome-learning | job-hunter | yes | outcome-learning#5:T |
| 96 | Write a thank-you note to the panel I interviewed with yesterday | application-tracker | job-outreach | NO | job-outreach#10:F |

## Errored (CLI error result; excluded from all scores)

| # | query | error |
|---|---|---|
| 91 | Caitlin hasn't answered my email from last week, write her a short follow-up | error_max_turns |

## Conflicts in eval expectations (query claimed by >1 member)

- Show me my application outcomes so far. -> outcome-learning, application-tracker
