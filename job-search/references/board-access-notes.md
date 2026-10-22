# Board Access Notes

What actually worked when fetching postings during a live search (a construction project
manager in Benton Harbor, MI, 2026-10-21). Sites change their blocking and filters often;
treat these as current observations, not guarantees.

## LinkedIn

- The logged-out (guest) job search did not apply the salary filter (`f_SB2`) or the remote
  filter (`f_WT`): results still included postings below the pay floor or on-site. Read pay
  and work arrangement from each posting instead of trusting the filter.
- A signed-in search applies the filters, but use the user's own signed-in browser only with
  their permission. Never ask for or type their password.

## Indeed, Glassdoor, ZipRecruiter, SimplyHired

- Indeed, Glassdoor and ZipRecruiter usually block automated fetches (HTTP 403 or 401). Keep
  the link for the user and find the same job elsewhere (employer site, ATS feed below).
- SimplyHired search pages may block too, but its individual posting pages usually load and
  often carry the employer's posted pay range.

## Employer applicant-tracking systems (most reliable)

Employer ATS job feeds are public and are the best way to confirm a posting is still open and
read its pay:

- Workday: the career site's `cxs` JSON endpoint, the URL the site itself calls
  (`https://<tenant>.<wdN>.myworkdayjobs.com/wday/cxs/<tenant>/<site>/jobs`).
- Greenhouse (`boards-api.greenhouse.io/v1/boards/<board>/jobs?pay_transparency=true`) and
  Ashby (`api.ashbyhq.com/posting-api/job-board/<board>?includeCompensation=true`): public
  job-board APIs; those parameters add the posted pay range.
- Lever (`api.lever.co/v0/postings/<company>?mode=json`): public postings API; pay appears
  only when the employer fills it in.

When a posting's apply link goes to one of these, check the feed before scoring
`posting_legitimacy`.

## Labeling pay

A pay range seen only on an aggregator (not on the employer's posting or ATS feed) may be an
estimate or out of date. Label it with its source, in the form "<range> (source:
SimplyHired)", and score `comp_vs_target` with that caveat.
