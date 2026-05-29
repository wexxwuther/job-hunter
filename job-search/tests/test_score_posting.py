"""
Tests for scripts/score_posting.py

These tests are load-bearing safety tests: they encode the design intent behind the weight
choices and the red-flags-as-multiplier semantics. If a future refactor changes a weight
without updating the rationale, these tests should fail loudly.

Run from skill root:
    python -m pytest tests/test_score_posting.py -v
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "scripts" / "score_posting.py"
sys.path.insert(0, str(SCRIPT.parent))

from score_posting import (  # noqa: E402
    THRESHOLD_APPLY,
    THRESHOLD_SPECIFIC_REASON,
    WEIGHT_COMP,
    WEIGHT_CULTURAL,
    WEIGHT_CV_MATCH,
    WEIGHT_LEGITIMACY,
    score_posting,
)


PERFECT = {
    "cv_match": 5.0,
    "comp_vs_target": 5.0,
    "cultural_signals": 5.0,
    "posting_legitimacy": 5.0,
    "red_flags_penalty": 0.0,
}


# ---- Design-intent tests (load-bearing) ------------------------------------


def test_weights_sum_to_one():
    """If anyone changes a weight, the others must compensate. Module import asserts this
    too, but exercising it from the test suite makes the intent explicit."""
    total = WEIGHT_CV_MATCH + WEIGHT_COMP + WEIGHT_CULTURAL + WEIGHT_LEGITIMACY
    assert abs(total - 1.0) < 1e-9


def test_cv_match_is_heaviest_weight():
    """cv_match must be the single heaviest input. If a refactor demotes it, the skill
    starts recommending roles users would never get interviewed for."""
    assert WEIGHT_CV_MATCH > WEIGHT_COMP
    assert WEIGHT_CV_MATCH > WEIGHT_CULTURAL
    assert WEIGHT_CV_MATCH > WEIGHT_LEGITIMACY


def test_perfect_posting_scores_five():
    result = score_posting(PERFECT)
    assert result.weighted_global == 5.0
    assert result.recommendation == "apply"


def test_red_flag_torpedoes_perfect_score():
    """Pays-only-in-equity (penalty 0.5) on a 5/5 posting must drop it below the apply
    threshold. This is the load-bearing semantic: red flags multiply, not subtract."""
    posting = dict(PERFECT, red_flags_penalty=0.5)
    result = score_posting(posting)
    assert result.weighted_global == 2.5
    assert result.recommendation == "skip"


def test_full_penalty_zeros_score():
    """A penalty of 1.0 must zero the score, not produce a negative or wrap-around."""
    posting = dict(PERFECT, red_flags_penalty=1.0)
    result = score_posting(posting)
    assert result.weighted_global == 0.0
    assert result.recommendation == "skip"


# ---- Recommendation threshold tests ----------------------------------------


def test_apply_threshold_exact():
    """Score exactly at 4.0 should recommend apply (inclusive)."""
    posting = {
        "cv_match": 4.0,
        "comp_vs_target": 4.0,
        "cultural_signals": 4.0,
        "posting_legitimacy": 4.0,
        "red_flags_penalty": 0.0,
    }
    result = score_posting(posting)
    assert result.weighted_global == 4.0
    assert result.recommendation == "apply"


def test_specific_reason_band():
    """3.5-3.99 should recommend apply_if_specific_reason."""
    posting = {
        "cv_match": 3.5,
        "comp_vs_target": 3.5,
        "cultural_signals": 3.5,
        "posting_legitimacy": 3.5,
        "red_flags_penalty": 0.0,
    }
    result = score_posting(posting)
    assert result.weighted_global == 3.5
    assert result.recommendation == "apply_if_specific_reason"


def test_skip_below_threshold():
    posting = {
        "cv_match": 3.0,
        "comp_vs_target": 3.0,
        "cultural_signals": 3.0,
        "posting_legitimacy": 3.0,
        "red_flags_penalty": 0.0,
    }
    result = score_posting(posting)
    assert result.weighted_global == 3.0
    assert result.recommendation == "skip"


# ---- Input validation tests ------------------------------------------------


def test_clamps_above_five():
    posting = dict(PERFECT, cv_match=10.0)
    result = score_posting(posting)
    assert result.cv_match == 5.0
    assert any("clamped to 5.0" in note for note in result.notes)


def test_clamps_below_one():
    posting = dict(PERFECT, cv_match=0.0)
    result = score_posting(posting)
    assert result.cv_match == 1.0
    assert any("clamped to 1.0" in note for note in result.notes)


def test_clamps_negative_penalty():
    posting = dict(PERFECT, red_flags_penalty=-0.5)
    result = score_posting(posting)
    assert result.red_flags_penalty == 0.0


def test_clamps_penalty_above_one():
    posting = dict(PERFECT, red_flags_penalty=1.5)
    result = score_posting(posting)
    assert result.red_flags_penalty == 1.0


def test_missing_required_key_raises():
    posting = {k: 4.0 for k in ["cv_match", "comp_vs_target", "cultural_signals"]}
    with pytest.raises(ValueError, match="missing required sub-score keys"):
        score_posting(posting)


def test_penalty_optional_defaults_to_zero():
    posting = {k: 4.0 for k in
               ["cv_match", "comp_vs_target", "cultural_signals", "posting_legitimacy"]}
    result = score_posting(posting)
    assert result.red_flags_penalty == 0.0
    assert result.weighted_global == 4.0


def test_rejects_bool_input():
    """JSON nulls/booleans should be rejected, not silently coerced."""
    posting = dict(PERFECT, cv_match=True)
    with pytest.raises(ValueError, match="cv_match"):
        score_posting(posting)


def test_rejects_string_input():
    posting = dict(PERFECT, cv_match="4.0")
    with pytest.raises(ValueError, match="cv_match"):
        score_posting(posting)


def test_rejects_non_dict_input():
    with pytest.raises(ValueError, match="sub_scores must be an object"):
        score_posting([4.0, 4.0, 4.0, 4.0])


# ---- Directional sanity (flipping a sub-score flips the recommendation) ----


def test_dropping_legitimacy_can_drop_recommendation():
    """A 4.5 on everything except legitimacy=1.0 should land in the specific-reason band,
    not 'apply'. This is the load-bearing semantic from career-ops Block G."""
    posting = {
        "cv_match": 4.5,
        "comp_vs_target": 4.5,
        "cultural_signals": 4.5,
        "posting_legitimacy": 1.0,
        "red_flags_penalty": 0.0,
    }
    result = score_posting(posting)
    # 0.35*4.5 + 0.25*4.5 + 0.20*4.5 + 0.20*1.0 = 1.575 + 1.125 + 0.9 + 0.2 = 3.8
    assert result.weighted_global == 3.8
    assert result.recommendation == "apply_if_specific_reason"


def test_dropping_cv_match_torpedoes_recommendation():
    """cv_match=1.0 with others=5.0 should NOT recommend apply, because the heaviest
    weight is dragging hardest. This is the directional sanity test for failure-mode #6
    (voodoo constants)."""
    posting = {
        "cv_match": 1.0,
        "comp_vs_target": 5.0,
        "cultural_signals": 5.0,
        "posting_legitimacy": 5.0,
        "red_flags_penalty": 0.0,
    }
    result = score_posting(posting)
    # 0.35*1.0 + 0.25*5.0 + 0.20*5.0 + 0.20*5.0 = 0.35 + 1.25 + 1.0 + 1.0 = 3.6
    assert result.weighted_global == 3.6
    assert result.recommendation == "apply_if_specific_reason"


# ---- CLI smoke test --------------------------------------------------------


def test_cli_inline_input(tmp_path):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--sub-scores", json.dumps(PERFECT)],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0, result.stderr
    parsed = json.loads(result.stdout)
    assert parsed["weighted_global"] == 5.0
    assert parsed["recommendation"] == "apply"


def test_cli_file_input(tmp_path):
    p = tmp_path / "scored.json"
    p.write_text(json.dumps([PERFECT, dict(PERFECT, cv_match=1.0)]))
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--sub-scores-file", str(p)],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0, result.stderr
    parsed = json.loads(result.stdout)
    assert len(parsed) == 2
    assert parsed[0]["recommendation"] == "apply"
    assert parsed[1]["recommendation"] == "apply_if_specific_reason"


def test_cli_invalid_json_fails():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--sub-scores", "not json"],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 2
    assert "error" in result.stderr.lower()


# ---- Constants documented (CL45 load-bearing safety) -----------------------


def test_thresholds_match_career_ops_block_g():
    """career-ops Block G uses 4.0 as the 'apply immediately' threshold and 3.5 as the
    'apply only if specific reason' band. If anyone moves these, the skill loses its
    quality-over-quantity discipline."""
    assert THRESHOLD_APPLY == 4.0
    assert THRESHOLD_SPECIFIC_REASON == 3.5
