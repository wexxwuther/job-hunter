# Security Policy

## Reporting a vulnerability

If you find a security issue in `job-hunter`, **do not open a public issue.** Instead:

- **Email:** greg@gdkdigital.com
- **Subject line:** `[security] job-hunter, <one-line summary>`

Include:
- What you found (the bug, not just the symptom)
- How to reproduce it
- What an attacker could do with it
- Your suggested fix, if any

You'll get an acknowledgment within 72 hours. Confirmed issues get patched on `main`, a new release tag, and a credit in CHANGELOG.md (unless you'd rather stay anonymous).

## What counts as a security issue

- Anything that could expose a user's resume, North-Star profile, or other workspace files to a third party
- Anything that could let a posting (or a maliciously crafted "job description") execute code via the skill
- Anything that bypasses the design constraint that `.job-hunter-profile.md` lives **only** in the user's workspace and is never sent anywhere

## What doesn't count

- "The skill suggests jobs I don't want", that's a feature request, not a security issue
- "The score for this posting seems wrong", that's a calibration issue, open a regular issue
- "Some recruiters might find this annoying", out of scope

## Supported versions

Only the latest release is supported. The skill is small enough that a fix means "upgrade to latest", no LTS branches.

## Trust model

`job-hunter` is a local agent skill. It runs in your harness (Claude Code, Codex, etc.), reads files from your workspace, and writes outputs to your workspace. It has:

- No telemetry
- No phone-home
- No required API keys
- No required network calls beyond what your agent already does to search the web

If you spot a change that violates any of those, that's a security issue worth reporting.
