#!/usr/bin/env python3
"""
dedupe_postings.py

Deduplicate a list of job postings collected across multiple search sources. Postings are
matched by normalized (company, title, location); when duplicates are found the script picks
the URL from the most direct source (company career page > aggregator > LinkedIn-style mirror)
and keeps the other URLs as 'also_seen_on' so the user can see breadth.

Input: JSON file or stdin, format:
  [
    {
      "title": "Senior Data Engineer",
      "company": "Acme Corp",
      "location": "Austin, TX",
      "url": "https://linkedin.com/jobs/view/1234",
      "source": "LinkedIn",
      "posted": "2026-04-15",
      "salary": "$180k-220k",
      "summary": "..."
    },
    ...
  ]

Output: same shape, deduplicated, with 'also_seen_on' appended where duplicates collapsed.

Usage:
    python dedupe_postings.py postings.json
    cat postings.json | python dedupe_postings.py -
    python dedupe_postings.py postings.json --out deduped.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from typing import Any
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode


# URL query parameters that are tracking/referrer noise, not identity
TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "gclid", "fbclid", "msclkid", "dclid", "yclid",
    "ref", "refid", "ref_id", "referrer", "src", "source",
    "_hsenc", "_hsmi", "hsCtaTracking",
    "mc_cid", "mc_eid",
    "trk", "trkInfo", "originalSubdomain",
    "lipi", "licu",
    "_ga", "_gid",
}


def _canonicalize_url(url: str) -> str:
    if not url or not url.strip():
        return ""
    try:
        parsed = urlparse(url.strip())
    except ValueError:
        return url.strip()
    scheme = parsed.scheme.lower() or "https"
    if scheme not in ("http", "https"):
        return url.strip()
    netloc = parsed.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    path = parsed.path.rstrip("/") or "/"
    pairs = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=False)
             if k.lower() not in TRACKING_PARAMS]
    pairs.sort()
    query = urlencode(pairs)
    return urlunparse((scheme, netloc, path, "", query, ""))


SOURCE_PRIORITY = [
    "company career page",
    "company careers",
    "company website",
    "greenhouse",
    "lever",
    "workday",
    "ashby",
    "smartrecruiters",
    "built in",
    "dice",
    "wellfound",
    "we work remotely",
    "remote ok",
    "linkedin",
    "indeed",
    "glassdoor",
    "ziprecruiter",
    "craigslist",
    "aggregator",
    "unknown",
]


def _normalize(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^\w\s-]", " ", s)
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\b(sr|senior|jr|junior|lead|principal|staff|i|ii|iii|iv|2|3)\b", "", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def _normalize_company(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"\b(inc|incorporated|llc|ltd|limited|corp|corporation|co|company)\b", "", s)
    s = re.sub(r"[.,]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def _normalize_location(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"\s+", " ", s)
    if "remote" in s:
        return "remote"
    parts = [p.strip() for p in s.split(",")]
    return ", ".join(parts[:2]) if parts else s


def _source_priority(source: str) -> int:
    src = (source or "unknown").lower().strip()
    for i, key in enumerate(SOURCE_PRIORITY):
        if key in src:
            return i
    return len(SOURCE_PRIORITY)


def _key(posting: dict[str, Any]) -> tuple[str, str, str]:
    return (
        _normalize_company(posting.get("company", "")),
        _normalize(posting.get("title", "")),
        _normalize_location(posting.get("location", "")),
    )


def dedupe(postings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not isinstance(postings, list):
        raise ValueError("input must be a JSON array of posting objects")

    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for p in postings:
        if not isinstance(p, dict):
            raise ValueError(f"each posting must be an object, got {type(p).__name__}")
        if not p.get("title") or not p.get("company"):
            raise ValueError(f"posting missing required title/company: {p}")
        groups[_key(p)].append(p)

    url_index: dict[str, dict[str, Any]] = {}
    for group in list(groups.values()):
        for p in group:
            cu = _canonicalize_url(p.get("url", ""))
            if cu and cu not in url_index:
                url_index[cu] = p
            elif cu:
                pass

    out: list[dict[str, Any]] = []
    for key, group in groups.items():
        if len(group) == 1:
            single = dict(group[0])
            single["canonical_url"] = _canonicalize_url(single.get("url", ""))
            out.append(single)
            continue
        group_sorted = sorted(group, key=lambda p: _source_priority(p.get("source", "")))
        primary = dict(group_sorted[0])
        primary["canonical_url"] = _canonicalize_url(primary.get("url", ""))
        also = []
        for other in group_sorted[1:]:
            also.append({
                "source": other.get("source", "unknown"),
                "url": other.get("url", ""),
            })
        primary["also_seen_on"] = also
        out.append(primary)

    out.sort(key=lambda p: (p.get("company", "").lower(), p.get("title", "").lower()))
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="path to postings JSON, or '-' for stdin")
    parser.add_argument("--out", default=None, help="output JSON path (default: stdout)")
    args = parser.parse_args(argv)

    try:
        if args.input == "-":
            postings = json.load(sys.stdin)
        else:
            with open(args.input, "r", encoding="utf-8") as f:
                postings = json.load(f)
    except json.JSONDecodeError as e:
        print(f"error: invalid JSON input: {e}", file=sys.stderr)
        return 2
    except OSError as e:
        print(f"error: cannot read input: {e}", file=sys.stderr)
        return 2

    try:
        deduped = dedupe(postings)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    out_json = json.dumps(deduped, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(out_json + "\n")
        original = len(postings) if isinstance(postings, list) else 0
        print(f"wrote {len(deduped)} deduped postings to {args.out} (from {original} input)",
              file=sys.stderr)
    else:
        print(out_json)

    return 0


if __name__ == "__main__":
    sys.exit(main())
