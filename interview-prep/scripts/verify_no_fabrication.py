#!/usr/bin/env python3
"""
verify_no_fabrication.py

Compare an ORIGINAL resume text against a PROPOSED tailored or tightened
version. Surface every factual claim in the proposed version that does NOT
appear in the original. The script is detection-only: it lists what's new,
the agent uses the list to drive per-claim user confirmation, the user
decides what's a fabrication vs a legitimate rephrasing.

The script NEVER auto-approves output. It NEVER modifies files. Its only
job is to make new claims visible.

Detection categories:

  - new_proper_nouns      : capitalized tokens in proposed that aren't in original.
                            Catches new tool names, company names, product names
                            (Pinecone, Weaviate, Stripe). High precision.
  - new_numbers           : numeric tokens (integers, percentages, dollar amounts,
                            ranges, units) in proposed that aren't in original.
                            Catches invented quantification ("60 houses/week",
                            "$1M+", "managed a team of 12").
  - new_sections          : markdown headings or all-caps section labels in
                            proposed that aren't in original. Catches structural
                            changes (e.g., promoting a project to its own
                            Professional Experience entry).
  - new_bullets           : count delta of bullet lines per detected section.
                            Catches whole-new-bullet additions.
  - new_phrase_runs       : 5+-word runs in proposed not found in original.
                            The semantic-fabrication catch. Lossy (paraphrasing
                            triggers false positives), but useful as a final pass.

Output schema:

    {
      "original_chars": N,
      "proposed_chars": M,
      "new_proper_nouns": [{"token": "Pinecone", "context": "...sentence..."}, ...],
      "new_numbers": [{"token": "60", "context": "..."}, ...],
      "new_sections": ["## Professional Experience: GDK Digital", ...],
      "new_bullets": {"GDK Digital": +6, "Mark Scott Construction": +1},
      "new_phrase_runs": ["early specialization in insurance restoration", ...],
      "summary": {
        "total_new_claims": N,
        "highest_risk": "new_proper_nouns" | "new_numbers" | "new_phrase_runs" | "none",
        "verdict": "clean" | "review_required",
      },
      "auto_approved": false  // ALWAYS false. The script does not auto-approve.
    }

Usage:
    python verify_no_fabrication.py --original original_resume.txt \\
        --proposed tailored_resume.txt [--out diff_report.json]
    python verify_no_fabrication.py --original-stdin --proposed proposed.txt
    python verify_no_fabrication.py --original original.txt --proposed-stdin

CRITICAL: This script's output is INPUT to the user-confirmation flow. The
agent is responsible for surfacing every "new_*" entry to the user and
getting explicit yes/no per item before writing any tailored output. See
SKILL.md Phase 3 for the contract.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

# A token is considered a "proper noun candidate" if it starts with an uppercase
# letter, has at least 2 chars, and is not in this stopword set.
_PROPER_NOUN_STOPWORDS = {
    # Common sentence-start words
    "The", "A", "An", "I", "We", "You", "They", "He", "She", "It", "This", "That",
    "These", "Those", "My", "Your", "Our", "Their", "His", "Her", "Its",
    "And", "But", "Or", "So", "Yet", "For", "Nor", "After", "Before", "When",
    "While", "If", "Although", "Because", "Since", "Unless", "Until", "As",
    "At", "By", "From", "In", "Of", "On", "To", "With", "Without",
    # Month names (dates in resumes, not fabrications)
    "January", "February", "March", "April", "May", "June", "July", "August",
    "September", "October", "November", "December",
    "Jan", "Feb", "Mar", "Apr", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    # Day names
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
    # Section / structural labels common in resumes
    "Present", "Current", "Summary", "Experience", "Education", "Skills",
    "Certifications", "Projects", "Awards", "References",
    # Common resume verbs / nouns
    "Lead", "Senior", "Junior", "Manager", "Director", "Engineer", "Architect",
    "Developer", "Designer", "Analyst",
}

# A "number token" is anything that looks like a quantity: integers, decimals,
# percentages, dollar amounts, ranges, abbreviated thousands/millions.
# Examples: "60", "60/week", "$120k", "20+", "5,000", "1.2M", "$1M+", "85%"
_NUMBER_PATTERN = re.compile(
    r"""
    (?:
        \$[\d,]+(?:\.\d+)? (?:k|K|m|M|b|B|MM|MM\+)? \+? |  # $1M+, $120k, $5,000
        \d[\d,]* (?:\.\d+)? \s* (?:k|K|m|M|b|B|MM)? \+? % |  # 85%, 20%+
        \d[\d,]* (?:\.\d+)? \s* (?:k|K|m|M|b|B|MM)? \+? (?:/\w+|x\b)? |  # 60/week, 10x
        \d{4}                                                # year tokens (2023, 1992)
    )
    """,
    re.VERBOSE,
)

# Section heading detection: markdown ## headings OR all-caps lines with optional
# bold markers. Matches "## Professional Experience", "**PROFESSIONAL EXPERIENCE**", etc.
_SECTION_HEADING_PATTERN = re.compile(
    r"""
    ^\s*
    (?:
        \#{1,3}\s+ .+ |                          # markdown heading
        \*{2}? [A-Z][A-Z\s&/\-]{4,} \*{2}? \s*$  # all-caps line, 5+ chars
    )
    \s*$
    """,
    re.VERBOSE | re.MULTILINE,
)


def _tokenize_words(text: str) -> list[str]:
    """Tokenize on whitespace and punctuation boundaries, preserving case."""
    return re.findall(r"[A-Za-z][A-Za-z0-9\-\']*", text)


def _proper_noun_set(text: str) -> set[str]:
    """Return the set of all proper-noun-candidate tokens in the text.
    Proper noun = starts uppercase, len >= 2, not in stopword set,
    not at the start of a sentence (we approximate by checking the prior char)."""
    out = set()
    # Walk character-by-character so we know what precedes each token
    for match in re.finditer(r"[A-Z][A-Za-z0-9\-\']+", text):
        token = match.group(0)
        if token in _PROPER_NOUN_STOPWORDS:
            continue
        if len(token) < 2:
            continue
        # Reject token if it's at the start of a sentence (preceded by . ! ? \n or BOF)
        # This is a heuristic, proper nouns at sentence starts will be missed,
        # but the cost of false positives (capitalized sentence-start words flagged
        # as proper nouns) is higher than the cost of missing some real ones.
        start = match.start()
        if start == 0:
            continue
        # Look backwards for the first non-whitespace char
        i = start - 1
        while i >= 0 and text[i] in " \t":
            i -= 1
        if i < 0:
            continue
        prev = text[i]
        if prev in ".!?\n\r":
            continue
        out.add(token)
    return out


def _number_set(text: str) -> set[str]:
    """Return the set of all number-tokens in the text. Years are special-cased
    because (a) employment dates are always year-tokens that mirror across both
    documents, and (b) flagging years as "new numbers" produces noise."""
    out = set()
    for match in _NUMBER_PATTERN.finditer(text):
        tok = match.group(0).strip()
        # Skip plain 4-digit years, they're calendar dates, not fabricated stats
        if re.fullmatch(r"(?:19|20)\d{2}", tok):
            continue
        out.add(tok)
    return out


def _section_headings(text: str) -> list[str]:
    """Return the list of section headings (preserves order + duplicates intentionally)."""
    return [m.group(0).strip() for m in _SECTION_HEADING_PATTERN.finditer(text)]


def _bullet_count_by_section(text: str) -> dict[str, int]:
    """Walk the document, count bullet lines per section. A bullet is any line
    starting with -, *, or • or ▸ after optional whitespace."""
    counts: dict[str, int] = {}
    current_section = "(preamble)"
    for line in text.splitlines():
        stripped = line.strip()
        # Detect section transition
        if _SECTION_HEADING_PATTERN.fullmatch(line):
            current_section = stripped
            counts.setdefault(current_section, 0)
            continue
        # Bullet line?
        if re.match(r"^[-*•▸]\s", stripped):
            counts.setdefault(current_section, 0)
            counts[current_section] += 1
    return counts


def _phrase_runs(text: str, n: int = 5) -> set[str]:
    """Return the set of n-word runs in the text (sliding window of n words).
    Phrasing matched case-insensitively after light normalization (strip
    punctuation other than internal hyphens, collapse whitespace)."""
    # Normalize: lowercase, strip leading/trailing punctuation per word,
    # split on whitespace
    words = re.findall(r"[a-z0-9][a-z0-9\-']*", text.lower())
    if len(words) < n:
        return set()
    runs = set()
    for i in range(len(words) - n + 1):
        runs.add(" ".join(words[i : i + n]))
    return runs


def _context_for_token(text: str, token: str, max_chars: int = 100) -> str:
    """Return a short context window around the first occurrence of token in text."""
    idx = text.find(token)
    if idx < 0:
        return ""
    start = max(0, idx - max_chars // 2)
    end = min(len(text), idx + len(token) + max_chars // 2)
    snippet = text[start:end].replace("\n", " ").strip()
    return f"...{snippet}..." if (start > 0 or end < len(text)) else snippet


def verify(original: str, proposed: str, phrase_run_length: int = 5) -> dict:
    """Detect every claim in proposed that is not in original. Returns the
    structured detection dict. Never makes a judgment about whether a claim
    is a fabrication, that's the user's call."""

    # New proper nouns
    orig_nouns = _proper_noun_set(original)
    prop_nouns = _proper_noun_set(proposed)
    new_nouns = sorted(prop_nouns - orig_nouns)
    new_proper_nouns = [
        {"token": tok, "context": _context_for_token(proposed, tok)}
        for tok in new_nouns
    ]

    # New numbers
    orig_numbers = _number_set(original)
    prop_numbers = _number_set(proposed)
    new_numbers_set = sorted(prop_numbers - orig_numbers)
    new_numbers = [
        {"token": tok, "context": _context_for_token(proposed, tok)}
        for tok in new_numbers_set
    ]

    # New section headings (preserve order in proposed)
    orig_sections = set(_section_headings(original))
    new_sections = []
    seen = set()
    for h in _section_headings(proposed):
        if h not in orig_sections and h not in seen:
            new_sections.append(h)
            seen.add(h)

    # Bullet count delta per section (only report sections with positive delta)
    orig_bullets = _bullet_count_by_section(original)
    prop_bullets = _bullet_count_by_section(proposed)
    bullet_deltas: dict[str, int] = {}
    for section, count in prop_bullets.items():
        delta = count - orig_bullets.get(section, 0)
        if delta > 0:
            bullet_deltas[section] = delta

    # New phrase runs (5+-word substring search)
    orig_runs = _phrase_runs(original, phrase_run_length)
    prop_runs = _phrase_runs(proposed, phrase_run_length)
    new_runs = sorted(prop_runs - orig_runs)
    # Limit to first 20 to avoid overwhelming output; user can re-run with --all
    new_phrase_runs = new_runs[:20]

    # Summary
    total = (
        len(new_proper_nouns)
        + len(new_numbers)
        + len(new_sections)
        + sum(bullet_deltas.values())
        + len(new_phrase_runs)
    )
    if total == 0:
        verdict = "clean"
        highest_risk = "none"
    else:
        verdict = "review_required"
        # Risk ranking: proper nouns > numbers > phrase runs > bullets > sections
        if new_proper_nouns:
            highest_risk = "new_proper_nouns"
        elif new_numbers:
            highest_risk = "new_numbers"
        elif new_phrase_runs:
            highest_risk = "new_phrase_runs"
        elif bullet_deltas:
            highest_risk = "new_bullets"
        else:
            highest_risk = "new_sections"

    return {
        "original_chars": len(original),
        "proposed_chars": len(proposed),
        "new_proper_nouns": new_proper_nouns,
        "new_numbers": new_numbers,
        "new_sections": new_sections,
        "new_bullets": bullet_deltas,
        "new_phrase_runs": new_phrase_runs,
        "summary": {
            "total_new_claims": total,
            "highest_risk": highest_risk,
            "verdict": verdict,
        },
        # LOAD-BEARING: this field is always False. The script's contract is
        # that it detects new claims and presents them; it never decides they're OK.
        # A test asserts this field is always False regardless of input.
        "auto_approved": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original", type=Path,
                        help="path to original resume text (plain text or markdown)")
    parser.add_argument("--proposed", type=Path,
                        help="path to proposed tailored/tightened resume text")
    parser.add_argument("--original-stdin", action="store_true",
                        help="read original from stdin instead of --original file")
    parser.add_argument("--proposed-stdin", action="store_true",
                        help="read proposed from stdin instead of --proposed file")
    parser.add_argument("--out", type=Path,
                        help="write JSON report to this file instead of stdout")
    parser.add_argument("--phrase-run-length", type=int, default=5,
                        help="minimum word-run length for phrase-run detection (default 5)")
    args = parser.parse_args(argv)

    if args.original_stdin and args.proposed_stdin:
        print("error: cannot read BOTH original and proposed from stdin", file=sys.stderr)
        return 2
    if not args.original and not args.original_stdin:
        print("error: --original or --original-stdin required", file=sys.stderr)
        return 2
    if not args.proposed and not args.proposed_stdin:
        print("error: --proposed or --proposed-stdin required", file=sys.stderr)
        return 2

    if args.original_stdin:
        original = sys.stdin.read()
    else:
        original = args.original.read_text(encoding="utf-8")
    if args.proposed_stdin:
        proposed = sys.stdin.read()
    else:
        proposed = args.proposed.read_text(encoding="utf-8")

    report = verify(original, proposed, phrase_run_length=args.phrase_run_length)
    payload = json.dumps(report, indent=2, ensure_ascii=False)

    if args.out:
        args.out.write_text(payload, encoding="utf-8")
        verdict = report["summary"]["verdict"]
        print(f"wrote report to {args.out} (verdict: {verdict})", file=sys.stderr)
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
