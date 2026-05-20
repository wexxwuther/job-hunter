# Match Quality Rubric

How to evaluate how well a posting fits the user's resume and target, and when to flag or
drop a posting outright. This reference is loaded when the agent needs to make a judgment
call about a borderline posting — most of the routine extraction (title, company, salary,
location) doesn't need it.

For the orthogonal question — is this posting real and active? — see
`references/posting-legitimacy-rubric.md`. The two axes are scored independently and feed
`scripts/score_posting.py` as separate sub-scores.

## Red flag detection

Flag these to the user visibly. The user can still choose to pursue the role; the flag just
makes the decision informed instead of accidental.

Severity gradations matter for the `red_flags_penalty` field in `score_posting.py`:
- **Soft** red flags (vague description, reposted for months): penalty 0.0-0.2
- **Moderate** red flags (no salary in transparency state, staffing agency hiding employer):
  penalty 0.2-0.4
- **Severe** red flags (unpaid trial work, SSN pre-offer, pays only in equity,
  typosquatting): penalty 0.5-1.0 — these should torpedo the score

| Red flag | What it looks like | Severity | Why it matters |
|---|---|---|---|
| Vague description | "Looking for a rockstar to join our dynamic team" with no specific responsibilities | Soft | Often a placeholder posting, a staffing-agency lead capture, or a company that doesn't know what it wants |
| "Unlimited earning potential" / "be your own boss" | Commission-only or MLM-style language | Severe | Almost always commission-only sales or MLM; rarely a real W-2 role |
| Requirements wildly mismatched to title | "Entry-level" with 8+ years required; senior pay for junior responsibilities | Moderate | Misleading title, bait-and-switch, or salary compression |
| Reposted listings months old | Same posting visible on multiple boards for 60+ days, no edits | Soft-Moderate | Real role may have been filled; this is either a perpetual hiring pipeline (often body shops) or stale data. See posting-legitimacy-rubric.md for the structured version. |
| Staffing agency without named employer | "Confidential client" / "Fortune 500 in [city]" / "our client" | Moderate | You can't research the company before applying; often these are contract roles with significant markup |
| No salary range when state requires it | Posting from NYC, CA, CO, WA, IL, MD without a comp range | Moderate | Legal violation in jurisdictions with pay-transparency laws; often signals a company that doesn't follow basic compliance |
| Requires unpaid "trial work" | "Complete this small project before we interview" with no compensation | Severe | Free-labor harvesting; legitimate companies pay for trial work |
| Requests SSN / bank info pre-offer | Anywhere in the application flow before a written offer | Severe | Identity fraud risk; legitimate employers only need this after offer acceptance |
| Pays only in equity / crypto | No cash component | Severe | High-risk for living expenses; flag as a deal-breaker check |
| Domain typosquatting | Apply at `careers-stripe.com` instead of `stripe.com/jobs` | Severe | Phishing for resume/identity data |

Surface red flags inline in the posting card, never silently include or exclude. The HTML
tracker should render the penalty as part of the score breakdown so the user understands
*why* the global score is what it is.

## Match strength rubric

Rate each posting against the user's resume on the 1-5 `cv_match` axis. The mapping to the
legacy three-bucket tag (used in the tracker for at-a-glance scanning) is:

- **5.0:** Strong, 80%+ alignment
- **4.0-4.9:** Strong-to-Good, mid-80s alignment with one secondary gap
- **3.0-3.9:** Good, 50-80% alignment
- **2.0-2.9:** Possible, 30-50% alignment, stretch
- **1.0-1.9:** Below the bar — drop, don't include

### 5.0 — Strong (>=80% alignment)
- User has 80%+ of stated required skills with the same terminology or close synonyms
- Seniority level matches (e.g., "Senior" posting matches 5+ YOE on resume in similar role)
- Industry/domain matches (or user has clear transferable experience in the same problem space)
- Compensation range overlaps user's target
- User could apply with confidence; resume needs only light tailoring

### 3.0-3.9 — Good (50-80% alignment)
- User has most core requirements but missing 1-2 secondary skills
- Slight seniority gap (e.g., "Staff" posting; user is "Senior" with strong signals of staff-level scope)
- Adjacent industry (e.g., enterprise SaaS posting; user comes from B2B fintech — different verticals, same tooling)
- Comp range slightly off but negotiable
- Worth applying with a targeted tailored resume that emphasizes adjacency

### 2.0-2.9 — Possible (<50% alignment, or stretch)
- User has 30-50% of requirements, mostly transferable from related but distinct work
- Big seniority gap (under-leveled or over-leveled)
- Different industry, different tooling, but role title matches
- Worth considering if interested; needs a strong cover letter making the case
- Honest framing: "this is a stretch, here's what would have to land"

Do not invent a fourth bucket. If a posting is below 30% alignment, drop it from the list rather
than show it as "Possible" — that's noise, not opportunity.

## When to drop a posting

Drop, don't flag, when:
- The URL 404s or returns a generic "this job is no longer available" page
- The posting is clearly outside the user's stated location with no remote option
- The posting is a hard category mismatch (user is a backend engineer; posting is for a sales role at a tech company)
- The posting is an obvious scam (per red-flag list, Severe column)
- The `posting_legitimacy` score is 1.0-1.5 AND the user has 10+ other postings to choose
  from — there's no upside to spending tailoring time on a near-certain ghost

When dropping, still mention the count in the "Sources searched" summary so the user understands
the search wasn't padded — e.g., "LinkedIn returned 47 results, 8 dropped as expired/scam, 39 considered."

## Salary expectation vs. market sanity check

Before presenting results, run a quick sanity check against the user's stated comp floor:

- If the median posting salary is **>30% below** user's floor: flag that target may be above
  market for this role/location/seniority, suggest considering Director-level postings or
  different location/specialty.
- If the median posting salary is **>30% above** user's floor: flag that user may be
  under-pricing themselves, suggest negotiating from a higher anchor.
- If user's stated floor is "any": skip this check.

Use `scripts/normalize_salary.py` to parse posting salary strings into comparable numbers
before computing the median.

## Freshness threshold

Default freshness window: posts from the last 30 days. Older postings:
- 30-60 days: include but flag age visibly
- 60-90 days: include only if total result count is below 5; flag prominently
- 90+ days: drop unless the user explicitly asks for stale results

Many postings have no date; default to including them but mark the source as "date unknown" so
the user can decide. Aggregators sometimes strip dates that the original company page shows.

See `references/posting-legitimacy-rubric.md` for the more structured age-banded rating
that feeds the legitimacy sub-score.
