#!/usr/bin/env python3
"""
normalize_salary.py

Parse free-text salary strings from job postings into a structured numeric range. Handles the
common posting formats:
    "$180k", "180,000", "$180,000-$220,000", "180-220k", "$180K - 220K USD/year"
    "180k-220k", "$95/hour", "$50-65 per hour", "USD 180,000-220,000 annually"

Output is a normalized record with min, max, currency, period (year/hour/month), and confidence.
Used by job-hunter Phase 2 to filter postings against the user's stated comp floor, and to flag
mismatches between expectation and market.

Usage:
    python normalize_salary.py "$180k-220k"
    python normalize_salary.py "USD 95/hour" --target-annual
    python normalize_salary.py "180,000 - 220,000" --currency-hint USD
    echo "$120K to $150K" | python normalize_salary.py -
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from typing import Optional


@dataclass
class Salary:
    raw: str
    min: Optional[float]
    max: Optional[float]
    currency: str
    period: str
    annualized_min: Optional[float]
    annualized_max: Optional[float]
    confidence: str
    notes: list[str]


CURRENCY_SYMBOLS = {"$": "USD", "€": "EUR", "£": "GBP", "¥": "JPY", "₹": "INR", "C$": "CAD",
                    "A$": "AUD", "NZ$": "NZD"}

PERIOD_PATTERNS = [
    (r"/\s*(?:yr|year|annum|annually|p\.?a\.?)", "year"),
    (r"per\s+(?:year|annum)", "year"),
    (r"/\s*(?:hr|hour|hourly)", "hour"),
    (r"per\s+hour", "hour"),
    (r"/\s*(?:mo|month|monthly)", "month"),
    (r"per\s+month", "month"),
    (r"/\s*(?:wk|week|weekly)", "week"),
    (r"per\s+week", "week"),
    (r"/\s*(?:day|daily)", "day"),
    (r"per\s+day", "day"),
]

HOURS_PER_YEAR = 2080
WEEKS_PER_YEAR = 52
MONTHS_PER_YEAR = 12
DAYS_PER_YEAR = 260


def _detect_currency(text: str, hint: Optional[str] = None) -> tuple[str, list[str]]:
    notes: list[str] = []
    upper = text.upper()
    iso = re.search(r"\b(USD|EUR|GBP|CAD|AUD|NZD|JPY|INR|CHF|SEK|DKK|NOK)\b", upper)
    if iso:
        return iso.group(1), notes
    for sym, code in CURRENCY_SYMBOLS.items():
        if sym in text:
            return code, notes
    if hint:
        notes.append(f"currency inferred from hint: {hint}")
        return hint.upper(), notes
    notes.append("currency not detected; defaulting to USD")
    return "USD", notes


def _detect_period(text: str) -> tuple[str, list[str]]:
    text_lower = text.lower()
    for pattern, period in PERIOD_PATTERNS:
        if re.search(pattern, text_lower):
            return period, []
    notes: list[str] = []
    if re.search(r"\bk\b", text_lower) or re.search(r",\d{3}\b", text):
        return "year", ["period inferred from k-suffix or thousand-separator (annual)"]
    if re.search(r"\d+\s*(?:\.\d+)?\s*$", text_lower.strip()) and "/" not in text:
        return "year", ["no explicit period; defaulting to year"]
    return "year", ["no explicit period; defaulting to year"]


def _parse_amount(s: str) -> Optional[float]:
    s = s.strip()
    s = s.replace(",", "")
    m = re.match(r"^([\d.]+)\s*([kKmM]?)$", s)
    if not m:
        return None
    try:
        value = float(m.group(1))
    except ValueError:
        return None
    suffix = m.group(2).lower()
    if suffix == "k":
        value *= 1_000
    elif suffix == "m":
        value *= 1_000_000
    return value


def _annualize(amount: float, period: str) -> float:
    if period == "year":
        return amount
    if period == "hour":
        return amount * HOURS_PER_YEAR
    if period == "month":
        return amount * MONTHS_PER_YEAR
    if period == "week":
        return amount * WEEKS_PER_YEAR
    if period == "day":
        return amount * DAYS_PER_YEAR
    return amount


def parse_salary(text: str, currency_hint: Optional[str] = None) -> Salary:
    raw = text
    notes: list[str] = []

    if not text or not text.strip():
        return Salary(raw=raw, min=None, max=None, currency="", period="",
                      annualized_min=None, annualized_max=None,
                      confidence="none", notes=["empty input"])

    currency, c_notes = _detect_currency(text, currency_hint)
    notes.extend(c_notes)

    period, p_notes = _detect_period(text)
    notes.extend(p_notes)

    cleaned = text
    for sym in CURRENCY_SYMBOLS:
        cleaned = cleaned.replace(sym, " ")
    cleaned = re.sub(r"\b(USD|EUR|GBP|CAD|AUD|NZD|JPY|INR|CHF|SEK|DKK|NOK)\b", " ",
                     cleaned, flags=re.IGNORECASE)
    for pattern, _ in PERIOD_PATTERNS:
        cleaned = re.sub(pattern, " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\b(per|annum|annually|hourly|monthly|weekly|daily|to)\b", " ",
                     cleaned, flags=re.IGNORECASE)

    numbers = re.findall(r"[\d.,]+\s*[kKmM]?", cleaned)
    parsed = [_parse_amount(n) for n in numbers]
    parsed = [p for p in parsed if p is not None and p > 0]

    if not parsed:
        return Salary(raw=raw, min=None, max=None, currency=currency, period=period,
                      annualized_min=None, annualized_max=None,
                      confidence="none", notes=notes + ["no numbers parsed"])

    if len(parsed) >= 2:
        lo, hi = min(parsed[:2]), max(parsed[:2])
        confidence = "high"
    else:
        lo = hi = parsed[0]
        confidence = "medium"
        notes.append("single value; treating as point estimate (min=max)")

    return Salary(
        raw=raw,
        min=lo,
        max=hi,
        currency=currency,
        period=period,
        annualized_min=_annualize(lo, period),
        annualized_max=_annualize(hi, period),
        confidence=confidence,
        notes=notes,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("text", nargs="?", default=None,
                        help="salary string, or '-' for stdin")
    parser.add_argument("--currency-hint", default=None,
                        help="currency code to assume when not detectable (e.g., USD, EUR)")
    parser.add_argument("--target-annual", action="store_true",
                        help="emit only the annualized range, one number per line")
    args = parser.parse_args(argv)

    if args.text == "-" or args.text is None:
        if sys.stdin.isatty() and args.text is None:
            parser.error("provide a salary string or pipe input")
        text = sys.stdin.read().strip()
    else:
        text = args.text

    result = parse_salary(text, args.currency_hint)

    if args.target_annual:
        if result.annualized_min is not None and result.annualized_max is not None:
            print(f"{int(result.annualized_min)} {int(result.annualized_max)}")
            return 0
        else:
            print("error: could not parse salary", file=sys.stderr)
            return 2

    print(json.dumps(asdict(result), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
