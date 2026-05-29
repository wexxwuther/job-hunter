#!/usr/bin/env python3
"""
build_search_queries.py

Build a set of web-search query strings across the four tiers of the job-hunter workflow
(major boards, niche boards, local sources, direct company pages) given a role, location,
and optional industry/company list.

Usage:
    python build_search_queries.py --role "data engineer" --location "Austin, TX"
    python build_search_queries.py --role "PM" --location "Seattle" --industry tech --companies stripe,anthropic
    python build_search_queries.py --role "nurse" --location "Phoenix, AZ" --industry healthcare --json

Outputs a numbered list of search queries (or JSON). The agent runs the queries with
WebSearch / Bash(curl) / its preferred search tool; this script is purely query generation,
so it works offline and is deterministic.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from typing import Iterable


# Tier 1 - major boards (apply to virtually all searches)
TIER_1_BOARDS = [
    ("LinkedIn", "linkedin.com/jobs"),
    ("Indeed", "indeed.com/viewjob"),
    ("Glassdoor", "glassdoor.com/job"),
    ("ZipRecruiter", "ziprecruiter.com/jobs"),
]

# Tier 2 - niche boards by industry. Mirrors references/niche-boards-by-industry.md
TIER_2_BY_INDUSTRY: dict[str, list[tuple[str, str]]] = {
    "tech": [
        ("Dice", "dice.com"),
        ("Built In", "builtin.com"),
        ("Wellfound", "wellfound.com"),
        ("We Work Remotely", "weworkremotely.com"),
        ("Remote OK", "remoteok.com"),
        ("HN Who's Hiring", "news.ycombinator.com"),
    ],
    "healthcare": [
        ("Health eCareers", "healthecareers.com"),
        ("PracticeLink", "practicelink.com"),
        ("Nurse.com", "nurse.com"),
        ("HealthcareJobSite", "healthcarejobsite.com"),
    ],
    "finance": [
        ("eFinancialCareers", "efinancialcareers.com"),
        ("Wall Street Oasis", "wallstreetoasis.com"),
        ("One Wire", "onewire.com"),
    ],
    "marketing": [
        ("Mediabistro", "mediabistro.com"),
        ("CreativeCircle", "creativecircle.com"),
        ("AdAge Job Board", "adage.com/jobs"),
    ],
    "government": [
        ("USAJobs", "usajobs.gov"),
        ("GovernmentJobs.com", "governmentjobs.com"),
    ],
    "nonprofit": [
        ("Idealist", "idealist.org"),
        ("Foundation List", "foundationlist.org"),
    ],
    "education": [
        ("HigherEdJobs", "higheredjobs.com"),
        ("SchoolSpring", "schoolspring.com"),
        ("Chronicle Vitae", "chroniclevitae.com"),
    ],
    "trades": [
        ("iHireConstruction", "ihireconstruction.com"),
        ("AllTrucking", "alltrucking.com"),
        ("ManufacturingJobs", "manufacturingjobs.com"),
    ],
    "legal": [
        ("LawCrossing", "lawcrossing.com"),
        ("Law360 Jobs", "jobs.law360.com"),
    ],
}

# Tier 3 - state portal templates. Full registry in references/state-workforce-commissions.md.
# Only a handful here; the script falls back to a generic query if the state isn't listed.
STATE_PORTALS: dict[str, str] = {
    "tx": "workintexas.com",
    "ca": "caljobs.ca.gov",
    "ny": "jobzone.ny.gov",
    "fl": "employflorida.com",
    "il": "illinoisjoblink.illinois.gov",
    "wa": "worksourcewa.com",
    "ma": "masshirecjc.com",
    "pa": "jobgateway.pa.gov",
    "ga": "employgeorgia.com",
    "co": "connectingcolorado.com",
    "az": "arizonaatwork.com",
    "or": "oregonjobsplus.com",
    "mi": "mitalent.org",
    "nc": "ncworks.gov",
    "va": "vec.virginia.gov",
}


@dataclass
class QuerySet:
    tier_1: list[str] = field(default_factory=list)
    tier_2: list[str] = field(default_factory=list)
    tier_3: list[str] = field(default_factory=list)
    tier_4: list[str] = field(default_factory=list)
    role_synonyms: list[str] = field(default_factory=list)

    def all(self) -> list[str]:
        return self.tier_1 + self.tier_2 + self.tier_3 + self.tier_4

    def to_dict(self) -> dict[str, list[str]]:
        return {
            "tier_1_major_boards": self.tier_1,
            "tier_2_niche_boards": self.tier_2,
            "tier_3_local_sources": self.tier_3,
            "tier_4_company_pages": self.tier_4,
            "role_synonym_suggestions": self.role_synonyms,
        }


def _quote(s: str) -> str:
    s = s.strip()
    if not s:
        return s
    return f'"{s}"' if " " in s else s


def _extract_state_code(location: str) -> str | None:
    parts = [p.strip() for p in location.split(",")]
    for part in parts:
        p = part.strip().lower()
        if len(p) == 2 and p.isalpha():
            return p
    location_lower = location.lower()
    state_names = {
        "texas": "tx", "california": "ca", "new york": "ny", "florida": "fl",
        "illinois": "il", "washington": "wa", "massachusetts": "ma",
        "pennsylvania": "pa", "georgia": "ga", "colorado": "co", "arizona": "az",
        "oregon": "or", "michigan": "mi", "north carolina": "nc", "virginia": "va",
    }
    for name, code in state_names.items():
        if name in location_lower:
            return code
    return None


def _extract_city(location: str) -> str:
    return location.split(",")[0].strip()


def build_queries(
    role: str,
    location: str,
    industry: str | None = None,
    companies: Iterable[str] | None = None,
) -> QuerySet:
    if not role.strip():
        raise ValueError("role is required and must be non-empty")
    if not location.strip():
        raise ValueError("location is required and must be non-empty")

    qs = QuerySet()
    role_q = _quote(role)
    loc_q = _quote(location)
    city = _extract_city(location)
    city_q = _quote(city)

    for name, domain in TIER_1_BOARDS:
        qs.tier_1.append(f"site:{domain} {role_q} {loc_q}")
    qs.tier_1.append(f"{role_q} {loc_q} job posting 2026")

    industry_key = (industry or "").strip().lower() or None
    if industry_key and industry_key in TIER_2_BY_INDUSTRY:
        for name, domain in TIER_2_BY_INDUSTRY[industry_key]:
            qs.tier_2.append(f"site:{domain} {role_q} {loc_q}")
    elif industry_key:
        qs.tier_2.append(f"{_quote(industry)} job board {role_q} {loc_q}")
    else:
        qs.tier_2.append(f"specialty job board {role_q} {loc_q}")

    state = _extract_state_code(location)
    if state and state in STATE_PORTALS:
        qs.tier_3.append(f"site:{STATE_PORTALS[state]} {role_q}")
    elif state:
        qs.tier_3.append(f"{state.upper()} workforce commission jobs {role_q}")
    else:
        qs.tier_3.append(f"{loc_q} state workforce commission jobs {role_q}")

    qs.tier_3.extend([
        f"{city_q} government jobs {role_q}",
        f"{city_q} business journal jobs {role_q}",
        f"{city_q} chamber of commerce job board",
        f"site:craigslist.org {city_q} {role_q}",
        f"{city_q} university career center {role_q}",
    ])

    if companies:
        for c in companies:
            c = c.strip()
            if not c:
                continue
            cq = _quote(c)
            qs.tier_4.append(f"{cq} careers {role_q}")
            qs.tier_4.append(f"site:{c.lower()}.com careers {role_q}")
    else:
        qs.tier_4.extend([
            f"largest employers {city_q}",
            f"top employers {city_q} {_quote(industry) if industry else ''}".strip(),
        ])

    qs.role_synonyms = _suggest_synonyms(role)

    return qs


def _suggest_synonyms(role: str) -> list[str]:
    role_low = role.lower().strip()
    synonyms_table = {
        "data engineer": ["analytics engineer", "data platform engineer", "ETL developer"],
        "software engineer": ["software developer", "SWE", "backend engineer"],
        "product manager": ["PM", "product owner", "technical product manager"],
        "data scientist": ["ML engineer", "applied scientist", "analytics scientist"],
        "devops engineer": ["SRE", "platform engineer", "infrastructure engineer"],
        "frontend engineer": ["front-end developer", "UI engineer", "React developer"],
        "designer": ["UX designer", "product designer", "UI designer"],
        "marketing manager": ["growth manager", "demand gen manager"],
    }
    return synonyms_table.get(role_low, [])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role", required=True, help='Job title or keyword (e.g., "data engineer")')
    parser.add_argument("--location", required=True, help='Location (e.g., "Austin, TX" or "remote")')
    parser.add_argument("--industry", default=None,
                        help="Optional industry: tech, healthcare, finance, marketing, government, "
                             "nonprofit, education, trades, legal")
    parser.add_argument("--companies", default="",
                        help="Optional comma-separated target companies (e.g., 'stripe,anthropic')")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    args = parser.parse_args(argv)

    companies = [c.strip() for c in args.companies.split(",") if c.strip()] if args.companies else []

    try:
        qs = build_queries(args.role, args.location, args.industry, companies)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(qs.to_dict(), indent=2))
        return 0

    def emit_tier(title: str, qs_list: list[str]) -> None:
        if not qs_list:
            return
        print(f"\n## {title}")
        for i, q in enumerate(qs_list, 1):
            print(f"  {i}. {q}")

    emit_tier("Tier 1: Major boards", qs.tier_1)
    emit_tier("Tier 2: Niche boards", qs.tier_2)
    emit_tier("Tier 3: Local / regional sources", qs.tier_3)
    emit_tier("Tier 4: Direct company pages", qs.tier_4)

    if qs.role_synonyms:
        print("\n## Role synonyms to also search")
        for syn in qs.role_synonyms:
            print(f"  - {syn}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
