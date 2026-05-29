#!/usr/bin/env python3
"""
propose_lessons.py

Read a signals.json document (produced by harvest_outcomes.py) and translate
each signal into a suggested LESSONS.md entry the user can review and confirm.

This script never writes to LESSONS.md directly. The agent is responsible for
surfacing each suggestion to the user, getting explicit yes/no confirmation,
and only then appending confirmed entries to .job-hunter/LESSONS.md.

Output schema:
    {
      "workspace": "...",
      "suggestions": [
        {
          "kind": "<signal kind that triggered this>",
          "summary": "One-line pattern statement for user review",
          "lesson_block": "Multi-line markdown entry ready to append after confirmation",
          "reason": "Why this signal warrants a lesson (anchored in evidence count)",
          "evidence_count": N,
          "confidence": "low | medium | high"
        },
        ...
      ],
      "no_op_reason": "<if suggestions is empty, why>",
      "application_guidance": "Always surface to user with evidence; never auto-append."
    }

Discipline (matches self-improving-skills' propose_iteration.py):
- Deterministic translation: each signal kind maps to a fixed suggestion shape.
  The reason and evidence count are pulled directly from the signal — never
  paraphrased by an LLM. This keeps the lessons log honest.
- No side effects: the script never modifies LESSONS.md, OUTCOMES.md, or any
  other file in the workspace. The agent (with user confirmation) does that.
- Untrusted-data flag is propagated from the input signals document.

Usage:
    python propose_lessons.py --signals signals.json [--out proposal.json]
    python propose_lessons.py --signals-stdin [--out proposal.json]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# How many evidence entries upgrade confidence levels
HIGH_CONFIDENCE_THRESHOLD = 10
MEDIUM_CONFIDENCE_THRESHOLD = 5


def _confidence(evidence_count: int) -> str:
    if evidence_count >= HIGH_CONFIDENCE_THRESHOLD:
        return "high"
    if evidence_count >= MEDIUM_CONFIDENCE_THRESHOLD:
        return "medium"
    return "low"


def _format_lesson_block(date_str: str, pattern: str, evidence: str,
                         affected_subscores: str) -> str:
    """Render a LESSONS.md entry block in the format documented in the template."""
    return (
        f"## {date_str} — {pattern}\n\n"
        f"**Pattern:** {pattern}\n"
        f"**Evidence:** {evidence}\n"
        f"**How it shapes scoring:** {affected_subscores}\n"
    )


def _translate_rejection_dominant_reason(signal: dict, date_str: str) -> dict:
    """A rejection reason dominated >=50% of negative outcomes. Suggest a
    lesson that adjusts the matching sub-score grading."""
    category = signal["category"]
    matches = signal["matches"]
    total = signal["evidence_count"]
    fraction_pct = int(round(signal["fraction"] * 100))

    # Map category → human-readable pattern + which sub-score it shapes
    category_map = {
        "comp": (
            "User rejects postings below comp target more often than other reasons",
            "Grade comp_vs_target more strictly: a posting that is even slightly "
            "below the user's stated target should land at 2.5-3.0, not 3.5-4.0."
        ),
        "culture": (
            "User cites culture/team fit as a leading rejection reason",
            "Grade cultural_signals more conservatively: weight Glassdoor signals, "
            "team-size, and mission language heavily; don't inflate on visible polish alone."
        ),
        "size": (
            "User consistently rejects companies citing size/bureaucracy",
            "Grade cultural_signals lower for companies above 1000 employees; "
            "cite this lesson in the result so the user can audit."
        ),
        "remote": (
            "User rejects postings citing remote/RTO policy mismatches",
            "Grade cultural_signals lower when the posting requires office attendance "
            "above the user's stated tolerance in .job-hunter-profile.md."
        ),
        "responsibilities": (
            "User rejects postings citing scope/seniority mismatch",
            "Grade cv_match more strictly on seniority level alignment — a 'Senior' "
            "role at a company that uses 'Senior' as L3 should grade lower."
        ),
        "no_response": (
            "User experiences high no-response rates after applying",
            "Lower posting_legitimacy slightly when the posting source has a track "
            "record of no-response outcomes for this user (see OUTCOMES.md by source)."
        ),
    }

    pattern, scoring_guidance = category_map.get(category, (
        f"Rejection reason '{category}' dominates {fraction_pct}% of negative outcomes",
        "Discuss with the user how this should shape future scoring."
    ))

    return {
        "kind": "rejection_dominant_reason",
        "summary": pattern,
        "lesson_block": _format_lesson_block(
            date_str=date_str,
            pattern=pattern,
            evidence=f"{matches} of {total} rejections cited this category ({fraction_pct}%)",
            affected_subscores=scoring_guidance,
        ),
        "reason": (
            f"{matches} of {total} rejection outcomes ({fraction_pct}%) cite '{category}' "
            f"as a contributing factor"
        ),
        "evidence_count": total,
        "confidence": _confidence(total),
    }


def _translate_recommendation_calibration(signal: dict, date_str: str) -> dict | None:
    """Suggest a lesson only when calibration is meaningfully off from ideal."""
    precision = signal.get("precision")
    if precision is None:
        return None
    if precision >= 0.7:
        # Calibration is fine; no lesson needed
        return None

    fp = signal["false_positive"]
    tp = signal["true_positive"]
    total = signal["evidence_count"]
    prec_pct = int(round(precision * 100))

    pattern = (
        f"Agent 'apply' recommendations are correct only {prec_pct}% of the time "
        f"({tp} of {tp + fp} apply-recommendations led to a positive outcome)"
    )

    return {
        "kind": "recommendation_calibration",
        "summary": pattern,
        "lesson_block": _format_lesson_block(
            date_str=date_str,
            pattern=pattern,
            evidence=f"{tp} true positives, {fp} false positives across {total} outcomes",
            affected_subscores=(
                "Tighten the apply threshold OR adjust how cv_match and comp_vs_target "
                "are graded — the current grading is over-recommending 'apply'."
            ),
        ),
        "reason": (
            f"Precision={prec_pct}% across {total} outcomes; below the 70% threshold "
            f"where the agent's recommendation is reliable enough to defer to."
        ),
        "evidence_count": total,
        "confidence": _confidence(total),
    }


_TRANSLATORS = {
    "rejection_dominant_reason": _translate_rejection_dominant_reason,
    "recommendation_calibration": _translate_recommendation_calibration,
}


def propose(signals_doc: dict, today: str | None = None) -> dict:
    """Translate signals.json into proposal.json. Pure function: same input
    produces same output. The `today` parameter is overridable to keep tests
    deterministic."""
    today = today or datetime.now().strftime("%Y-%m-%d")

    if signals_doc.get("no_op_reason"):
        return {
            "workspace": signals_doc.get("workspace"),
            "suggestions": [],
            "no_op_reason": signals_doc["no_op_reason"],
            "application_guidance": (
                "Always surface suggestions to user with evidence before "
                "appending. Never auto-write to LESSONS.md."
            ),
        }

    suggestions: list[dict] = []
    for signal in signals_doc.get("signals", []):
        kind = signal.get("kind")
        translator = _TRANSLATORS.get(kind)
        if not translator:
            continue
        suggestion = translator(signal, today)
        if suggestion is not None:
            suggestions.append(suggestion)

    return {
        "workspace": signals_doc.get("workspace"),
        "suggestions": suggestions,
        "no_op_reason": (
            "no signals met the suggestion threshold (e.g., calibration was fine)"
            if not suggestions else None
        ),
        "application_guidance": (
            "Always surface suggestions to user with evidence before appending. "
            "Never auto-write to LESSONS.md. The agent must get explicit user "
            "confirmation per suggestion."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--signals", type=Path, help="path to signals.json from harvest_outcomes.py")
    group.add_argument("--signals-stdin", action="store_true",
                       help="read signals JSON from stdin")
    parser.add_argument("--out", type=Path, help="write proposal JSON here instead of stdout")
    parser.add_argument("--today", help="override today's date as YYYY-MM-DD (for testing)")
    args = parser.parse_args(argv)

    if args.signals_stdin:
        signals_doc = json.load(sys.stdin)
    else:
        signals_doc = json.loads(args.signals.read_text(encoding="utf-8"))

    result = propose(signals_doc, today=args.today)
    payload = json.dumps(result, indent=2)

    if args.out:
        args.out.write_text(payload, encoding="utf-8")
        print(f"wrote proposal to {args.out}", file=sys.stderr)
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
