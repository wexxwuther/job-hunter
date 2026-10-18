# Changelog - resume-tailor

## v1.1.1 (2026-10-18)

- Gate fix (canonical copy): verify_no_fabrication.py: a comma right after a number ("In 2023, four new") was kept as part of the token, so a number or year already in the source was flagged as new ("2023,", "40,"). Trailing commas are now stripped; inner commas ("1,200") are kept and truly new numbers are still flagged. Found by the first live outcome-eval run of interview-prep (2026-10-18). Regression tests in `tests/test_verify_no_fabrication.py`.

## v1.1.0 (2026-10-18)

Fresh-context drafter-reviewer pass for Mode B (new step 5), adapted from the reviewer agent
in MadsLorentzen/ai-job-search (idea only; no code taken):

- `scripts/review_pass.py packet` builds the reviewer prompt from the source facts, the
  posting and the draft. Each block gets a random per-packet marker, and the posting is
  marked untrusted.
- A subagent with no other context returns JSON findings. On harnesses without subagents
  the review runs as a separate same-context step, and the user is told it is weaker.
- `scripts/review_pass.py check` validates the reply. A quote counts only where it really
  appears: `location` in the draft, `source_evidence` in the source (never the posting or
  the draft), `posting_evidence` in the posting. Every unaddressed requirement goes to the
  user, even with a related source quote. Employer claims must be verified or removed.
- Advisory only. `verify_no_fabrication.py` stays mandatory and runs last, on the revised
  draft. At most two rounds.
- First live trial: the reviewer quoted "2021-2024" for a "5+ years" requirement, and
  "built SQL reports" for "advanced SQL". That is why `missed_requirement` always asks the
  user. Regression test added.
- 26 new tests (7 load-bearing), mutation-checked (9/9 mutants killed).

## v1.0.0 (2026-05-28)

Established as the **resume-tailor** member of the job-hunter family (v6.0.0 split of
the former job-hunter monolith). This member owns its phase's scripts + evals
and is routed by the `job-hunter` orchestrator; it also works standalone.
Reads/writes the shared `.job-hunter/` workspace per
`job-hunter/references/workspace-contract.md` and degrades gracefully when
run alone. See the family continuity stack at `job-hunter/docs/continuity/`.
