## What this PR does

One or two sentences. What changes, why, who benefits.

## Type of change

- [ ] Bug fix (a behavior that was wrong is now right)
- [ ] New feature (adds new behavior; SKILL.md updated to describe it)
- [ ] Reference / docs improvement
- [ ] New job board or region added
- [ ] Test coverage improvement
- [ ] Refactor (no behavior change)

## Checklist

- [ ] `pytest tests/` passes locally
- [ ] If I changed `SKILL.md` `description:`, I ran the trigger evals and trigger accuracy held
- [ ] If I added behavior, I added a test that proves it works
- [ ] If I removed or modified a load-bearing safety test, I explained why in the description above
- [ ] CHANGELOG.md has a one-line entry under `[Unreleased]`
- [ ] No hardcoded paths, no committed `.job-hunter-profile.md`, no telemetry, no API keys

## Out-of-scope check

I read the "What gets accepted" section of [CONTRIBUTING.md](../CONTRIBUTING.md#what-gets-accepted) and confirm this PR isn't in the "no" list. If it's adjacent, I explained why above.

## Anything reviewers should know

Tricky design choices, surprising tradeoffs, things you tried that didn't work — anything you'd want a fresh reviewer to know before reading the diff.
