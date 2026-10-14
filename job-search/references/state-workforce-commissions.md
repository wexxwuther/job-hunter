# State Workforce Commission Registry (US)

For Tier 3 local searches. Every US state runs an official workforce/employment commission
website with current job listings. These catch government-administered postings plus many
private-sector roles that small employers list with the state.

When the user's target location is a US state, search the relevant entry below. The URLs are
the public job-search portals; the agency name in parentheses is the underlying authority.

**Last verified: 2026-10-13** (all 51 entries; HTTP check plus a real browser for blocked sites,
replacements confirmed against the agency's own .gov page). Re-check with
`python tools/check_state_portals.py` from the repo root. Prefer a state .gov host: a retired
non-.gov portal domain can lapse and be re-registered by anyone (employgeorgia.com became an
online-poker site after Georgia moved to WorkSource Georgia).

Format: `state | portal URL pattern | agency`

Search pattern across all of these: `site:[domain] "[role]"` works on most state portals.
If site: fails, use: `[state] state jobs "[role]"` and look for the .gov result.

| State | Portal | Agency |
|---|---|---|
| Alabama | alabamaworks.workforce.alabama.gov | AL Dept of Workforce (formerly Dept of Labor) |
| Alaska | alaskajobs.alaska.gov | AK Dept of Labor and Workforce Development |
| Arizona | arizonaatwork.com | AZ Dept of Economic Security |
| Arkansas | arjoblink.arkansas.gov | AR Division of Workforce Services |
| California | caljobs.ca.gov | CA Employment Development Department |
| Colorado | myservices.connectingcolorado.gov | CO Dept of Labor and Employment |
| Connecticut | cthires.com | CT Dept of Labor |
| Delaware | joblink.delaware.gov | DE Dept of Labor |
| Florida | employflorida.com | FL Dept of Economic Opportunity |
| Georgia | worksourcegaportal.com | WorkSource Georgia, Technical College System of GA (replaced EmployGeorgia 2023) |
| Hawaii | hirenethawaii.com | HI Workforce Development Division |
| Idaho | idahoworks.gov | ID Dept of Labor |
| Illinois | illinoisjoblink.illinois.gov | IL Dept of Employment Security |
| Indiana | indianacareerconnect.com | IN Dept of Workforce Development |
| Iowa | workforce.iowa.gov | IA Workforce Development |
| Kansas | kansasworks.com | KS Dept of Commerce |
| Kentucky | kyjobs.usnlx.com | KY Career Center (National Labor Exchange portal, linked from kcc.ky.gov) |
| Louisiana | louisianaworks.net | LA Workforce Commission (HiRE system) |
| Maine | joblink.maine.gov | ME Dept of Labor |
| Maryland | mwejobs.maryland.gov | MD Workforce Exchange |
| Massachusetts | jobquest.mass.gov | MassHire Department of Career Services (MassHire JobQuest) |
| Michigan | mitalent.org | MI Talent Investment Agency |
| Minnesota | careerforce.mn.gov | MN Dept of Employment and Economic Development (CareerForce) |
| Mississippi | mdes.ms.gov | MS Dept of Employment Security |
| Missouri | jobs.mo.gov | MO Office of Workforce Development |
| Montana | montanaworks.gov | MT Dept of Labor and Industry |
| Nebraska | neworks.nebraska.gov | NE Dept of Labor |
| Nevada | employnv.gov | NV Dept of Employment, Training and Rehabilitation (EmployNV) |
| New Hampshire | nhworksjobmatch.nhes.nh.gov | NH Employment Security (NHWorks Job Match) |
| New Jersey | mycareer.nj.gov | NJ Dept of Labor and Workforce Development (My Career NJ) |
| New Mexico | jobs.dws.nm.gov | NM Dept of Workforce Solutions |
| New York | newyork.usnlx.com | NY Dept of Labor (NYS Job Bank on National Labor Exchange; official alias myjobs.ny.gov failed TLS on 2026-10-13) |
| North Carolina | www.ncworks.gov | NC Dept of Commerce |
| North Dakota | jobsnd.com | ND Job Service |
| Ohio | ohiomeansjobs.ohio.gov | OH Dept of Job and Family Services |
| Oklahoma | employoklahoma.gov | OK Employment Security Commission (replaced OKJobMatch 2025) |
| Oregon | imatchskills.org | OR Employment Department (iMatchSkills / WorkSource Oregon) |
| Pennsylvania | www.pacareerlink.pa.gov | PA Dept of Labor and Industry (PA CareerLink) |
| Rhode Island | www.employri.org | RI Dept of Labor and Training (EmployRI, linked from dlt.ri.gov) |
| South Carolina | jobs.scworks.org | SC Dept of Employment and Workforce |
| South Dakota | sdworks.sd.gov | SD Dept of Labor and Regulation |
| Tennessee | jobs4tn.gov | TN Dept of Labor and Workforce Development |
| Texas | workintexas.com | TX Workforce Commission |
| Utah | jobs.utah.gov | UT Dept of Workforce Services |
| Vermont | vermontjoblink.com | VT Dept of Labor |
| Virginia | vec.virginia.gov | VA Employment Commission |
| Washington | worksourcewa.com | WA Employment Security Department |
| West Virginia | workforcewv.org | WV WORKFORCE |
| Wisconsin | jobcenterofwisconsin.com | WI Dept of Workforce Development |
| Wyoming | hire.wyo.gov | WY Dept of Workforce Services |
| DC | dcnetworks.org | DC Dept of Employment Services |

## How to verify a portal is still live

State agencies rename and redomain frequently. Before quoting a result to the user, do a quick
sanity check: search `[state] workforce commission jobs` and confirm the official .gov result
points to the same portal. If the portal in this table 404s, the registry needs an update,
flag this in `docs/continuity/maintenance.md`.

## Beyond the state portal

Most states also have:
- **City-level portals** for state capitals and major metros (e.g., `austincityjobs.org`,
  `jobs.nyc.gov`, `jobsapps.lacity.org`)
- **County-level portals** for large counties (e.g., `mocojobs.com` for Montgomery County MD)
- **University system career pages** for state university systems (e.g., `careers.utexas.edu`,
  `jobs.universityofcalifornia.edu`)

Search pattern: `[city] OR [county] government jobs` and `[state] university system careers`.
