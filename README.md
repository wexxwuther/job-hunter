# job-hunter

> **Stop applying to ghost jobs.**
> A free, open-source AI agent **skill family** that searches LinkedIn, Indeed, and state job boards, scores each posting **1-5** for legitimacy and CV-fit, and outputs a **tailored, ATS-ready resume + cover letter** per role.
> Built for every career: nurses, welders, teachers, engineers. Runs cross-OS (Windows / macOS / Linux) in **Claude Code**, **OpenAI Codex**, **OpenClaw**, **Hermes Agent**, and any [agentskills.io](https://agentskills.io)-compatible agent.

[![Tests](https://github.com/wexxwuther/job-hunter/actions/workflows/test.yml/badge.svg)](https://github.com/wexxwuther/job-hunter/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Agent Skill](https://img.shields.io/badge/agentskills.io-open_standard-blue)](https://agentskills.io)
[![Unit tests](https://img.shields.io/badge/unit_tests-455%2F455-brightgreen)](.)

> **job-hunter is a skill family (since v6.0.0; first released as v6.1.0).** What used to be one large skill is an **orchestrator** (`job-hunter`) that routes to seven focused member skills, so "just tighten my resume" runs the resume skill alone, while "run my whole job search" fans out across all of them. The orchestrator owns the shared `.job-hunter/` workspace and the anti-fabrication safety gate, and decides which members each request needs.
>
> | Skill | Role | What it does |
> |---|---|---|
> | **job-hunter** | orchestrator | Routes your request to the right members; owns the workspace + the anti-fabrication invariant |
> | **career-profile** | profile-intake | Captures your North-Star profile (5 questions) + parses your resume |
> | **job-search** | search | Finds, dedupes, and scores postings 1-5 across 4 search tiers |
> | **resume-tailor** | resume-tailor | Tightens (Mode A) or tailors (Mode B) your resume, with the verify-no-fabrication gate |
> | **cover-letter** | cover-letter | Drafts a posting-tailored cover letter from your real facts, through the same gate |
> | **application-tracker** | tracker | Tracks applications + drafts stale-application follow-ups |
> | **interview-prep** | interview-prep | Preps you for a scheduled interview: stage questions, STAR answers from your real experience, gap answers, mock interview |
> | **outcome-learning** | learning-loop | Learns from your outcomes; proposes opt-in lessons |
>
> Install all 8 together: the Claude Code plugin or the one-shot installer ([Install](#install) below). Each member also works on its own.
[![GitHub Release](https://img.shields.io/github/v/release/wexxwuther/job-hunter)](https://github.com/wexxwuther/job-hunter/releases/latest)
[![GitHub stars](https://img.shields.io/github/stars/wexxwuther/job-hunter?style=social)](https://github.com/wexxwuther/job-hunter/stargazers)
[![GitHub last commit](https://img.shields.io/github/last-commit/wexxwuther/job-hunter)](https://github.com/wexxwuther/job-hunter/commits/main)
[![Downloads](https://img.shields.io/github/downloads/wexxwuther/job-hunter/total)](https://github.com/wexxwuther/job-hunter/releases)

---

## Why I built this

People are looking for jobs and changing career paths all the time. The job search is full of noise. Ghost listings that were never real, irrelevant matches, generic advice, hours wasted tailoring resumes for roles that already had a hire lined up. It eats time you don't have.

I also believe agent skills are the next big breakthrough in agentic AI. Small, focused, composable capabilities you bolt onto whatever agent you're already using. Combining the two was the obvious move.

This is what job-hunting looks like when an AI agent actually does the boring parts. Free, open-source, runs locally, never uploads your resume.

---

## Quickstart

Once installed (see [Install](#install) below), just ask your agent:

```
Find me senior backend engineer jobs in Seattle, $180k+, that aren't ghost listings.
```

```
Here's my resume, what nurse practitioner jobs near Austin would I be a strong fit for?
```

```
Tailor my resume for this posting: [URL]
```

The skill auto-activates, walks you through 5 quick profile questions on first use (saved to `.job-hunter-profile.md` in your workspace, **never** sent anywhere), then runs the full pipeline:

1. **Understand the user**, North-Star profile (5 questions) + resume parsing
2. **Search**, LinkedIn, Indeed, Glassdoor, ZipRecruiter, Dice, Wellfound, USAJobs, 50-state workforce commissions, and company career pages
3. **Score**, every posting gets a 1-5 across 5 sub-scores (CV match, comp vs target, cultural signals, posting legitimacy, red flags)
4. **Tailor**, ATS-optimized DOCX resume + cover letter per role you want to pursue
5. **Track**, interactive HTML tracker with sort/filter, sub-score breakdown, and weighted global score
6. **Prep**, a stage-specific interview prep pack built from the resume and cover letter you actually sent
7. **Learn**, after 5+ closed outcomes, opt-in lessons about what is working for you

---

## Install

job-hunter is a family of 8 skills. Install all 8; the orchestrator routes between them.

| Harness | Where the skills go | Install guide |
|---|---|---|
| **Claude Code** | the `job-hunter` plugin, or `~/.claude/skills/<skill>/` | [install/claude-code.md](install/claude-code.md) |
| **OpenAI Codex** | `~/.agents/skills/<skill>/` | [install/codex.md](install/codex.md) |
| **ChatGPT** | One upload containing the family and member resources; subject to workspace skill availability | [install/chatgpt.md](install/chatgpt.md) |
| **OpenClaw** | `~/.agents/skills/<skill>/` (shared with Codex) | [install/openclaw.md](install/openclaw.md) |
| **Hermes Agent** | `~/.hermes/skills/<skill>/` | [install/hermes.md](install/hermes.md) |

### ChatGPT and OpenClaw compatibility builds (local, unreleased)

Run `python tools/build_runtime_packages.py` to generate target ZIPs in
`dist/compatibility/`. ChatGPT gets one skill containing all member workflows;
OpenClaw gets eight standalone skill directories. These adapters use the host's
available tools, support sequential work without Claude's `Task` tool, and explain
session storage and missing-capability behavior. Local archive/script tests are
available; live ChatGPT upload and OpenClaw session acceptance remain pending.

The local-only privacy claims elsewhere in this README describe local agents.
Files supplied to ChatGPT are processed under that product's account/workspace
settings; download state and outputs before ending a hosted session.

### Claude Code: the plugin (all 8 in one step)

```
/plugin marketplace add wexxwuther/job-hunter
/plugin install job-hunter@gdk-skills
```

You get `/job-hunter:job-hunter` (the orchestrator) plus `/job-hunter:career-profile`, `:job-search`, `:resume-tailor`, `:cover-letter`, `:application-tracker`, `:interview-prep`, and `:outcome-learning`.

### One-shot installers (every harness)

Installs all 8 skills into `~/.claude/skills/`, `~/.agents/skills/` (Codex and OpenClaw), and `~/.hermes/skills/`:

```bash
# macOS / Linux
curl -fsSL https://raw.githubusercontent.com/wexxwuther/job-hunter/main/install/install.sh | bash
```

```powershell
# Windows (PowerShell)
iwr https://raw.githubusercontent.com/wexxwuther/job-hunter/main/install/install.ps1 -UseBasicParsing | iex
```

### Offline, or the Claude.ai / Claude Desktop uploader

The [latest release](https://github.com/wexxwuther/job-hunter/releases/latest) has:

- `job-hunter-FAMILY-installer-only-v6.1.0.zip`: unzip, then run `bash job-hunter/install/install.sh` (or `install\install.ps1` on Windows). No internet needed.
- `<skill>-v6.1.0-claude-code.zip` (8 files, the orchestrator is `job-hunter-orchestrator-...`): the Claude.ai / Desktop skill uploader takes one skill per zip, so upload all 8. `-codex`, `-cursor`, and `-portable` sets exist for those uploaders.
- `job-hunter-PLUGIN-v6.1.0.zip`: the Claude Code plugin for `claude --plugin-dir`.

Releases v4.0.0 to v5.2.0 are the retired single-skill version; v6.1.0 is the first release of the family.

---

## How the scoring works

Every job posting gets scored across **five sub-scores** (1-5 each) with documented weights:

| Sub-score | Weight | What it measures |
|---|---|---|
| `cv_match` | **0.35** (heaviest) | How well your resume aligns with the posting's stated requirements |
| `comp_vs_target` | 0.25 | Listed comp vs your target band from your North-Star profile |
| `cultural_signals` | 0.20 | Mission, team size, hiring-page tone, glassdoor signal |
| `posting_legitimacy` | 0.20 | Ghost-job rubric (re-posts, vague specs, missing recruiter) |
| `red_flags_penalty` | **multiplier** | Pays-in-equity, asks-for-SSN-pre-offer, fee-to-apply, torpedoes the score |

A single severe red flag can take an otherwise-perfect posting from 5.0 to 1.0. Read the full rubrics in [job-search/references/posting-legitimacy-rubric.md](job-search/references/posting-legitimacy-rubric.md) and [job-search/references/match-quality-rubric.md](job-search/references/match-quality-rubric.md).

---

## What you get out of the box

Each member is a self-contained skill folder (`SKILL.md`, `scripts/`, `references/`, `tests/`, `evals/`). Scripts are standard-library Python with no network calls; DOCX and PDF reading (`career-profile`, `interview-prep`) uses `python-docx` / `pypdf` when installed.

```
.claude-plugin/                       # Claude Code marketplace + plugin manifest (lists the 8 dirs)
job-hunter/                           # orchestrator: routing + the shared .job-hunter/ workspace
  scripts/                            #   init_workspace, export_workspace, import_workspace
career-profile/scripts/               # init_profile (North-Star profile), parse_resume (DOCX/PDF/text)
job-search/scripts/                   # build_search_queries, expand_role_synonyms, normalize_salary,
                                      #   dedupe_postings, score_posting (deterministic 1-5)
resume-tailor/scripts/                # extract_ats_keywords, review_pass, verify_no_fabrication (the gate)
cover-letter/scripts/                 # draft_cover_letter, review_pass, verify_no_fabrication (same gate)
application-tracker/scripts/          # generate_tracker_html, draft_followup (check-in + thank-you drafts)
interview-prep/scripts/               # load_application, build_prep_pack, verify_no_fabrication (same gate)
outcome-learning/scripts/             # harvest_outcomes, propose_lessons
install/                              # one-shot installers (sh + ps1) and per-harness guides
tools/                                # routing, trigger, and outcome eval runners; repo guards
docs/                                 # continuity notes and eval evidence
```

No API keys required. No telemetry. No phoning home. Your `.job-hunter-profile.md` stays in **your** workspace.

---

## The learning loop (v5+)

Job-hunter keeps a small, per-user memory of decisions, outcomes, and confirmed lessons, all in plain-markdown files in your workspace, never sent anywhere.

| File (lives in `<your-workspace>/.job-hunter/`) | What it captures |
|---|---|
| `DECISIONS.md` | Per-session choices and why (skipped Acme because location, chose light tailoring for Beta) |
| `LESSONS.md` | Patterns about your preferences, **you confirm each one** before it's added |
| `OUTCOMES.md` | What actually happened (accepted, rejected after onsite, no response after 21 days) |
| `REJECTED_IDEAS.md` | Hard constraints, "no defense contractors", "no commission-only", agent never re-asks |

The cycle: as you apply and outcomes land, `outcome-learning/scripts/harvest_outcomes.py` looks for patterns. When ≥5 closed-loop outcomes exist, `outcome-learning/scripts/propose_lessons.py` translates the signals into suggested lessons. The agent surfaces each suggestion with evidence and asks **"want me to remember this?"**, only confirmed lessons get added to `LESSONS.md`.

**Six guardrails keep it honest:**
1. **Cold-start guard**: no lessons proposed until ≥5 closed-loop outcomes (no pattern detection from thin data)
2. **Opt-in only**: the agent never auto-writes lessons; every entry is user-confirmed
3. **Deterministic translation**: same input → same suggestion; reasons are anchored in evidence, not paraphrased
4. **Bounded influence**: lessons adjust how sub-scores are *graded* for you; the scoring weights in `job-search/scripts/score_posting.py` stay constant for all users
5. **Plain markdown**: every file is readable, editable, deletable by you, no black-box weights
6. **Local-only**: no telemetry, no phone-home, no upload

Delete `.job-hunter/` to start over. The skill re-initializes it on next run. See `outcome-learning/references/learning-loop-guide.md` for the full design and trust model.

---

## Tested

```bash
pip install pytest python-docx pypdf
python -m pytest --import-mode=importlib \
  job-hunter/tests career-profile/tests job-search/tests resume-tailor/tests \
  cover-letter/tests application-tracker/tests outcome-learning/tests \
  interview-prep/tests install tools
# 455 passed
```

CI ([.github/workflows/test.yml](.github/workflows/test.yml)) runs the same command on every push across Python 3.10/3.11/3.12 on Ubuntu, macOS, and Windows. Routing, trigger, and outcome eval results live in [docs/evals/](docs/evals/).

---

## FAQ

**I don't have a resume yet, can I still use this?**
Yes. If no resume is in your workspace, the skill will offer two paths: (1) point to one you have (file upload, path, or paste), or (2) walk you through a focused interview to draft a baseline `resume.md` from scratch, work history, accomplishments with numbers, skills, education, projects, and any non-traditional experience. Once the baseline is solid, the normal job-search and tailoring flow kicks in. The skill won't run the job search with no resume at all, because the scoring rubric and tailoring step both need one.

**My resume is thin or out of date.**
The skill will flag that before tailoring rather than producing 10 weak tailored versions of a weak base resume. It'll walk you through a short strengthen-the-baseline pass (asking for numbers on your accomplishments, surfacing skills you haven't listed, filling in dates) and then proceed.

**Will this submit applications for me?**
No. It produces the tailored resume + cover letter + application tracker. You submit. That's a deliberate boundary, auto-submission is a different trust model and out of scope for this skill.

**Does it send my resume or profile anywhere?**
No. Your resume, your `.job-hunter-profile.md`, and every tailored output live in your workspace. The skill has no telemetry, no phone-home, no required API keys, and no required network calls beyond what your agent already does to search the web. See [SECURITY.md](SECURITY.md) for the full trust model.

**Does it help me prepare for interviews?**
Yes, since 2026-10-18, through the separate `interview-prep` member. When an application reaches the interview stage, it reads the tracker entry plus the resume and cover letter you actually sent, and builds a prep pack for that stage (recruiter screen, hiring manager, skills test, panel, case, final round): likely questions mapped to your real examples in STAR form, honest answers for gaps (it will not script experience you do not have), questions to ask, and an optional mock interview. Every answer goes through the same `verify_no_fabrication.py` gate as your resume. It is for candidates; it does not write interview plans for hiring managers.

**Does the skill learn from my interactions?**
Yes, but entirely locally and opt-in. After 5+ closed-loop application outcomes, the skill surfaces patterns it noticed (e.g., "4 of 5 rejections cite comp, want me to remember this?") and asks you to confirm before adding any lesson. Confirmed lessons live in `<your-workspace>/.job-hunter/LESSONS.md` and adjust how sub-scores are graded for you. The scoring weights themselves stay constant. Nothing is uploaded or used for training. See the [learning loop](#the-learning-loop-v5) section above and `outcome-learning/references/learning-loop-guide.md`.

**Can I reset what the skill has learned about me?**
Yes, delete `<your-workspace>/.job-hunter/`. The next run will re-initialize empty templates. You can also edit any of the four files directly (LESSONS.md, DECISIONS.md, OUTCOMES.md, REJECTED_IDEAS.md) since they're plain markdown.

**Will the skill help me follow up on applications?**
Yes. The `application-tracker` member's `scripts/draft_followup.py` has two templates: `check_in` (7-10 days after applying with no response) and `thank_you` (24-48 hours after an interview). The skill scans your `tracker.json` for applications stale at `status=applied` for 7+ days and offers to draft polite check-in emails. It also drafts thank-you notes after you report an interview. **The skill never sends the email**, that's by design, and a load-bearing safety test enforces it. You copy-paste. See `application-tracker/references/followup-templates.md` for the patterns and cited sources.

**Can I move my job-hunter state to a different machine?**
Yes. The orchestrator's `job-hunter/scripts/export_workspace.py` bundles your profile + `.job-hunter/` learning loop + `tracker.json` (and optionally your tailored DOCX outputs) into a single zip. `job-hunter/scripts/import_workspace.py` restores them on a new machine. The export refuses to write to cloud-sync directories (Dropbox, OneDrive, iCloud) by default; pass `--allow-cloud` if you intentionally want that. Roundtrip preserves all files byte-for-byte. The import path-sanitizes the archive to reject any traversal payloads.

**Does this work for non-tech careers?**
Yes, this is the explicit design goal. `job-search/references/niche-boards-by-industry.md` includes verified entries for healthcare (Vivian Health, Nurse.com, Health eCareers, AlliedTravelCareers, state nursing board portals), trades (iHireConstruction, AllTrucking, IBEW/UA local hall search patterns, SkillBridge for military-to-trades), legal (LawCrossing, BCG Attorney Search, state bar career pages), education (HigherEdJobs, SchoolSpring, K12JobSpot), government (USAJobs, GovernmentJobs.com, NEOGOV-hosted municipal portals, state civil-service exams), and more. The agent picks the right tier-2 boards based on your role.

**I asked it to tighten my resume and it added things I didn't say. What went wrong?**
That's a real bug we fixed in v5.2.0, and the fix lives on in the `resume-tailor` member. Earlier versions of Phase 3 had truth-preservation listed as a Key Principle near the bottom of the SKILL.md, while the actual phase instructions said things like "push for numbers and outcomes." LLMs follow active instructions over passive guardrails, so the skill added quantification and content the user hadn't given it. v5.2.0 splits Phase 3 into two explicit modes: **Mode A (Tighten/Copyedit)** is a zero-fabrication contract that may not add numbers, change job titles, or pull content from external websites, and **Mode B (Tailor for a posting)** runs a mandatory verification gate (`resume-tailor/scripts/verify_no_fabrication.py`, bundled byte-identical in `cover-letter` and `interview-prep`) that surfaces every new claim before any output file is written. If you ever see the skill add something you didn't say, that's still a bug; please open an issue.

---

## Contributing

Issues, feature requests, and PRs welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for the workflow. If you found a security issue, see [SECURITY.md](SECURITY.md) for private disclosure.

If you use `job-hunter` to land a job, **open a Discussion and tell us**, that's the highest-signal feedback this project gets.

---

## License

[MIT](LICENSE). Use it commercially, fork it, rebrand it, ship it inside your product. No attribution required (but appreciated).

---

## Credits

- Competitive design review against [`santifer/career-ops`](https://github.com/santifer/career-ops) (MIT), `job-hunter` v4 folded in four of its ideas (1-5 scoring, legitimacy/match split, North-Star profile, multi-block tracker) and rejected five others where our design constraints differ.
- Built on the open [agentskills.io](https://agentskills.io) spec so it runs across Claude Code, Codex, OpenClaw, and any future compatible agent.
