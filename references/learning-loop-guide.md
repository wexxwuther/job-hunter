# The Learning Loop

How job-hunter remembers what works for *you* across sessions, while keeping every byte of that memory in your workspace and out of the cloud.

## What is the learning loop?

A small set of plain-markdown files in your workspace that capture decisions, outcomes, lessons, and hard constraints, and a pair of scripts that translate signals from those files into suggested lessons for you to review and confirm.

The skill itself never changes between users. What changes per user is the **context** the agent operates in. That context is what you see in your `.job-hunter/` directory.

## The four files

All live under `<your-workspace>/.job-hunter/`:

| File | Who writes | Who reads | Purpose |
|---|---|---|---|
| **DECISIONS.md** | Agent (with your reasons) + you | Agent (last few entries, for continuity) | Per-session record: skipped Acme because it required relocation, chose light tailoring for Beta, etc. |
| **LESSONS.md** | You, confirmed via agent suggestions | Agent every session, before scoring | Durable patterns: "user rejects large companies", "comp_vs_target is decisive for this user". Adjusts how sub-scores are graded for *you*. |
| **OUTCOMES.md** | Agent (on tracker.json status changes) + you | Agent for learning, propose_lessons.py for pattern detection | What actually happened: accepted, rejected after onsite, no response after 21 days. |
| **REJECTED_IDEAS.md** | You only, agent never writes here | Agent every session, before search | Hard constraints: "no defense contractors", "no commission-only comp". These are filters, not preferences. |

## The cycle

```
You apply → Tracker status changes → OUTCOMES.md updated → harvest_outcomes.py
runs (when ≥5 closed outcomes) → propose_lessons.py emits suggestion →
Agent surfaces suggestion + evidence to you → You confirm (or reject) →
Confirmed lesson appends to LESSONS.md → Next session, lesson shapes scoring
```

The cycle has six guardrails that keep it honest:

1. **Cold-start guard.** No lessons proposed until at least 5 closed-loop outcomes. Pattern detection from thin data is guessing, not learning. The `harvest_outcomes.py` script enforces this and returns `no_op_reason: "need >=5 closed-loop outcomes, have N"`.
2. **Opt-in only.** The agent **never** auto-writes to LESSONS.md. Every entry there required you to say yes. `propose_lessons.py` emits suggestions with evidence; the agent surfaces them; you confirm; only then does the agent append.
3. **Deterministic translation.** The script that proposes lessons is deterministic, same input produces the same output. The "reason" line for each suggestion is anchored in observed evidence, never paraphrased.
4. **Bounded influence.** Lessons adjust how sub-scores are *graded* for you. They do **not** change the scoring weights in `scripts/score_posting.py`, those stay constant for all users.
5. **Plain markdown.** Every file is readable, editable, deletable by you. No black-box weights, no opaque database. Delete a lesson you disagree with and it's gone.
6. **Local-only.** No telemetry, no phone-home. The `.job-hunter/` directory lives in your workspace. The `harvest_outcomes.py` and `propose_lessons.py` scripts read local files only.

## Privacy notes

- Add `.job-hunter/` to your own `.gitignore` if you keep your workspace in git. The skill's own `.gitignore` already prevents it from being committed to the public job-hunter repo if you ever clone there.
- `signals.json` and any `proposal.json` written by the scripts contain workspace data, treat them as user-private.
- Sharing your `tracker.html` with a friend? Fine, that's just the rendered job list. But avoid sharing the contents of `.job-hunter/` unless you want to share your reasoning and history.

## When to nuke and start over

You can delete `.job-hunter/` at any time without breaking the skill, the next run will re-initialize it with empty templates. Reasons you might want to:

- Career pivot, where past lessons no longer apply.
- Privacy reset (e.g., a shared workspace where you don't want history visible).
- You suspect a confirmed lesson is wrong (faster to nuke + rebuild than edit-by-edit).

## The cadence

- Per-session: agent reads all four files at the start of each session.
- Per-outcome: when you update `tracker.json` status past `applied`, the agent appends to OUTCOMES.md.
- Per-significant-change: when ≥5 closed outcomes exist AND a new outcome lands, agent opportunistically runs harvest + propose to surface any new patterns.

## What this is not

- Not a self-modifying skill. The Python in `scripts/` is identical for every user, every version.
- Not silent learning. Every lesson required your confirmation.
- Not a competitive advantage over time. The whole point is that the skill works equally well for everyone; what differs is the per-user context you've accumulated.
- Not training data. Nothing here is uploaded, shared, or used to train any model.
