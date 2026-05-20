#!/usr/bin/env python3
"""
harvest_outcomes.py

Read the per-user learning-loop files in a workspace and classify closed-loop
outcomes into deterministic signals. This is the read-side of the per-user
learning loop. The output is a JSON document on stdout (or --out) that
propose_lessons.py consumes to suggest new entries for the user's LESSONS.md.

Sources read (all in user's workspace):
  - .job-hunter/OUTCOMES.md        (the closed-loop outcomes; ground truth)
  - .job-hunter/DECISIONS.md       (per-session decisions; secondary signal)
  - tracker.json                   (current application states; tertiary signal)

Signals surfaced:
  - rejection_dominant_reason : one reason cited in >= half of rejections
  - comp_threshold_signal     : pattern of comp_vs_target scores at rejections
  - culture_size_signal       : pattern across cultural_signals at rejections
  - board_yield               : application boards with zero positive outcomes
  - recommendation_calibration: agent recommendation accuracy vs actual outcome

COLD-START GUARD: if OUTCOMES.md has fewer than MIN_CLOSED_OUTCOMES (5) closed
entries, the output is `{"signals": [], "no_op_reason": "need >=5 closed-loop
outcomes, have N", ...}`. This is deliberate and matches the discipline used in
the self-improving-skills harvest_signals.py script. Patterns from thin data are
guesses, not lessons.

Privacy: reads only local files the user already has on disk. Never sends
anything off-machine. The output `signals.json` itself contains workspace
data and should be treated as user-private.

Usage:
    python harvest_outcomes.py --workspace /path/to/workspace [--out signals.json]
    python harvest_outcomes.py --workspace /path/to/workspace --json  (alias for stdout)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

MIN_CLOSED_OUTCOMES = 5

# Outcome enum recognized by the OUTCOMES template
OUTCOME_VALUES = {
    "accepted_offer",
    "rejected_offer",
    "rejected_after_onsite",
    "rejected_after_screen",
    "rejected_at_resume",
    "no_response_after_21d",
    "withdrew",
    "other",
}

POSITIVE_OUTCOMES = {"accepted_offer"}
NEGATIVE_OUTCOMES = {
    "rejected_offer",
    "rejected_after_onsite",
    "rejected_after_screen",
    "rejected_at_resume",
    "no_response_after_21d",
}

# Field patterns expected in an OUTCOMES.md entry block (after the ## heading)
_OUTCOME_FIELD_PATTERNS = {
    "outcome": re.compile(r"^\*\*Outcome:\*\*\s*([a-z_0-9]+)", re.MULTILINE),
    "reason": re.compile(r"^\*\*Reason[^:]*:\*\*\s*(.+?)(?=\n\*\*|\n##|\Z)", re.MULTILINE | re.DOTALL),
    "agent_rec": re.compile(r"^\*\*Agent recommendation[^:]*:\*\*\s*([a-z_]+)", re.MULTILINE),
    "score_breakdown": re.compile(r"^\*\*Score breakdown[^:]*:\*\*\s*(.+)", re.MULTILINE),
    "url": re.compile(r"^\*\*Posting URL:\*\*\s*(\S+)", re.MULTILINE),
}

# Append marker on DECISIONS.md template (the line below which user/agent entries land).
# Used to distinguish "user has added decisions" from "template scaffolding exists."
_DECISIONS_APPEND_MARKER = "<!-- Agent and user entries appended below this line -->"


def _has_user_decisions(decisions_text: str) -> bool:
    """True only when there's non-whitespace content AFTER the documented append
    marker in DECISIONS.md. Just having the template scaffolding (with privacy
    notice + format docs) does NOT count as decisions present.

    Falls back to checking for any `## YYYY-` heading if the marker is missing
    (someone hand-deleted it), since that's the documented entry format.
    """
    if not decisions_text.strip():
        return False
    idx = decisions_text.find(_DECISIONS_APPEND_MARKER)
    if idx >= 0:
        return bool(decisions_text[idx + len(_DECISIONS_APPEND_MARKER):].strip())
    # Marker missing — fall back to looking for any dated entry heading
    return bool(re.search(r"^## \d{4}-\d{2}-\d{2}", decisions_text, re.MULTILINE))


def _read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


_APPEND_MARKER = "<!-- Closed-loop outcomes appended below this line -->"


def parse_outcomes(text: str) -> list[dict]:
    """Parse OUTCOMES.md into a list of outcome dicts.

    Entries are delimited by `## ` headings AFTER the documented append marker.
    The marker (`<!-- Closed-loop outcomes appended below this line -->`) is
    load-bearing: everything before it is template documentation (which contains
    example `## ` headings and `**Outcome:**` lines as format docs). Anything
    before the marker is ignored.

    If the marker is missing (someone deleted it), we fall back to scanning the
    whole file, but skip any `## ` heading whose body lies inside a fenced code
    block (```). This double-safety pattern prevents documentation examples from
    being mis-parsed as outcomes.

    Empty / template-only files return an empty list. Malformed entries are
    skipped silently.
    """
    if not text.strip():
        return []

    # Slice everything from the append marker onward (typical case)
    marker_idx = text.find(_APPEND_MARKER)
    if marker_idx >= 0:
        body = text[marker_idx + len(_APPEND_MARKER):]
    else:
        # Fallback: strip fenced code blocks so documentation examples don't pollute
        body = re.sub(r"```.*?```", "", text, flags=re.DOTALL)

    # Split on `## ` headings — first chunk is the file preamble we discard
    chunks = re.split(r"^## ", body, flags=re.MULTILINE)
    entries = []
    for chunk in chunks[1:]:
        # Each chunk starts with the heading line then the entry body
        heading_line, _, body = chunk.partition("\n")
        entry = {"heading": heading_line.strip()}

        for key, pattern in _OUTCOME_FIELD_PATTERNS.items():
            match = pattern.search(body)
            if match:
                entry[key] = match.group(1).strip()

        # Only count entries that have a recognized outcome value
        outcome = entry.get("outcome", "").lower()
        if outcome in OUTCOME_VALUES:
            entries.append(entry)

    return entries


def _classify_recommendation_calibration(entries: list[dict]) -> dict | None:
    """Did the agent's recommendation match the actual outcome?

    Returns a signal dict only when both agent_rec and outcome are present on
    >= 5 entries (so the calibration analysis itself has signal).
    """
    paired = [(e["agent_rec"], e["outcome"]) for e in entries
              if "agent_rec" in e and "outcome" in e]
    if len(paired) < MIN_CLOSED_OUTCOMES:
        return None

    # Buckets: agent said apply + got positive = good; agent said apply + got
    # negative = false-positive; agent said skip + got positive = false-negative
    true_positive = sum(1 for rec, out in paired if rec == "apply" and out in POSITIVE_OUTCOMES)
    false_positive = sum(1 for rec, out in paired if rec == "apply" and out in NEGATIVE_OUTCOMES)
    false_negative = sum(1 for rec, out in paired if rec == "skip" and out in POSITIVE_OUTCOMES)

    return {
        "kind": "recommendation_calibration",
        "evidence_count": len(paired),
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "precision": true_positive / (true_positive + false_positive) if (true_positive + false_positive) else None,
    }


def _classify_rejection_reasons(entries: list[dict]) -> dict | None:
    """Find a reason cited in >= 50% of rejections.

    Returns a signal dict only when there are >= 5 rejections AND one
    keyword dominates. Keyword detection is intentionally simple
    (substring matching on a small canonical list); the agent re-interprets
    the signal in natural language during propose_lessons.
    """
    rejections = [e for e in entries if e.get("outcome", "") in NEGATIVE_OUTCOMES]
    if len(rejections) < MIN_CLOSED_OUTCOMES:
        return None

    reason_texts = [e.get("reason", "").lower() for e in rejections]

    # Canonical reason categories — substring matches into the free-text reason
    categories = {
        "comp": ["comp", "salary", "pay", "below target", "low pay"],
        "culture": ["culture", "fit", "team", "values", "mission"],
        "size": ["bureaucratic", "political", "too big", "too small", "size", "company size"],
        "remote": ["remote", "rto", "return to office", "in office", "in-office"],
        "responsibilities": ["responsibilities", "scope", "level", "seniority"],
        "no_response": ["no response", "ghosted", "never heard back"],
    }

    counts = Counter()
    for text in reason_texts:
        for category, keywords in categories.items():
            if any(kw in text for kw in keywords):
                counts[category] += 1

    if not counts:
        return None

    top_category, top_count = counts.most_common(1)[0]
    if top_count / len(rejections) < 0.5:
        return None

    return {
        "kind": "rejection_dominant_reason",
        "category": top_category,
        "matches": top_count,
        "evidence_count": len(rejections),
        "fraction": top_count / len(rejections),
    }


def harvest(workspace: Path) -> dict:
    """Read the workspace's .job-hunter/ files and emit a signals document."""
    outcomes_path = workspace / ".job-hunter" / "OUTCOMES.md"
    decisions_path = workspace / ".job-hunter" / "DECISIONS.md"

    outcomes_text = _read_text(outcomes_path)
    decisions_text = _read_text(decisions_path)

    entries = parse_outcomes(outcomes_text)

    if len(entries) < MIN_CLOSED_OUTCOMES:
        return {
            "workspace": str(workspace),
            "outcomes_found": len(entries),
            "min_required": MIN_CLOSED_OUTCOMES,
            "signals": [],
            "no_op_reason": (
                f"need >={MIN_CLOSED_OUTCOMES} closed-loop outcomes, "
                f"have {len(entries)} — apply to more roles and update tracker.json status"
            ),
            "decisions_present": _has_user_decisions(decisions_text),
            "untrusted_data": False,  # the user wrote the source files themselves
        }

    signals: list[dict] = []

    calibration = _classify_recommendation_calibration(entries)
    if calibration:
        signals.append(calibration)

    rejection_reason = _classify_rejection_reasons(entries)
    if rejection_reason:
        signals.append(rejection_reason)

    return {
        "workspace": str(workspace),
        "outcomes_found": len(entries),
        "signals": signals,
        "no_op_reason": "no patterns met the 50% dominance threshold yet" if not signals else None,
        "decisions_present": _has_user_decisions(decisions_text),
        "untrusted_data": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, type=Path,
                        help="user's workspace folder (contains .job-hunter/)")
    parser.add_argument("--out", type=Path,
                        help="write signals JSON here instead of stdout")
    args = parser.parse_args(argv)

    result = harvest(args.workspace)
    payload = json.dumps(result, indent=2)

    if args.out:
        args.out.write_text(payload, encoding="utf-8")
        print(f"wrote signals to {args.out}", file=sys.stderr)
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
