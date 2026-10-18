# job-search natural-trigger probe (live claude -p)

- Environment: family-only (--setting-sources project; only the 8 members plus Claude Code's bundled skills); user hooks disabled; normal tool set
- Model(s): claude-opus-4-8[1m]; skills listed: 21
- Turn 1 only, 3 sample(s) per case, stopped at the first Skill call
- Expected skill loaded: 20/24 scored samples (0 errored, not scored)
- Cost (CLI-reported floor; calls stopped at a Skill call report none): $0.21

| # | turn 1 | expected loaded | other skill | answered | capped | errored |
|---|---|---|---|---|---|---|
| 1 | Find me senior backend engineer roles in Austin, $180k+. Here's my res... | 3/3 | - | 0 | 0 | 0 |
| 2 | Find me a job | 0/3 | job-hunter, job-hunter, job-hunter | 0 | 0 | 0 |
| 3 | My search came back with only these three (postings.json): one stale p... | 3/3 | - | 0 | 0 | 0 |
| 4 | Search for product manager jobs in Denver. My salary target is $250k. | 3/3 | - | 0 | 0 | 0 |
| 5 | The same job appears on LinkedIn, Indeed, and the company's careers pa... | 3/3 | - | 0 | 0 | 0 |
| 6 | I found this posting on LinkedIn, it has no apply button visible, no s... | 2/3 | - | 1 | 0 | 0 |
| 7 | Score this posting: I'm a senior backend engineer with 8 YOE in Python... | 3/3 | - | 0 | 0 | 0 |
| 8 | I'm a registered nurse in Ohio looking for travel-nurse contracts, $80... | 3/3 | - | 0 | 0 | 0 |
