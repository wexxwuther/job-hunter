# Outcomes: what actually happened

Record of the closed-loop outcome for every position you applied to. This is the supervisory signal that closes the loop, the agent compares its `recommendation` (apply / apply_if_specific_reason / skip) against actual outcomes here to surface meaningful patterns.

**Why this file exists:** the agent's scoring rubric is calibrated against general principles. Your actual outcomes are calibrated against *you*. With ≥5 closed-loop entries here, the agent can start surfacing patterns (subject to your confirmation) into `LESSONS.md`.

**Privacy:** This file lives only in your workspace. It is never sent off-machine, never committed to the public skill repository. Add `.job-hunter/` to your `.gitignore` if you keep your workspace in git.

**Format per entry:**

```
## <Company>, <Role>, <applied date>

**Posting URL:** <link>
**Agent recommendation at time of apply:** apply | apply_if_specific_reason | skip
**Score breakdown (if recorded):** cv_match=X.X, comp_vs_target=X.X, cultural_signals=X.X, posting_legitimacy=X.X, red_flags_penalty=X.X, weighted_global=X.X
**Outcome:** accepted_offer | rejected_offer | rejected_after_onsite | rejected_after_screen | rejected_at_resume | no_response_after_21d | withdrew | other
**Reason (yours or theirs):** Short free-text reason if known
**Lesson candidate?:** yes | no | not_yet, does this outcome suggest a pattern worth surfacing?
```

The simplest workflow: as `tracker.json` status moves past `applied`, the agent appends an entry here. You can also add entries directly.

**Cold-start guard:** until this file has 5 closed-loop entries, the agent will not propose any lessons. Pattern detection from <5 outcomes is guessing, not learning.

---

<!-- Closed-loop outcomes appended below this line -->
