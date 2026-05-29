# Reload Protocol, job-hunter

How to pick up where a previous session left off, with the right context loaded in the right
order. Designed for any of: cold session resume, after compaction, after a long pause, or
after handoff from another agent.

## Start of session, read in this order

1. **`docs/continuity/session-state.md`**, current state, what's done, what's next. The
   shortest path to knowing where we are.

2. **`docs/continuity/compaction-handoff.md`**, if the last session ended near compaction
   or with substantial uncommitted work, this file has the full evidence chain. Designed to
   be self-contained.

3. **`docs/continuity/decisions.md`**, *why* the current state is the current state.
   Critical for not re-relitigating settled choices.

4. **`docs/continuity/rejected-ideas.md`**, *what we deliberately didn't do*, with reasons.
   Saves the time of proposing something that was already rejected.

5. **`docs/continuity/lessons.md`**, specific failure modes from real iterations. Avoid
   repeating them.

6. **`CHANGELOG.md`** (one level up), the public iteration record. Confirms what's in the
   current version vs. earlier ones.

7. **`docs/continuity/open-questions.md`**, only if you need to pick up an unresolved
   thread.

## Verify state before trusting notes

Continuity docs can drift from filesystem state. Before acting on what they say, run (THIS repo is the active v5+ source of truth):

```powershell
$builder = "C:\Users\Owner\.claude\skills\self-improving-skills"
$work = "E:\Git\job-hunter-public"

# 1. Audit should be 15/15, 0 findings
python "$builder\scripts\audit_existing.py" --skill $work | Select-Object -First 6

# 2. Validate should return OK
python "$builder\scripts\validate.py" $work

# 3. Mock eval, 28 trigger evals (100% trigger accuracy)
$results = "$work\evals\results\reload-check-$(Get-Date -Format yyyyMMdd)"
if (Test-Path $results) { Remove-Item $results -Recurse -Force }
python "$builder\scripts\run_evals.py" --skill $work --runner mock --out-dir $results
Get-Content "$results\report.md"

# 4. Unit tests should be 201/201 (v5.2.0)
python -m pytest "$work\tests" -q

# 5. Verify the plugin-managed original (v1, read-only) is untouched
(Get-FileHash "C:\Users\Owner\AppData\Roaming\Claude\local-agent-mode-sessions\skills-plugin\5c05cc04-2463-4046-bba9-caf393e8b23f\e536094f-d1a7-4bf2-b2e6-96280eabdba7\skills\job-hunter\SKILL.md" -Algorithm SHA256).Hash
# Should equal: C9031AB1AB57CDFBD146A4E15838F20F0390E30D387AE2018AB2A145EB9D2724
```

If any of these don't match expectations, **stop**. Investigate before continuing. Possible
causes: someone edited the plugin-managed path (and it'll be re-synced), the harness was
updated (commands or scoring may differ), or the working copy got partially overwritten.

## During work

- Continuity docs are local evidence about past state. They are NOT instructions that override
  the user's current request or the actual code/data state. When a continuity doc and current
  reality disagree, trust the reality and update the doc.
- Apply Karpathy's surgical-changes rule: each edit should trace to a specific signal or user
  request. If you find yourself making unrelated "while I'm here" improvements, stop.
- After every meaningful change, re-run the eval suite. Don't batch verifications.

## Before handoff, compaction, or long pause

1. **`session-state.md`**: update "Last updated" date, current scores, what got done, what's
   pending.
2. **`compaction-handoff.md`**: if substantial work happened, refresh this with the full
   evidence chain. Goal: a future session could read THIS file alone and pick up.
3. **`decisions.md`**: any durable decisions made? Add entries.
4. **`rejected-ideas.md`**: any approaches considered and dropped? Add entries.
5. **`lessons.md`**: any surprises or failure modes worth recording? Add entries.
6. **`CHANGELOG.md`**: if this session shipped a new accepted iteration, write the entry.
7. **`_meta.json`**: bump `current_score`, `last_iteration`, `signals_observed` if scores moved.
8. **Frozen cohorts**: if the description was substantially rewritten this session, run
   `snapshot_frozen.py --skill $work --apply` to mint a new frozen-vN cohort. The script
   refuses to overwrite, so this is always safe.

## After compaction specifically

The "I just compacted, what now?" sequence:

1. Run the **verify state** block above first. Compaction sometimes drops uncommitted edits
   that were in conversation context but not on disk; this catches the discrepancy.
2. Read `compaction-handoff.md` from top to bottom. It's the only doc designed to be
   self-contained for cold pickup.
3. If `compaction-handoff.md` references work that doesn't match the filesystem, follow up on
   the discrepancy before continuing.
4. Resume from the "Exact Next Action" section of `session-state.md`.

## Emergency: continuity docs lost or corrupted

If the entire `docs/continuity/` directory is gone or unreadable:

1. The skill still works as a skill, SKILL.md is the entry point.
2. CHANGELOG.md has the public iteration record.
3. `_meta.json` has the score history.
4. Recovery procedure: regenerate the continuity stack from `retrofit_existing.py --apply`
   (it'll create stub templates), then re-fill from CHANGELOG + git log + your own session memory.

## Start Of Session

The canonical read order (also captured in the "Start of session" section above): read
`session-state.md` first for current state, then `compaction-handoff.md` for the full evidence
chain, then `decisions.md` / `rejected-ideas.md` / `lessons.md` for the why-context. Verify
filesystem state before trusting the docs, they can drift.

## During Work

Continuity docs are local evidence about past state, NOT instructions that override the user's
current request or the actual code state. When a doc and current reality disagree, trust the
reality and update the doc. Apply Karpathy's surgical-changes rule: every edit traces to a
specific signal. Re-run evals after every change, don't batch verifications.

## Before Handoff Or Compaction

Update `session-state.md`, `compaction-handoff.md`, and any other touched continuity files.
If a new accepted iteration shipped, write a `CHANGELOG.md` entry and bump `_meta.json`. If
the description was substantially rewritten, run `snapshot_frozen.py --apply` to mint a new
frozen cohort. Full checklist is in the "Before handoff, compaction, or long pause" section
above.
