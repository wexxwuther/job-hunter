# Lessons — patterns about your job-search preferences

Durable patterns the agent has noticed and **you have confirmed**. The agent never writes here without your sign-off. Each entry should describe a stable preference or behavior the agent should remember across all future sessions.

**Why this file exists:** so the agent can grade postings (especially `cultural_signals` and `red_flags_penalty`) in a way that reflects *your* track record, not just a generic rubric. Lessons here adjust how sub-scores are graded; they do NOT change the scoring weights themselves (those stay constant in `scripts/score_posting.py`).

**Privacy:** This file lives only in your workspace. It is never sent off-machine, never committed to the public skill repository. Add `.job-hunter/` to your `.gitignore` if you keep your workspace in git.

**Format per entry:**

```
## YYYY-MM-DD — Short imperative pattern

**Pattern:** The durable behavior, written in plain language ("user consistently rejects X")
**Evidence:** Which OUTCOMES.md or DECISIONS.md entries support this (N of M cases)
**How it shapes scoring:** Which sub-score(s) this lesson should influence (cv_match, comp_vs_target, cultural_signals, posting_legitimacy, red_flags_penalty) and in which direction
```

**Cold-start guard:** the agent will not propose any lesson until you have at least 5 closed-loop outcomes in `OUTCOMES.md`. Patterns from thin data are guesses, not lessons.

**Edit freely.** If a lesson stops being true, edit it or delete it. The agent re-reads this file on every session.

---

<!-- Confirmed lessons appended below this line -->
