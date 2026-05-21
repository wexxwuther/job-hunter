# Contributing to job-hunter

Thanks for considering a contribution. This skill is designed to help real people find real jobs, so the bar for changes is "would this help someone job-hunting next Tuesday?"

## Ways to contribute

- **File a bug**: use the [Bug Report template](.github/ISSUE_TEMPLATE/bug_report.md). Include the agent harness (Claude Code, Codex, etc.), the trigger phrase you used, the expected behavior, and what actually happened.
- **Request a feature**: use the [Feature Request template](.github/ISSUE_TEMPLATE/feature_request.md). Describe the job-seeker scenario, not the implementation.
- **Open a Discussion**: for design questions, "I used this to land a job" stories, or anything that's not a bug or feature.
- **Submit a PR**: see workflow below.

## PR workflow

1. **Fork** the repo and create a topic branch off `main`.
2. **Read [SKILL.md](SKILL.md)** end-to-end. The skill behavior is the product; PRs that change behavior must update the relevant section.
3. **Run the tests**, `pytest tests/` must pass. Add new tests for new behavior.
4. **Run the trigger evals** if you touch the SKILL.md `description` field, even small wording changes can shift trigger accuracy. The eval definitions are in [evals/trigger-evals.json](evals/trigger-evals.json).
5. **Update CHANGELOG.md** with a one-line entry under an `[Unreleased]` section.
6. **Open the PR**, use the [PR template](.github/PULL_REQUEST_TEMPLATE.md).

## What gets accepted

✅ **Yes:**
- Bug fixes with a regression test
- New job boards (especially regional/niche/non-US, this is a generalist skill)
- Improvements to ghost-job detection rubrics with cited evidence
- Resume-format support beyond DOCX/PDF/text
- Translations of `references/` docs

❌ **No:**
- Hardcoded company lists (breaks generalist scope, see [decisions in v4](CHANGELOG.md#v4))
- Heavy runtime dependencies (Playwright + bundled Chromium was specifically rejected, keep it portable)
- Letter-grade rendering on top of the 1-5 scores (cosmetic; adds no signal)
- Slash-command UX (auto-activation on natural language is the design)
- Telemetry, analytics, or anything that phones home

## Code style

- **Python**: PEP 8, no formatter required but `ruff check .` should pass
- **Markdown**: hard-wrap at 100 cols where practical
- **No emojis** in code or commit messages

## What "load-bearing" means

Some tests have comments calling them "load-bearing safety tests." These encode design constraints that future-you (or future-contributor) will be tempted to break. They include:

- `test_no_sample_profile_in_skill_directory`, the `.job-hunter-profile.md` template is **not** in the repo. It's generated into the user's workspace. This prevents a PII vector.
- `test_red_flag_torpedoes_perfect_score`, red flags are a multiplier, not additive. A pays-in-equity posting cannot score 5.0.
- `test_cv_match_is_heaviest_weight`, fit matters more than comp. Tuning weights to invert this is a behavior change requiring discussion.

If a PR removes or modifies a load-bearing test, explain in the PR description why the design constraint no longer applies.

## Code of Conduct

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Be kind. Job-hunting is already stressful.
