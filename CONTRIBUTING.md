# Contributing to job-hunter

Thanks for considering a contribution. This skill is designed to help real people find real jobs, so the bar for changes is "would this help someone job-hunting next Tuesday?"

## Ways to contribute

- **File a bug**: use the [Bug Report template](.github/ISSUE_TEMPLATE/bug_report.md). Include the agent harness (Claude Code, Codex, etc.), the trigger phrase you used, the expected behavior, and what actually happened.
- **Request a feature**: use the [Feature Request template](.github/ISSUE_TEMPLATE/feature_request.md). Describe the job-seeker scenario, not the implementation.
- **Open a Discussion**: for design questions, "I used this to land a job" stories, or anything that's not a bug or feature.
- **Submit a PR**: see workflow below.

## PR workflow

1. **Fork** the repo and create a topic branch off `main`.
2. **Read the `SKILL.md` of every member you touch** end-to-end. This repo is a family of 8 skills (`job-hunter/` orchestrator plus `career-profile/`, `job-search/`, `resume-tailor/`, `cover-letter/`, `application-tracker/`, `interview-prep/`, `outcome-learning/`). The skill behavior is the product; PRs that change behavior must update the relevant section. The shared workspace contract is `job-hunter/references/workspace-contract.md` (each member bundles a copy).
3. **Run the tests**, the same command CI runs in [.github/workflows/test.yml](.github/workflows/test.yml) must pass (`python -m pytest --import-mode=importlib <every member>/tests install tools`). Add new tests for new behavior. `verify_no_fabrication.py` is canonical in `resume-tailor/` and must stay byte-identical in `cover-letter/` and `interview-prep/` (a test enforces it).
4. **Run the trigger evals** if you touch a `SKILL.md` `description` field, even small wording changes can shift which skill loads. Each member's cases are in `<member>/evals/trigger-evals.json`; measure a member's real trigger rate with `python tools/run_trigger_probe.py --family-only` and family routing with `tools/run_routing_evals.py`.
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

- `test_no_sample_profile_in_skill_directory` (`career-profile/tests/`), the `.job-hunter-profile.md` template is **not** in the repo. It's generated into the user's workspace. This prevents a PII vector.
- `test_red_flag_torpedoes_perfect_score` (`job-search/tests/`), red flags are a multiplier, not additive. A pays-in-equity posting cannot score 5.0.
- `test_cv_match_is_heaviest_weight` (`job-search/tests/`), fit matters more than comp. Tuning weights to invert this is a behavior change requiring discussion.

If a PR removes or modifies a load-bearing test, explain in the PR description why the design constraint no longer applies.

## Code of Conduct

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Be kind. Job-hunting is already stressful.
