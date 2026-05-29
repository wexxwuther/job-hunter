---
name: job-search
description: Finds, expands, normalizes, deduplicates, and deterministically scores real job postings. Use when the user wants to find jobs, search for openings or positions or work, look for roles near them or remote, find companies hiring in a field, score or rank job postings, find roles matching their resume, detect ghost jobs or fake postings, or sanity-check whether a posting is worth applying to. Searches across major boards (LinkedIn, Indeed, Glassdoor, ZipRecruiter), industry niche boards, 50-state workforce commissions and local sources, and direct company career pages, then scores each posting on five sub-scores (cv_match, comp_vs_target, cultural_signals, posting_legitimacy, red_flags_penalty). Do not use for tailoring a resume to a posting (use resume-tailor), setting up a profile or parsing a resume (use career-profile), tracking applications or follow-ups (use application-tracker), or learning from outcomes (use outcome-learning).
license: MIT
compatibility: Cross-vendor (agentskills.io open standard) + cross-OS (Windows, macOS, Linux). Installs across Claude Code, OpenAI Codex, OpenClaw, and Hermes Agent. Works standalone or as the search member of the job-hunter family; reads the shared .job-hunter/ workspace if present and degrades gracefully if absent.
metadata:
  spec_version: "agentskills.io (living spec; tracked 2026-05-28)"
  family: "job-hunter"
  family_role: "search"
allowed-tools: Read Write Edit Bash(python:*) Glob Grep WebSearch WebFetch
---

# job-search (family search member)

Find real job openings across every tier that matters, then score each one with
a deterministic rubric so the user has a defensible numeric reason to pursue or
skip — not a hand-waved tag. This is the **search** member of the job-hunter
family.

## When to use this skill

Use this skill when the user wants to **find** or **score** job postings:

- "Find me senior backend engineer roles in Seattle, $180k+"
- "What jobs match my resume?"
- "Look for openings near me, I'm a marketing manager"
- "Search local jobs in Austin for a data analyst"
- "Find companies hiring software engineers in Boston"
- "Score this posting for me" / "Is this posting legit or a ghost job?"
- "Find remote DevOps jobs that pay at least $150k"

Do **not** use this skill for tailoring or optimizing a resume against a posting
(use **resume-tailor**), setting up the North-Star profile or parsing a resume
(use **career-profile**), tracking applications or drafting follow-ups (use
**application-tracker**), or harvesting lessons from outcomes (use
**outcome-learning**). For an end-to-end hunt that spans several of these, the
**job-hunter** orchestrator routes across the family.

## Inputs (workspace contract)

This member reads upstream artifacts **if present** and **degrades gracefully**
if absent, so it also works standalone:

- **`.job-hunter-profile.md`** (North-Star profile, produced by career-profile):
  if present, run the profile's deal-breakers, company-size, and
  mission-vs-comp answers into the scoring below. **If absent**, score on the
  explicit search criteria the user gives you (role, location, comp). Do not
  fabricate a profile.
- **`.job-hunter/REJECTED_IDEAS.md`** and **`.job-hunter/LESSONS.md`** (if a
  workspace exists): treat REJECTED_IDEAS entries as hard filters and let
  confirmed LESSONS adjust how you *grade* the five sub-scores. Lessons never
  change the *weights* in `score_posting.py` — those stay constant.

Produces a scored **`postings.json`** per the family workspace contract
(`cv_match`, `comp_vs_target`, `cultural_signals`, `posting_legitimacy`,
`red_flags_penalty`, plus `weighted_global` and `recommendation`), which
resume-tailor and application-tracker consume downstream.

## Phase: Search for Jobs (4 tiers)

Use web search to cast the widest possible net across major boards, niche sites,
local sources, and direct company pages. Many of the best opportunities,
especially at smaller or regional companies, never appear on LinkedIn or Indeed.
A thorough search covers all four tiers below.

**Build the query set first.** Run `scripts/build_search_queries.py` to generate
a deterministic list of queries across all four tiers given the user's role,
location, industry, and any target companies:

```
python scripts/build_search_queries.py --role "data engineer" --location "Austin, TX" --industry tech
```

This avoids ad-hoc query construction and ensures each tier gets the right
number of distinct queries. Use the output as your search plan; when results are
thin, expand with `scripts/expand_role_synonyms.py "<role>"` (covers 80+ roles
with synonyms and adjacent titles) and re-run the query builder against each
synonym.

**Tier 1 — Major job boards (always):**
LinkedIn, Indeed, Glassdoor, ZipRecruiter. These have the most volume. Always
include a broad non-site-specific query (e.g.,
`"[role]" "[location]" job posting 2026`) as a fallback for when `site:` queries
are blocked.

**Tier 2 — Industry and niche boards:**
The board to use depends on the user's industry. See
[`references/niche-boards-by-industry.md`](references/niche-boards-by-industry.md)
for the full registry across tech, healthcare, finance, marketing/media,
government, nonprofits, education, trades, and legal. Only search the boards
relevant to the user's field; don't pad with every board.

**Tier 3 — Local and regional sources:**
This tier catches jobs that never reach national boards. Includes state
workforce commission portals (see
[`references/state-workforce-commissions.md`](references/state-workforce-commissions.md)
for the 50-state + DC registry), city and county job boards, local newspapers
and business journals, chambers of commerce, regional industry groups,
Craigslist, and university career centers. The query builder generates a starter
set for each of these for the user's specific location.

**Tier 4 — Direct company career pages:**
Some of the best matches come from going straight to employers. If the user has
target companies in mind, pass them via `--companies`. Otherwise search
`largest employers [city]` or `top [industry] companies [city]` and check their
career pages individually.

**General search principles:**
- Run multiple targeted searches across all relevant tiers rather than one broad one.
- Aim for **10+ unique postings** total, ideally from a mix of sources (not all LinkedIn).
- **Fallbacks:** If site-specific searches return thin results (some sites block
  `site:` queries), switch to broader queries. If a whole tier is empty, try
  harder on the others and tell the user what you tried.
- **Freshness:** Prefer postings from the last 30 days. If a result looks stale
  (no date, or clearly months old), skip it unless pickings are slim, and flag
  the age if you include it.
- **Deduplication:** The same job often appears on multiple boards. After
  collection, run `scripts/dedupe_postings.py` over the gathered postings to
  collapse duplicates by company + title + location. The script prefers the most
  direct URL (company career page > aggregator > LinkedIn-style mirror) and
  preserves the other sources under `also_seen_on` so the user can see breadth
  without seeing repeats.

**For each posting, extract:** job title; company name; a one-line company blurb
(industry, approximate size, anything notable); location (or remote status);
salary range (if listed); date posted (if available); **source** (where it was
found, e.g., "LinkedIn", "Austin Business Journal", "Company career page", "Texas
Workforce Commission"); direct URL; and a 2-3 sentence summary of the role and
key requirements.

**Two orthogonal axes — score them separately:**

- **Match quality:** does the role fit the user's background? Full rubric
  (red-flag catalog with severity gradations, 1-5 cv_match criteria, when to drop
  a posting vs flag it, salary-vs-market sanity check) in
  [`references/match-quality-rubric.md`](references/match-quality-rubric.md). Use
  `scripts/normalize_salary.py` to parse posting salary strings into comparable
  numbers before filtering against the user's comp floor or computing market
  medians.
- **Posting legitimacy:** is the posting real and active? Three-tier confidence
  scale (High Confidence / Proceed with Caution / Suspicious) with signals for
  age, repost patterns, apply-button quality, employer disclosure, salary
  transparency, and company activity. See
  [`references/posting-legitimacy-rubric.md`](references/posting-legitimacy-rubric.md).
  This is the ghost-job axis; treat it as independent from match quality so a 5/5
  match on a likely-fake posting still scores low.

Surface red flags inline in each posting card and feed severe red flags (SSN
pre-offer, pays only in equity, typosquatting) into the `red_flags_penalty`
multiplier rather than just displaying them.

## Phase 2.5: Deterministic scoring

After triaging each posting, fill in five 1-5 sub-scores (`cv_match`,
`comp_vs_target`, `cultural_signals`, `posting_legitimacy`, plus a 0-1
`red_flags_penalty` if applicable) and run `scripts/score_posting.py` to produce
a weighted global score and a recommendation
(`apply` / `apply_if_specific_reason` / `skip`):

```
python scripts/score_posting.py --sub-scores '{"cv_match": 4.5, "comp_vs_target": 4.5, "cultural_signals": 4.0, "posting_legitimacy": 5.0, "red_flags_penalty": 0.0}'
```

or batch via `--sub-scores-file scored.json` (a JSON array of sub-score objects).

The five sub-scores:
- **`cv_match`** — how well the posting fits the user's resume/profile. This is
  the **heaviest weight** because it is the single most predictive signal of
  whether the application reaches a human.
- **`comp_vs_target`** — compensation vs the user's target (use
  `normalize_salary.py` first).
- **`cultural_signals`** — culture/values fit signals.
- **`posting_legitimacy`** — is it a real, active opening (the ghost-job axis).
- **`red_flags_penalty`** — a 0-1 multiplier applied to the weighted additive
  score. A single severe red flag (e.g., pays only in equity at 0.5) can torpedo
  an otherwise strong score. This is the discipline that prevents "everything is
  a 4" inflation; red flags **multiply, they do not subtract.**

The weights are documented inline in the script and held constant. Recommendation
bands: `>= 4.0` -> `apply`; `3.5-3.99` -> `apply_if_specific_reason`; `< 3.5` ->
`skip`. See `tests/test_score_posting.py` for the load-bearing semantic tests
around weight intent (cv_match heaviest, red-flag-torpedoes, and the
career-ops Block G thresholds).

Write the scored postings to `postings.json` (the family workspace artifact) so
downstream members can consume them. Each posting carries the five sub-scores
plus `weighted_global` and `recommendation`.

## Output: presenting links

Job links need to be clickable in the user's environment, and most chat UIs do
not auto-link bare URLs inside long responses. Present the postings as a rendered
HTML file saved to the workspace folder so every link is a real anchor. Bare-URL
text in chat is a fallback only if HTML output is unavailable. The HTML should
show each job as a card/row with title (linked), company + blurb, location,
salary, date, **source**, summary, a recommendation/score badge, and any red
flags; offer filters by recommendation bucket and source type; sort by
`weighted_global` descending by default; include a count header; and include a
"Sources searched" summary at the bottom (even tiers that returned nothing) so
the user sees the breadth of the search.

## Handling thin or suspicious results

- **Few results:** don't present 3 mediocre results and call it done. Try
  alternative titles via `expand_role_synonyms.py`, broaden the location, or
  check different boards. Tell the user what you tried.
- **Can't fetch a posting page:** some sites block scraping. Include the link so
  the user can read it, and note that scoring is best-effort without the full JD.
- **Suspicious posting:** rate it low on `posting_legitimacy` (independent of
  match quality), cite the specific ghost-job signals, and recommend `skip` /
  proceed-with-caution rather than padding the result set.
