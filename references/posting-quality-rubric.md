# Posting Quality Rubric (deprecated stub)

This file was split in iteration v4 into two orthogonal axes:

- **`references/match-quality-rubric.md`** — how well does the posting fit the user's resume?
  Red-flag catalog with severity gradations, 1-5 cv_match rubric, drop rules, salary sanity
  check, freshness threshold.
- **`references/posting-legitimacy-rubric.md`** — is the posting real and active? Three-tier
  confidence scale (High Confidence / Proceed with Caution / Suspicious), signals catalog
  for age, repost patterns, apply-button, employer-disclosure, salary-transparency, and
  company-activity.

The split exists because these two questions have different answers and different
consequences. A perfect-match posting that's a ghost listing wastes your tailoring time; a
moderate-match posting that's a high-confidence real opening is often the better use of your
day. See career-ops Block G for the empirical validation of this separation; independent 2025
estimates put ghost-job prevalence on LinkedIn at ~27% (ResumeUp.AI analysis) and the broader
online job market at 18-30% (Greenhouse 2025; Congressional Research Service report IF12977).

Both rubrics feed `scripts/score_posting.py` as separate sub-scores (`cv_match` and
`posting_legitimacy`). Severe red flags feed the multiplicative `red_flags_penalty` field.

This stub will be removed in a future iteration once nothing references it.
