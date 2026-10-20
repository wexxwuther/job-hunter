# job-search natural-trigger probe (live claude -p)

- Environment: full install (every user skill, plugin and MCP); user hooks disabled; normal tool set
- Model(s): claude-opus-4-8[1m]; skills listed: 319
- Turn 1 only, 3 sample(s) per case, stopped at the first Skill call
- Expected skill loaded: 4/6 scored samples (0 errored, not scored)
- Cost (CLI-reported floor; calls stopped at a Skill call report none): $0.00

| # | turn 1 | expected loaded | other skill | answered | capped | errored |
|---|---|---|---|---|---|---|
| 1 | Find me senior backend engineer roles in Austin, $180k+. Here's my res... | 1/3 | job-hunter, job-hunter | 0 | 0 | 0 |
| 6 | I found this posting on LinkedIn, it has no apply button visible, no s... | 3/3 | - | 0 | 0 | 0 |
