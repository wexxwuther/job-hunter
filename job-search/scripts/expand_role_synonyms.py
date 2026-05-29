#!/usr/bin/env python3
"""
expand_role_synonyms.py

Expand a job role into known synonyms and related titles for broader search coverage. Used in
Phase 2 of job-hunter when the initial search returns thin results — running the same query
against role synonyms often surfaces postings that use different terminology for the same job.

Covers 80+ roles across tech, healthcare, finance, marketing, operations, education, trades,
legal, and sales. Returns the original role plus all known synonyms.

Usage:
    python expand_role_synonyms.py "data engineer"
    python expand_role_synonyms.py "nurse" --json
    python expand_role_synonyms.py "software engineer" --include-adjacent
"""

from __future__ import annotations

import argparse
import json
import re
import sys


# Each entry: canonical key -> list of synonyms / alternate titles
# Adjacent roles (stepping-stone or natural pivots) live in ADJACENT.
SYNONYMS: dict[str, list[str]] = {
    # Tech - engineering
    "software engineer": ["software developer", "SWE", "backend engineer", "frontend engineer",
                          "full stack engineer", "full-stack developer", "applications engineer",
                          "programmer"],
    "backend engineer": ["backend developer", "server-side engineer", "API engineer",
                         "platform engineer"],
    "frontend engineer": ["front-end developer", "UI engineer", "React developer",
                          "Vue developer", "web developer"],
    "full stack engineer": ["full-stack developer", "full stack developer", "fullstack engineer"],
    "data engineer": ["analytics engineer", "data platform engineer", "ETL developer",
                      "data infrastructure engineer", "BI engineer"],
    "data scientist": ["ML engineer", "machine learning engineer", "applied scientist",
                       "analytics scientist", "research scientist"],
    "machine learning engineer": ["ML engineer", "AI engineer", "applied ML engineer",
                                  "ML platform engineer"],
    "devops engineer": ["SRE", "site reliability engineer", "platform engineer",
                        "infrastructure engineer", "cloud engineer", "DevOps/SRE"],
    "security engineer": ["application security engineer", "AppSec engineer", "infosec engineer",
                          "cybersecurity engineer", "security analyst"],
    "qa engineer": ["test engineer", "SDET", "quality assurance analyst", "automation engineer"],
    "mobile engineer": ["iOS developer", "Android developer", "mobile developer",
                        "React Native developer", "Flutter developer"],
    "embedded engineer": ["firmware engineer", "embedded systems engineer", "IoT engineer"],
    # Tech - product/design
    "product manager": ["PM", "product owner", "technical product manager", "TPM",
                        "senior product manager", "group product manager"],
    "product designer": ["UX designer", "UI designer", "interaction designer",
                         "user experience designer"],
    "ux researcher": ["user researcher", "design researcher", "UX research analyst"],
    "designer": ["UX designer", "product designer", "UI designer", "graphic designer",
                 "visual designer"],
    "engineering manager": ["software engineering manager", "EM", "engineering lead",
                            "tech lead manager"],
    # Tech - data/analytics
    "data analyst": ["business analyst", "analytics analyst", "BI analyst", "reporting analyst"],
    "business analyst": ["BA", "business systems analyst", "operations analyst"],
    "business intelligence": ["BI analyst", "BI developer", "analytics developer"],

    # Healthcare
    "nurse": ["registered nurse", "RN", "LPN", "LVN", "nursing professional"],
    "registered nurse": ["RN", "staff nurse", "clinical nurse"],
    "nurse practitioner": ["NP", "advanced practice nurse", "APRN", "FNP"],
    "physician assistant": ["PA", "physician associate"],
    "physician": ["doctor", "MD", "DO", "attending physician", "staff physician"],
    "medical assistant": ["MA", "clinical assistant", "patient care assistant"],
    "pharmacist": ["clinical pharmacist", "retail pharmacist", "pharmacy manager"],
    "physical therapist": ["PT", "DPT", "rehabilitation therapist"],

    # Finance / accounting
    "accountant": ["staff accountant", "senior accountant", "CPA", "accounting analyst"],
    "financial analyst": ["finance analyst", "FP&A analyst", "investment analyst",
                          "corporate finance analyst"],
    "controller": ["financial controller", "assistant controller", "accounting manager"],
    "auditor": ["internal auditor", "external auditor", "audit associate"],
    "investment banker": ["IB analyst", "investment banking associate", "M&A analyst"],

    # Marketing / sales
    "marketing manager": ["growth manager", "demand gen manager", "marketing director",
                          "brand manager"],
    "content marketer": ["content strategist", "content writer", "content manager",
                         "editorial manager"],
    "growth marketer": ["growth lead", "growth manager", "performance marketing manager"],
    "seo specialist": ["SEO manager", "SEO analyst", "organic search specialist"],
    "sales rep": ["account executive", "AE", "sales representative", "business development rep",
                  "BDR", "SDR"],
    "account executive": ["AE", "enterprise AE", "sales executive", "senior account executive"],
    "customer success manager": ["CSM", "client success manager", "customer success rep"],

    # Operations
    "operations manager": ["ops manager", "operations lead", "business operations manager"],
    "project manager": ["program manager", "PMP", "PgM", "project coordinator"],
    "program manager": ["TPM", "technical program manager", "senior program manager"],
    "supply chain analyst": ["logistics analyst", "supply chain manager", "procurement analyst"],
    "office manager": ["office administrator", "administrative manager", "facilities manager"],
    "executive assistant": ["EA", "administrative assistant", "personal assistant", "PA"],

    # Education
    "teacher": ["instructor", "educator", "K-12 teacher", "classroom teacher"],
    "professor": ["associate professor", "assistant professor", "lecturer", "adjunct professor"],
    "academic advisor": ["college advisor", "student success advisor"],
    "instructional designer": ["learning designer", "curriculum designer",
                               "instructional design specialist"],

    # Trades / construction / manufacturing
    "electrician": ["journeyman electrician", "master electrician", "industrial electrician"],
    "plumber": ["journeyman plumber", "pipefitter"],
    "welder": ["TIG welder", "MIG welder", "structural welder", "pipe welder"],
    "carpenter": ["construction carpenter", "finish carpenter", "framing carpenter"],
    "construction superintendent": ["site superintendent", "general superintendent",
                                    "construction manager"],
    "truck driver": ["CDL driver", "OTR driver", "delivery driver", "long-haul driver"],
    "machinist": ["CNC machinist", "tool and die maker", "manual machinist"],

    # Legal
    "lawyer": ["attorney", "associate attorney", "counsel", "legal counsel"],
    "paralegal": ["legal assistant", "litigation paralegal", "corporate paralegal"],
    "compliance officer": ["compliance analyst", "regulatory compliance specialist"],

    # HR / recruiting
    "recruiter": ["technical recruiter", "talent acquisition specialist", "talent partner",
                  "sourcer"],
    "hr manager": ["people operations manager", "HR business partner", "HRBP"],
    "hr generalist": ["HR specialist", "people operations specialist"],

    # Customer / support
    "customer support": ["customer service representative", "support specialist", "CX specialist",
                         "client services representative"],
    "technical support": ["IT support", "helpdesk technician", "support engineer", "tier 1 support"],

    # Writing / media
    "writer": ["copywriter", "content writer", "technical writer", "editor"],
    "technical writer": ["documentation specialist", "technical content writer",
                         "developer documentation engineer"],
    "journalist": ["reporter", "staff writer", "news writer", "correspondent"],
}

# Adjacent / step-up / step-down roles - returned only with --include-adjacent
ADJACENT: dict[str, list[str]] = {
    "data engineer": ["data scientist", "ML engineer", "backend engineer", "software engineer"],
    "data analyst": ["data engineer", "data scientist", "business analyst"],
    "software engineer": ["backend engineer", "frontend engineer", "engineering manager"],
    "product manager": ["product designer", "product marketing manager", "TPM",
                        "engineering manager"],
    "nurse": ["nurse practitioner", "physician assistant", "medical assistant"],
    "accountant": ["financial analyst", "controller", "auditor"],
    "marketing manager": ["growth marketer", "content marketer", "product marketing manager"],
    "project manager": ["program manager", "TPM", "operations manager"],
    "designer": ["product designer", "UX researcher", "frontend engineer"],
}


def _normalize(role: str) -> str:
    role = role.lower().strip()
    role = re.sub(r"\s+", " ", role)
    return role


def expand(role: str, include_adjacent: bool = False) -> dict:
    norm = _normalize(role)
    direct: list[str] = SYNONYMS.get(norm, []).copy()

    if not direct:
        for key, syns in SYNONYMS.items():
            if norm in syns or any(_normalize(s) == norm for s in syns):
                direct = [key] + [s for s in syns if _normalize(s) != norm]
                norm = key
                break

    adjacent: list[str] = []
    if include_adjacent:
        adjacent = ADJACENT.get(norm, []).copy()

    return {
        "input": role,
        "canonical": norm if norm in SYNONYMS else role,
        "synonyms": direct,
        "adjacent": adjacent,
        "all_search_terms": [role] + direct + (adjacent if include_adjacent else []),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("role", help='Job role to expand (e.g., "data engineer")')
    parser.add_argument("--include-adjacent", action="store_true",
                        help="Also include adjacent/step-up roles (different job, related field)")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    args = parser.parse_args(argv)

    if not args.role.strip():
        print("error: role must be non-empty", file=sys.stderr)
        return 2

    result = expand(args.role, args.include_adjacent)

    if args.json:
        print(json.dumps(result, indent=2))
        return 0

    print(f"Input role: {result['input']}")
    print(f"Canonical:  {result['canonical']}")
    print()
    if result["synonyms"]:
        print("Synonyms (same job, different title):")
        for s in result["synonyms"]:
            print(f"  - {s}")
    else:
        print("No known synonyms in the table. Search the canonical role only.")
    if args.include_adjacent and result["adjacent"]:
        print()
        print("Adjacent roles (related, but different job):")
        for s in result["adjacent"]:
            print(f"  - {s}")
    print()
    print(f"Total search terms: {len(result['all_search_terms'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
