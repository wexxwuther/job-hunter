# job-hunter family routing evals (live claude -p)

- Model(s): claude-opus-4-8[1m]
- Queries: 72 (64 positive, 8 negative); completed: 72
- Positive strict: 55/64 (86%); lenient (orchestrator ok): 59/64 (92%)
- Negative (no family skill): 8/8 (100%)
- Cost (CLI-reported, completed calls only): $7.23; early-stopped at first skill call (cost not reported): 60

## Misses

| # | query | expected | routed | lenient | sources |
|---|---|---|---|---|---|
| 8 | Restore my job-hunter workspace on this machine | job-hunter | (none) | NO | job-hunter#8:T |
| 15 | Here's my resume DOCX - can you read it and pull out my experience? | career-profile | docx | NO | career-profile#3:T |
| 16 | Extract the text from my resume PDF so we can use it | career-profile | pdf | NO | career-profile#4:T |
| 29 | Find me a job | job-search | job-hunter | yes | job-search#8:T |
| 30 | Help me find work as a freelance graphic designer in NYC | job-search | job-hunter | yes | job-search#9:T |
| 31 | Are there any state government jobs in Texas I'd qualify for? | job-search | job-hunter | yes | job-search#10:T |
| 43 | Help me with my resume | resume-tailor | job-hunter | yes | resume-tailor#8:T |
| 67 | Show me my application outcomes so far. | outcome-learning | application-tracker | NO | outcome-learning#4:T |
| 68 | Reset what you know about my preferences. | outcome-learning | (none) | NO | outcome-learning#5:T |

## Conflicts in eval expectations (query claimed by >1 member)

