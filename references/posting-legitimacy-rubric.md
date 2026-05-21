# Posting Legitimacy Rubric

How to assess whether a job posting is real and active, independent of how well the role
matches the user's background. This axis exists because match quality and posting legitimacy
are two different failure modes: a perfect-match posting that's a ghost listing wastes the
user's tailoring effort, and a moderate-match posting that's a high-confidence real opening
is often the better use of their day.

Career-ops calls this "Block G" and scores it separately from the 1-5 match scale. Independent
2025 estimates put ghost-job prevalence on LinkedIn at ~27% (ResumeUp.AI analysis) and the
broader online job market at 18-30% (Greenhouse 2025; Congressional Research Service report
IF12977). Treating legitimacy as a sub-score (not a soft red flag) is the discipline that
keeps the user's tailoring time honest.

## Three-tier confidence scale

Rate each posting once, then feed the rating into `scripts/score_posting.py` as the
`posting_legitimacy` sub-score on the same 1-5 scale used by the other axes.

### High Confidence (rate 4.5-5.0)

The posting is almost certainly a real, active, fillable opening:

- Posted within the last 30 days, with a visible date
- Named employer (not "confidential client" or "Fortune 500 in X city")
- Apply button leads to the company's actual ATS (Greenhouse, Ashby, Lever, Workday) or
  career page, not a third-party form harvesting resumes
- Job description is specific: lists day-to-day responsibilities, named team or product,
  tooling stack with versions or specifics, not just a wishlist of buzzwords
- Salary range is visible (or the role is outside a pay-transparency jurisdiction)
- The company shows recent product launches, blog posts, or other signs of activity
- No recent layoff announcements or hiring freezes at the company

### Proceed with Caution (rate 2.5-4.0)

Mixed signals, the posting may be real but has indicators that warrant a closer look before
spending tailoring effort:

- Posted 30-60 days ago, or no date visible at all
- Apply button works but routes through a generic job-board form, not the company's ATS
- Job description is generic enough that you can't pin down what the team actually does
- Salary missing in a jurisdiction that requires pay transparency (NYC, CA, CO, WA, IL, MD)
- Same posting visible on multiple boards with identical wording (reposted not refreshed)
- Recent layoff announcements at the company (within 90 days), but the posting is for an
  unrelated team or function
- Company name is real but the role title doesn't match anything on their actual careers page
- Glassdoor or LinkedIn data shows the company has had this same role open for 6+ months
  without movement

### Suspicious (rate 1.0-2.5)

Multiple signals point at this not being a real, active opening. Recommend the user skip
unless they have specific reason to pursue:

- Posted 60+ days ago AND no visible refresh, but appearing as "new" on aggregators
- Same JD reposted three or more times in a 90-day window with no visible changes
- Apply button broken, redirects, or asks for SSN/bank info pre-offer
- "Confidential client" / "our client" with no named employer (staffing agency, no
  recourse, no research possible)
- Description boilerplate so generic it could apply to any company in any industry
- Company has had a hiring freeze announced AND this role exists on their careers page,
  pipeline-builder, not a real opening
- Recent layoff news at the company AND the role is on the affected team
- Domain typosquatting (apply at `careers-stripe.com` instead of `stripe.com/jobs`)
- Multi-level marketing or "be your own boss" framing
- Commission-only with "unlimited earning potential" language

## Signals catalog

When in doubt, count the signals. A posting with one Suspicious signal might still be fine;
a posting with three is almost certainly not worth tailoring for.

### Age signals

- **<30 days, dated:** legitimate-by-default
- **30-60 days:** caution; include but flag age in the tracker
- **60-90 days, no refresh:** likely stale; verify with a fresh job-board search before
  tailoring
- **90+ days:** drop unless the user explicitly asks for stale results

### Repost signals

- **Same JD, multiple boards, same week:** normal, aggregators syndicate
- **Same JD, multiple boards, same 30-day window, different post dates:** likely a real
  recurring need; legitimate
- **Same JD, no edits, reposted month after month:** ghost-job pattern; treat as pipeline-
  building, not a real opening
- **Same role, same company, three+ openings of identical title over 6 months:** body shop
  or churn signal; legitimate role but worth surfacing

### Apply-button signals

- **Direct ATS (Greenhouse, Ashby, Lever, Workday, Teamtailor):** legitimate-by-default
- **Company's own careers page form:** legitimate-by-default
- **Generic third-party form (Indeed Apply, ZipRecruiter Quick Apply):** ok, but verify the
  posting exists on the company's own careers page before tailoring
- **Email-only apply ("send your resume to careers@company.com"):** caution for any
  established company; legitimate for small businesses
- **Asks for SSN, bank info, or "trial work" before written offer:** suspicious; drop

### Employer-disclosure signals

- **Named company, real domain:** legitimate-by-default
- **"Our client" with industry/size hint:** staffing agency, legitimate but adds a
  middleman; comp visibility usually lower
- **"Confidential employer":** caution; the user can't research the company before
  spending tailoring effort
- **No company name anywhere on the posting:** suspicious

### Salary-transparency signals

- **Range visible in pay-transparency jurisdiction:** legitimate-by-default
- **Range missing in pay-transparency jurisdiction (NYC, CA, CO, WA, IL, MD):** caution;
  company may not be following compliance, which is a soft red flag for ops maturity
- **Range visible outside pay-transparency jurisdictions:** legitimate; voluntarily
  transparent companies often score higher on cultural fit too
- **"Competitive" or "commensurate with experience":** ok in non-transparency states;
  caution in transparency states

### Company-activity signals (corroborating, not deciding)

- **Recent product launches, blog posts, or press in last 90 days:** corroborates legitimacy
- **Layoff announcement in last 90 days affecting the posted team:** suspicious, even if
  the role is technically open, it may be a backfill that gets cancelled
- **Layoff announcement in last 90 days NOT affecting the posted team:** caution; verify
  the role is on a still-funded team
- **Company hasn't shipped or announced anything in 6+ months:** caution; may be in
  wind-down

## How to feed the rating to score_posting.py

The 1-5 rating maps directly to the `posting_legitimacy` sub-score field:

```json
{
  "cv_match": 4.0,
  "comp_vs_target": 4.5,
  "cultural_signals": 4.0,
  "posting_legitimacy": 2.0,        // Suspicious tier
  "red_flags_penalty": 0.0
}
```

Then `python scripts/score_posting.py --sub-scores '...'` computes the weighted global. A
posting with `posting_legitimacy=1.0` and everything else at 5.0 still scores well below 4.0
on the global, by design. That's the discipline.

## What this rubric does NOT cover

- **Match quality** (does the role fit the user's background?), see
  `references/match-quality-rubric.md`
- **Red flags that disqualify entirely** (pays in equity, requests SSN pre-offer, etc.),
  see `references/match-quality-rubric.md` red-flag catalog; severe red flags should
  populate `red_flags_penalty`, not the legitimacy score
- **Cultural fit** (stability, remote policy, mission alignment), separate sub-score

Three separate axes, three separate ratings. Aggregating them upfront destroys the signal
that lets the user understand *why* they should or shouldn't apply.
