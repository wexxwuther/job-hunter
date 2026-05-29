#!/usr/bin/env python3
"""
score_posting.py

Deterministic multi-block scorer for a single job posting. Produces 5 sub-scores plus a
weighted global score and a recommendation. Used in Phase 2 to give the user a defensible
numeric reason to pursue or skip a posting, rather than relying on a hand-waved "Strong /
Good / Possible" tag alone.

Inputs are LLM-graded sub-scores in the 1-5 range (the agent fills these in during posting
extraction); this script handles the arithmetic, applies the weights, computes a
red-flags multiplier, and emits a recommendation enum the tracker HTML can color-code.

Sub-scores (caller fills in based on posting + resume + user profile):
  cv_match           1-5  How well the resume matches stated requirements
  comp_vs_target     1-5  Salary range relative to user's stated comp target
  cultural_signals   1-5  Company stability, growth, remote policy, mission fit
  posting_legitimacy 1-5  See references/posting-legitimacy-rubric.md (ghost-job axis)
  red_flags_penalty  0-1  Fraction to subtract via multiplier (0 = clean, 0.5 = halve, etc.)

Weighted global score (also 1-5 scale):
  global = (0.35 * cv_match
            + 0.25 * comp_vs_target
            + 0.20 * cultural_signals
            + 0.20 * posting_legitimacy) * (1.0 - red_flags_penalty)

Recommendation buckets (matches career-ops Block-G semantics):
  apply                    >= 4.0
  apply_if_specific_reason 3.5 - 3.99
  skip                     < 3.5

Usage:
    python score_posting.py --sub-scores '{"cv_match": 4.5, "comp_vs_target": 4.0,
        "cultural_signals": 3.5, "posting_legitimacy": 5.0, "red_flags_penalty": 0.0}'
    python score_posting.py --sub-scores-file scored.json
    echo '{"cv_match": 4, ...}' | python score_posting.py -

Sub-scores file may be a single object or a list of objects (one per posting). For a list
input, the output is a JSON array of scored postings in the same order.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from typing import Any


# ---- Weight rationale -------------------------------------------------------
#
# These weights are deliberate, not arbitrary. Each carries a load-bearing reason.
#
# WEIGHT_CV_MATCH = 0.35
#   Rationale: CV match is the single most predictive signal that the application will
#   reach a human at the company. ATS filters rely on it; recruiters skim for it. Under-
#   weighting it produces "interesting role I'd never get an interview for" recommendations.
#
# WEIGHT_COMP = 0.25
#   Rationale: comp is a hard floor for most users — a great role that pays 40% under target
#   is not a great role for that user. Heavy enough to dominate over cultural fit when comp
#   is far below target, but not so heavy it overrides a 5/5 cv_match on a 4/5 comp.
#
# WEIGHT_CULTURAL = 0.20
#   Rationale: stability, remote policy, mission fit matter but are partly inferable from
#   the user accepting an interview anyway. Lower than cv/comp because users self-select on
#   these post-application.
#
# WEIGHT_LEGITIMACY = 0.20
#   Rationale: a high-confidence-legitimate posting that's a moderate match beats a perfect-
#   match posting that's likely a ghost listing. Career-ops Block G validated this weighting
#   empirically; independent 2025 estimates put ghost-job prevalence on LinkedIn at ~27%
#   (ResumeUp.AI analysis) and the broader online job market at 18-30% (Greenhouse 2025,
#   Congressional Research Service IF12977).
#
# RED_FLAGS as MULTIPLIER (not additive)
#   Rationale: red flags should be able to torpedo an otherwise-good score, not just chip
#   away at it. A pays-in-equity-only posting with a 5/5 cv_match should not score 4.0 just
#   because four sub-scores are high; the multiplier lets a 0.5 penalty halve the score.
#   Caller is responsible for choosing penalty magnitude (catalog in match-quality-rubric).
#
WEIGHT_CV_MATCH = 0.35
WEIGHT_COMP = 0.25
WEIGHT_CULTURAL = 0.20
WEIGHT_LEGITIMACY = 0.20

assert abs(
    (WEIGHT_CV_MATCH + WEIGHT_COMP + WEIGHT_CULTURAL + WEIGHT_LEGITIMACY) - 1.0
) < 1e-9, "additive weights must sum to 1.0"

# Recommendation thresholds match career-ops's "below 4.0 = recommend against" + a soft band.
THRESHOLD_APPLY = 4.0
THRESHOLD_SPECIFIC_REASON = 3.5


@dataclass
class ScoredPosting:
    cv_match: float
    comp_vs_target: float
    cultural_signals: float
    posting_legitimacy: float
    red_flags_penalty: float
    weighted_global: float
    recommendation: str
    notes: list[str]


SUB_SCORE_KEYS = ("cv_match", "comp_vs_target", "cultural_signals", "posting_legitimacy")
PENALTY_KEY = "red_flags_penalty"


def _clamp(value: float, lo: float, hi: float, name: str, notes: list[str]) -> float:
    if value < lo:
        notes.append(f"{name}={value} clamped to {lo} (below minimum)")
        return lo
    if value > hi:
        notes.append(f"{name}={value} clamped to {hi} (above maximum)")
        return hi
    return value


def _coerce_float(value: Any, name: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a number, got bool")
    if isinstance(value, (int, float)):
        return float(value)
    raise ValueError(f"{name} must be a number, got {type(value).__name__}")


def _recommendation(global_score: float) -> str:
    if global_score >= THRESHOLD_APPLY:
        return "apply"
    if global_score >= THRESHOLD_SPECIFIC_REASON:
        return "apply_if_specific_reason"
    return "skip"


def score_posting(sub_scores: dict) -> ScoredPosting:
    """Score a single posting from a dict of sub-scores.

    Required keys: cv_match, comp_vs_target, cultural_signals, posting_legitimacy
    Optional: red_flags_penalty (defaults to 0.0 = no penalty)

    Sub-scores are clamped to [1.0, 5.0]; penalty is clamped to [0.0, 1.0].
    """
    if not isinstance(sub_scores, dict):
        raise ValueError(f"sub_scores must be an object, got {type(sub_scores).__name__}")

    missing = [k for k in SUB_SCORE_KEYS if k not in sub_scores]
    if missing:
        raise ValueError(f"missing required sub-score keys: {', '.join(missing)}")

    notes: list[str] = []

    cv = _clamp(_coerce_float(sub_scores["cv_match"], "cv_match"), 1.0, 5.0, "cv_match", notes)
    comp = _clamp(_coerce_float(sub_scores["comp_vs_target"], "comp_vs_target"),
                  1.0, 5.0, "comp_vs_target", notes)
    cultural = _clamp(_coerce_float(sub_scores["cultural_signals"], "cultural_signals"),
                      1.0, 5.0, "cultural_signals", notes)
    legitimacy = _clamp(_coerce_float(sub_scores["posting_legitimacy"], "posting_legitimacy"),
                        1.0, 5.0, "posting_legitimacy", notes)

    penalty_raw = sub_scores.get(PENALTY_KEY, 0.0)
    penalty = _clamp(_coerce_float(penalty_raw, PENALTY_KEY), 0.0, 1.0, PENALTY_KEY, notes)

    additive = (
        WEIGHT_CV_MATCH * cv
        + WEIGHT_COMP * comp
        + WEIGHT_CULTURAL * cultural
        + WEIGHT_LEGITIMACY * legitimacy
    )
    global_score = additive * (1.0 - penalty)
    global_score = round(global_score, 2)

    if penalty >= 0.5:
        notes.append(f"red_flags_penalty={penalty} significantly reduced the global score")

    return ScoredPosting(
        cv_match=cv,
        comp_vs_target=comp,
        cultural_signals=cultural,
        posting_legitimacy=legitimacy,
        red_flags_penalty=penalty,
        weighted_global=global_score,
        recommendation=_recommendation(global_score),
        notes=notes,
    )


def _load_input(args: argparse.Namespace) -> Any:
    if args.sub_scores:
        return json.loads(args.sub_scores)
    if args.sub_scores_file:
        with open(args.sub_scores_file, "r", encoding="utf-8") as f:
            return json.load(f)
    if args.stdin_marker:
        return json.load(sys.stdin)
    raise ValueError("provide --sub-scores, --sub-scores-file, or pipe JSON to stdin with '-'")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--sub-scores", help="inline JSON object or array of sub-scores")
    src.add_argument("--sub-scores-file", help="path to JSON object or array of sub-scores")
    src.add_argument("-", dest="stdin_marker", action="store_true",
                     help="read JSON from stdin")
    args = parser.parse_args(argv)

    try:
        payload = _load_input(args)
    except (OSError, json.JSONDecodeError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    try:
        if isinstance(payload, list):
            results = [asdict(score_posting(item)) for item in payload]
            print(json.dumps(results, indent=2))
        elif isinstance(payload, dict):
            print(json.dumps(asdict(score_posting(payload)), indent=2))
        else:
            print(f"error: input must be an object or array, got {type(payload).__name__}",
                  file=sys.stderr)
            return 2
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
