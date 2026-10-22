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
- Anything that reads or discloses workspace data beyond the user's authorization, or bundles a user's `.job-hunter-profile.md` into the skill's source or distribution

## What doesn't count

- "The skill suggests jobs I don't want", that's a feature request, not a security issue
- "The score for this posting seems wrong", that's a calibration issue, open a regular issue
- "Some recruiters might find this annoying", out of scope

## Supported versions

Only the latest release (the v6 skill family) and `main` are supported. The retired v5 single-skill releases get no fixes. The project is small enough that a fix means "upgrade to latest", no LTS branches.

## Trust model

`job-hunter` runs in the selected agent host, including local agents and hosted
ChatGPT Work. Its bundled Python helpers read and write workspace files and have:

- No telemetry
- No phone-home
- No API-key requirement of their own
- No network calls

The host may send supplied resume/profile content to its model service and may
require its own account or provider credentials. Hosting, retention and training
settings belong to that product; the skill does not promise device-only processing
or override those settings. Search and connected apps have their own permissions.
The skill's learning loop stores confirmed notes in workspace files; it does not
train a model. Download hosted state and outputs before relying on later access.

Unauthorized disclosure or unexpected helper networking is a security issue worth reporting.
