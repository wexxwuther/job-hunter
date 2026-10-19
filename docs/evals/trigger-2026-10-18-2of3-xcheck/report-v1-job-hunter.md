# job-hunter natural-trigger probe (live claude -p)

- Environment: family-only (--setting-sources project; only the 8 members plus Claude Code's bundled skills); user hooks disabled; normal tool set
- Model(s): claude-opus-4-8[1m]; skills listed: 21
- Turn 1 only, 3 sample(s) per case, stopped at the first Skill call
- Expected skill loaded: 5/15 scored samples (0 errored, not scored)
- Cost (CLI-reported floor; calls stopped at a Skill call report none): $0.00

| # | turn 1 | expected loaded | other skill | answered | capped | errored |
|---|---|---|---|---|---|---|
| 1 | Tailor my resume for this Senior Backend Engineer role at Stripe. The ... | 0/3 | resume-tailor, resume-tailor, resume-tailor | 0 | 0 | 0 |
| 2 | Find me data-engineer jobs and tailor my resume for the top match. My ... | 2/3 | job-search | 0 | 0 | 0 |
| 3 | Where am I on my applications, and draft a follow-up for anything stal... | 0/3 | application-tracker, application-tracker, application-tracker | 0 | 0 | 0 |
| 4 | I'm starting my job search today - set me up and find some roles. | 3/3 | - | 0 | 0 | 0 |
| 5 | What's working in my job search? Learn from my outcomes. | 0/3 | outcome-learning, outcome-learning, outcome-learning | 0 | 0 | 0 |
