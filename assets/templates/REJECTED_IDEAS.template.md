# Rejected Ideas — hard constraints

Things you have explicitly told the agent NOT to do again. Treat these as **hard filters**, not soft preferences. The agent reads this file at the start of every session and applies these constraints before searching, scoring, or tailoring.

**Why this file exists:** the agent should never re-litigate a settled "no." If you said "no government contractors" once, you shouldn't have to say it every session. This file makes that commitment durable.

**Privacy:** This file lives only in your workspace. It is never sent off-machine, never committed to the public skill repository. Add `.job-hunter/` to your `.gitignore` if you keep your workspace in git.

**Format per entry:**

```
## YYYY-MM-DD — Short imperative constraint

**Rejected:** What the agent should NOT do (be specific — "no defense work" or "no companies > 5000 employees" or "no commission-only comp")
**Reason:** Why, in your own words — helps future-you decide whether to lift the constraint later
**Scope:** Hard filter (exclude entirely) | Soft warning (include but flag) — default is hard filter
```

**Editing this file:** delete an entry if the constraint no longer applies, or change Scope from "Hard filter" to "Soft warning" to relax it. The agent re-reads on every session.

**Important:** the agent should NOT add entries here on its own. Only entries you have explicitly stated (e.g., "stop suggesting X" or "I told you no Y last time") should land here. This file is your veto list, not the agent's pattern guesses.

---

<!-- User-rejected ideas appended below this line -->
