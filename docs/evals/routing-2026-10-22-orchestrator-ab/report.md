# Orchestrator description A/B for routing query 3 (2026-10-22)

Query: "Find me some backend roles and tailor my resume for the best one" (job-hunter/evals/trigger-evals.json id 3, expected job-hunter).

Question: did the 2026-10-22 trim of the job-hunter description (commit 0843528) move this query from job-hunter to job-search?

Answer: no. The description routes it to job-hunter in every hooks-off condition. The job-search samples in the 2026-10-22 routing run come from the owner's ts-judge UserPromptSubmit hook, which tools/run_routing_evals.py leaves on and which now says "Skill decision (follow it): load `job-search`" for this query. No description change.

## Variants

- A: current description (1019 chars, as deployed).
- B: pre-0843528 description plus "job-outreach (recruiter outreach, same gate)" (1058 chars; over the 1024 limit, so diagnostic only).

## 1. Model routing, hooks off (tools/run_trigger_probe.py, turn 1, 6 samples each)

| condition | skills listed | job-hunter | job-search | other |
|---|---|---|---|---|
| A_current_family | 22 | 6/6 | 0/6 | 0/6 |
| B_pretrim_plus_outreach_family | 22 | 6/6 | 0/6 | 0/6 |
| A_current_full_install | 320 | 6/6 | 0/6 | 0/6 |

Model: claude-opus-4-8[1m] in all 18 samples, 0 errored. Family env: --family-only from a clone of 449fc9c (B edited in its own clone). Full install: the deployed 02f66c7 skills, `--settings {"disableAllHooks": true}`.

## 2. ts-judge hook decision (E:/ts-judge select_skill, live, cache off)

| catalog variant | job-search | job-hunter |
|---|---|---|
| A current (372 families) | 13/13 | 0/13 |
| B job-hunter description swapped to pre-trim + outreach | 3/3 | 0/3 |
| C job-outreach removed (371 families) | 12/13 | 1/13 |

Why the trim cannot move this layer: stage 1 of the selector sees only the first clause of each description cut to 60 chars. For job-hunter that is "Routes a job-search task to the right specialists in the..." in both A and B. Stage 1 put career-profile (~0.78) and resume-tailor (~0.55) first; the third shortlist slot is job-search (~0.25), and job-hunter reached it once in 29 calls. Only the shortlist goes to stage 2, so job-hunter's full description is never read here.

## 3. The 2026-10-22 routing samples, re-read

Raw logs of the 4 samples (E:/tmp/jo-evals/routing*/raw/003.jsonl, not committed): 3 went to job-search and 2 of those say "loading the job-search skill as directed"; 1 went to job-hunter. ts-judge's injected context does not appear in the stream-json log, so the "as directed" wording plus the selector re-run above are the evidence (Inference, strong).

Not established: why earlier runs (10-12 to 10-20) got job-hunter with the hook on. ts-judge's code has not changed since 2026-10-08. A near-tie for the third shortlist slot on a catalog that keeps changing is the likely reason (Unknown).
