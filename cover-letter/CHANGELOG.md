# Changelog — cover-letter

## v1.1.0 (2026-10-18)

- New step 3: the same fresh-context reviewer pass as resume-tailor
  (`scripts/review_pass.py`, bundled byte-identical; a test guards the copy). Focus for
  letters: invented anecdotes or metrics, employer claims (verified or removed), and
  generic lines. Advisory only. The anti-fabrication gate (now step 4) stays mandatory
  and runs on the revised letter.
- 4 new tests, 1 new outcome eval.

## v1.0.0 — 2026-05-29

Initial release. Added as the 7th member of the job-hunter family, closing a real
gap (the family previously had zero cover-letter capability).

- `draft_cover_letter.py`: deterministic, fact-grounded cover-letter skeleton
  builder. Fills factual slots only from supplied source facts; emits
  `[CONFIRM: ...]` for anything ungrounded. Never invents values.
- Bundles `verify_no_fabrication.py` (byte-identical to resume-tailor's canonical
  gate) so a standalone install is still safe. The drafted letter is compared
  against the user's source facts; new proper nouns / numbers / claims are
  surfaced for per-item confirmation. Persuasive prose is allowed; new facts are
  not. Never auto-sends.
- Ships the family `references/workspace-contract.md` so it is self-contained
  post-install.
- 9 unit tests (incl. load-bearing safety tests: bundled-gate present,
  gate catches an invented metric, gate byte-identical to resume-tailor),
  9 trigger evals, 3 outcome evals.
