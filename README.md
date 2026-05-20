# job-hunter

> **Stop applying to ghost jobs.**
> A free, open-source AI agent skill that searches LinkedIn, Indeed, and state job boards, scores each posting **1-5** for legitimacy and CV-fit, and outputs a **tailored, ATS-ready resume + cover letter** per role.
> Built for every career — nurses, welders, teachers, engineers. Runs in **Claude Code**, **Codex**, and any [agentskills.io](https://agentskills.io)-compatible agent.

[![Tests](https://github.com/wexxwuther/job-hunter/actions/workflows/test.yml/badge.svg)](https://github.com/wexxwuther/job-hunter/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Agent Skill](https://img.shields.io/badge/agentskills.io-2025--12--18-blue)](https://agentskills.io)
[![Trigger accuracy](https://img.shields.io/badge/trigger_accuracy-28%2F28-brightgreen)](evals/trigger-evals.json)
[![Unit tests](https://img.shields.io/badge/unit_tests-177%2F177-brightgreen)](tests/)
[![GitHub Release](https://img.shields.io/github/v/release/wexxwuther/job-hunter)](https://github.com/wexxwuther/job-hunter/releases/latest)
[![GitHub stars](https://img.shields.io/github/stars/wexxwuther/job-hunter?style=social)](https://github.com/wexxwuther/job-hunter/stargazers)
[![GitHub last commit](https://img.shields.io/github/last-commit/wexxwuther/job-hunter)](https://github.com/wexxwuther/job-hunter/commits/main)
[![Downloads](https://img.shields.io/github/downloads/wexxwuther/job-hunter/total)](https://github.com/wexxwuther/job-hunter/releases)

---

## Quickstart

Once installed (see [Install](#install) below), just ask your agent:

```
Find me senior backend engineer jobs in Seattle, $180k+, that aren't ghost listings.
```

```
Here's my resume — what nurse practitioner jobs near Austin would I be a strong fit for?
```

```
Tailor my resume for this posting: [URL]
```

The skill auto-activates, walks you through 5 quick profile questions on first use (saved to `.job-hunter-profile.md` in your workspace — **never** sent anywhere), then runs the full pipeline:

1. **Understand the user** — North-Star profile (5 questions) + resume parsing
2. **Search** — LinkedIn, Indeed, Glassdoor, ZipRecruiter, Dice, Wellfound, USAJobs, 50-state workforce commissions, and company career pages
3. **Score** — every posting gets a 1-5 across 5 sub-scores (CV match, comp vs target, cultural signals, posting legitimacy, red flags)
4. **Tailor** — ATS-optimized DOCX resume + cover letter per role you want to pursue
5. **Track** — interactive HTML tracker with sort/filter, sub-score breakdown, and weighted global score

---

## Install

Pick your harness. All four install paths are first-class.

| Harness | Skills directory | Install guide |
|---|---|---|
| **Claude Code** | `~/.claude/skills/` | [install/claude-code.md](install/claude-code.md) |
| **OpenAI Codex** | `~/.codex/skills/` | [install/codex.md](install/codex.md) |
| **OpenClaw** | `~/.openclaw/skills/` | [install/openclaw.md](install/openclaw.md) |
| **Hermes Agent** | `~/.hermes/skills/` | [install/hermes.md](install/hermes.md) |

### One-shot installers

If you just want it working in 10 seconds:

```bash
# macOS / Linux
curl -fsSL https://raw.githubusercontent.com/wexxwuther/job-hunter/main/install/install.sh | bash
```

```powershell
# Windows (PowerShell)
iwr https://raw.githubusercontent.com/wexxwuther/job-hunter/main/install/install.ps1 -UseBasicParsing | iex
```

### Skip the line — download the zip

Prefer not to clone? Grab the latest release zip from the [Releases page](https://github.com/wexxwuther/job-hunter/releases/latest) and extract it into your agent's skills directory. Done.

---

## How the scoring works

Every job posting gets scored across **five sub-scores** (1-5 each) with documented weights:

| Sub-score | Weight | What it measures |
|---|---|---|
| `cv_match` | **0.35** (heaviest) | How well your resume aligns with the posting's stated requirements |
| `comp_vs_target` | 0.25 | Listed comp vs your target band from your North-Star profile |
| `cultural_signals` | 0.20 | Mission, team size, hiring-page tone, glassdoor signal |
| `posting_legitimacy` | 0.20 | Ghost-job rubric (re-posts, vague specs, missing recruiter) |
| `red_flags_penalty` | **multiplier** | Pays-in-equity, asks-for-SSN-pre-offer, fee-to-apply — torpedoes the score |

A single severe red flag can take an otherwise-perfect posting from 5.0 to 1.0. Read the full rubrics in [references/posting-legitimacy-rubric.md](references/posting-legitimacy-rubric.md) and [references/match-quality-rubric.md](references/match-quality-rubric.md).

---

## What you get out of the box

```
job-hunter/
├── SKILL.md                          # The skill itself (agentskills.io spec)
├── scripts/                          # 15 production Python scripts (no network deps)
│   ├── score_posting.py              # Deterministic 1-5 scoring
│   ├── parse_resume.py               # DOCX/PDF/text resume parser
│   ├── extract_ats_keywords.py       # Keyword-gap analysis
│   ├── build_search_queries.py       # Multi-board query builder
│   ├── expand_role_synonyms.py       # Role-title synonyms (SDE = SWE = Engineer)
│   ├── normalize_salary.py           # $120k/yr = $10k/mo = $60/hr
│   ├── dedupe_postings.py            # Cross-board dedup
│   ├── generate_tracker_html.py      # Interactive HTML tracker
│   ├── init_profile.py               # North-Star profile management
│   ├── init_workspace.py             # Sets up the .job-hunter/ learning loop
│   ├── harvest_outcomes.py           # Reads outcomes, finds patterns
│   ├── propose_lessons.py            # Suggests lessons for you to confirm
│   ├── draft_followup.py             # Check-in + thank-you email drafts
│   ├── export_workspace.py           # Bundle your state to a zip
│   └── import_workspace.py           # Restore from a zip on a new machine
├── references/                       # 9 reference docs the skill consults
├── assets/templates/                 # Template files + tracker CSS
├── tests/                            # 177 unit tests
└── evals/                            # Trigger + outcome eval suites
```

No API keys required. No telemetry. No phoning home. Your `.job-hunter-profile.md` stays in **your** workspace.

---

## The learning loop (v5+)

Job-hunter keeps a small, per-user memory of decisions, outcomes, and confirmed lessons — all in plain-markdown files in your workspace, never sent anywhere.

| File (lives in `<your-workspace>/.job-hunter/`) | What it captures |
|---|---|
| `DECISIONS.md` | Per-session choices and why (skipped Acme because location, chose light tailoring for Beta) |
| `LESSONS.md` | Patterns about your preferences — **you confirm each one** before it's added |
| `OUTCOMES.md` | What actually happened (accepted, rejected after onsite, no response after 21 days) |
| `REJECTED_IDEAS.md` | Hard constraints — "no defense contractors", "no commission-only" — agent never re-asks |

The cycle: as you apply and outcomes land, `scripts/harvest_outcomes.py` looks for patterns. When ≥5 closed-loop outcomes exist, `scripts/propose_lessons.py` translates the signals into suggested lessons. The agent surfaces each suggestion with evidence and asks **"want me to remember this?"** — only confirmed lessons get added to `LESSONS.md`.

**Six guardrails keep it honest:**
1. **Cold-start guard**: no lessons proposed until ≥5 closed-loop outcomes (no pattern detection from thin data)
2. **Opt-in only**: the agent never auto-writes lessons; every entry is user-confirmed
3. **Deterministic translation**: same input → same suggestion; reasons are anchored in evidence, not paraphrased
4. **Bounded influence**: lessons adjust how sub-scores are *graded* for you; the scoring weights in `score_posting.py` stay constant for all users
5. **Plain markdown**: every file is readable, editable, deletable by you — no black-box weights
6. **Local-only**: no telemetry, no phone-home, no upload

Delete `.job-hunter/` to start over. The skill re-initializes it on next run. See `references/learning-loop-guide.md` for the full design and trust model.

---

## Tested

```bash
cd job-hunter
pip install pytest                   # only dependency
pytest tests/
# 177 passed
```

CI runs the full suite on every push across Python 3.10/3.11/3.12 on Ubuntu, macOS, and Windows.

---

## FAQ

**I don't have a resume yet — can I still use this?**
Yes. If no resume is in your workspace, the skill will offer two paths: (1) point to one you have (file upload, path, or paste), or (2) walk you through a focused interview to draft a baseline `resume.md` from scratch — work history, accomplishments with numbers, skills, education, projects, and any non-traditional experience. Once the baseline is solid, the normal job-search and tailoring flow kicks in. The skill won't run the job search with no resume at all, because the scoring rubric and tailoring step both need one.

**My resume is thin or out of date.**
The skill will flag that before tailoring rather than producing 10 weak tailored versions of a weak base resume. It'll walk you through a short strengthen-the-baseline pass (asking for numbers on your accomplishments, surfacing skills you haven't listed, filling in dates) and then proceed.

**Will this submit applications for me?**
No. It produces the tailored resume + cover letter + application tracker. You submit. That's a deliberate boundary — auto-submission is a different trust model and out of scope for this skill.

**Does it send my resume or profile anywhere?**
No. Your resume, your `.job-hunter-profile.md`, and every tailored output live in your workspace. The skill has no telemetry, no phone-home, no required API keys, and no required network calls beyond what your agent already does to search the web. See [SECURITY.md](SECURITY.md) for the full trust model.

**Why isn't there an interview-prep feature?**
Deliberately out of scope. Interview prep is a different workflow with different inputs and a different success criterion. If you want it, run a separate interview-prep skill alongside this one.

**Does the skill learn from my interactions?**
Yes, but entirely locally and opt-in. After 5+ closed-loop application outcomes, the skill surfaces patterns it noticed (e.g., "4 of 5 rejections cite comp — want me to remember this?") and asks you to confirm before adding any lesson. Confirmed lessons live in `<your-workspace>/.job-hunter/LESSONS.md` and adjust how sub-scores are graded for you. The scoring weights themselves stay constant. Nothing is uploaded or used for training. See the [learning loop](#the-learning-loop-v5) section above and `references/learning-loop-guide.md`.

**Can I reset what the skill has learned about me?**
Yes — delete `<your-workspace>/.job-hunter/`. The next run will re-initialize empty templates. You can also edit any of the four files directly (LESSONS.md, DECISIONS.md, OUTCOMES.md, REJECTED_IDEAS.md) since they're plain markdown.

**Will the skill help me follow up on applications?**
Yes. `scripts/draft_followup.py` has two templates: `check_in` (7-10 days after applying with no response) and `thank_you` (24-48 hours after an interview). The skill scans your `tracker.json` for applications stale at `status=applied` for 7+ days and offers to draft polite check-in emails. It also drafts thank-you notes after you report an interview. **The skill never sends the email** — that's by design, and a load-bearing safety test enforces it. You copy-paste. See `references/followup-templates.md` for the patterns and cited sources.

**Can I move my job-hunter state to a different machine?**
Yes. `scripts/export_workspace.py` bundles your profile + `.job-hunter/` learning loop + `tracker.json` (and optionally your tailored DOCX outputs) into a single zip. `scripts/import_workspace.py` restores them on a new machine. The export refuses to write to cloud-sync directories (Dropbox, OneDrive, iCloud) by default; pass `--allow-cloud` if you intentionally want that. Roundtrip preserves all files byte-for-byte. The import path-sanitizes the archive to reject any traversal payloads.

**Does this work for non-tech careers?**
Yes — this is the explicit design goal. `references/niche-boards-by-industry.md` includes verified entries for healthcare (Vivian Health, Nurse.com, Health eCareers, AlliedTravelCareers, state nursing board portals), trades (iHireConstruction, AllTrucking, IBEW/UA local hall search patterns, SkillBridge for military-to-trades), legal (LawCrossing, BCG Attorney Search, state bar career pages), education (HigherEdJobs, SchoolSpring, K12JobSpot), government (USAJobs, GovernmentJobs.com, NEOGOV-hosted municipal portals, state civil-service exams), and more. The agent picks the right tier-2 boards based on your role.

---

## Contributing

Issues, feature requests, and PRs welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for the workflow. If you found a security issue, see [SECURITY.md](SECURITY.md) for private disclosure.

If you use `job-hunter` to land a job, **open a Discussion and tell us** — that's the highest-signal feedback this project gets.

---

## License

[MIT](LICENSE). Use it commercially, fork it, rebrand it, ship it inside your product. No attribution required (but appreciated).

---

## Credits

- Competitive design review against [`santifer/career-ops`](https://github.com/santifer/career-ops) (MIT) — `job-hunter` v4 folded in four of its ideas (1-5 scoring, legitimacy/match split, North-Star profile, multi-block tracker) and rejected five others where our design constraints differ.
- Built on the open [agentskills.io](https://agentskills.io) spec so it runs across Claude Code, Codex, OpenClaw, and any future compatible agent.
