"""
Tests for scripts/propose_lessons.py

Covers:
- no_op_reason from signals.json is propagated through
- rejection_dominant_reason → properly-formatted lesson block with category-specific guidance
- recommendation_calibration with high precision → no suggestion (calibration is fine)
- recommendation_calibration with low precision → suggestion with concrete guidance
- Unknown signal kinds are silently skipped (forward-compatible)
- Suggestion always includes application_guidance reminding to surface to user
- Determinism: same input + same date → identical output
- CLI works with both --signals file and --signals-stdin
- Confidence escalates correctly with evidence_count

Run from skill root:
    python -m pytest tests/test_propose_lessons.py -v
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).parent.parent
SCRIPT = SKILL_ROOT / "scripts" / "propose_lessons.py"
sys.path.insert(0, str(SCRIPT.parent))

from propose_lessons import propose  # noqa: E402


# ---- no_op_reason propagation -----------------------------------------------


def test_no_op_reason_propagates_from_signals():
    signals = {
        "workspace": "/tmp/ws",
        "outcomes_found": 2,
        "signals": [],
        "no_op_reason": "need >=5 closed-loop outcomes, have 2",
    }
    result = propose(signals)
    assert result["suggestions"] == []
    assert "have 2" in result["no_op_reason"]
    # Application guidance must always be present, even on no-op
    assert "Never auto-write" in result["application_guidance"]


def test_empty_signals_with_no_no_op_returns_threshold_message():
    """If signals harvest returned [] without a no_op_reason, the proposal
    still emits a sensible no_op_reason instead of an empty proposal."""
    signals = {"workspace": "/tmp/ws", "signals": [], "no_op_reason": None}
    result = propose(signals)
    assert result["suggestions"] == []
    assert result["no_op_reason"] is not None


# ---- rejection_dominant_reason translation ---------------------------------


def test_rejection_comp_signal_produces_comp_specific_lesson():
    signals = {
        "workspace": "/tmp/ws",
        "signals": [{
            "kind": "rejection_dominant_reason",
            "category": "comp",
            "matches": 4,
            "evidence_count": 5,
            "fraction": 0.8,
        }],
    }
    result = propose(signals, today="2026-06-15")
    assert len(result["suggestions"]) == 1
    s = result["suggestions"][0]
    assert s["kind"] == "rejection_dominant_reason"
    assert "comp" in s["summary"].lower()
    assert "comp_vs_target" in s["lesson_block"], \
        "lesson must name the affected sub-score"
    # Lesson block must use the documented format
    assert "## 2026-06-15 — " in s["lesson_block"]
    assert "**Pattern:**" in s["lesson_block"]
    assert "**Evidence:**" in s["lesson_block"]
    assert "**How it shapes scoring:**" in s["lesson_block"]
    # Reason is anchored in evidence
    assert "4 of 5" in s["reason"]
    assert "80%" in s["reason"]


def test_rejection_size_signal_produces_size_specific_lesson():
    signals = {
        "workspace": "/tmp/ws",
        "signals": [{
            "kind": "rejection_dominant_reason",
            "category": "size",
            "matches": 7,
            "evidence_count": 9,
            "fraction": 7/9,
        }],
    }
    result = propose(signals, today="2026-06-15")
    s = result["suggestions"][0]
    assert "size" in s["summary"].lower() or "bureaucra" in s["summary"].lower()
    assert "cultural_signals" in s["lesson_block"]
    assert "1000 employees" in s["lesson_block"]


def test_rejection_unknown_category_emits_generic_lesson():
    """Forward-compatibility: a new category not in the canonical map still
    produces a reasonable lesson block."""
    signals = {
        "workspace": "/tmp/ws",
        "signals": [{
            "kind": "rejection_dominant_reason",
            "category": "stock_dilution",  # not in the canonical category_map
            "matches": 5,
            "evidence_count": 8,
            "fraction": 5/8,
        }],
    }
    result = propose(signals, today="2026-06-15")
    assert len(result["suggestions"]) == 1
    s = result["suggestions"][0]
    assert "stock_dilution" in s["lesson_block"]


# ---- recommendation_calibration translation --------------------------------


def test_high_precision_calibration_emits_no_suggestion():
    """If the agent is calibrated well (precision >= 0.7), don't propose
    a lesson — there's nothing to fix."""
    signals = {
        "workspace": "/tmp/ws",
        "signals": [{
            "kind": "recommendation_calibration",
            "evidence_count": 10,
            "true_positive": 8,
            "false_positive": 1,
            "false_negative": 1,
            "precision": 0.89,
        }],
    }
    result = propose(signals, today="2026-06-15")
    assert result["suggestions"] == []
    assert result["no_op_reason"] is not None


def test_low_precision_calibration_emits_tightening_suggestion():
    """If precision < 0.7, propose a lesson to tighten apply criteria."""
    signals = {
        "workspace": "/tmp/ws",
        "signals": [{
            "kind": "recommendation_calibration",
            "evidence_count": 10,
            "true_positive": 3,
            "false_positive": 5,
            "false_negative": 2,
            "precision": 0.375,
        }],
    }
    result = propose(signals, today="2026-06-15")
    assert len(result["suggestions"]) == 1
    s = result["suggestions"][0]
    assert s["kind"] == "recommendation_calibration"
    assert "37%" in s["summary"] or "38%" in s["summary"]
    assert "Tighten" in s["lesson_block"] or "tighten" in s["lesson_block"]


def test_calibration_missing_precision_skipped_silently():
    """If the signal somehow lacks precision (shouldn't happen but defensive),
    we skip it rather than crash."""
    signals = {
        "workspace": "/tmp/ws",
        "signals": [{
            "kind": "recommendation_calibration",
            "evidence_count": 10,
            "true_positive": 5,
            "false_positive": 5,
            "false_negative": 0,
            "precision": None,
        }],
    }
    result = propose(signals, today="2026-06-15")
    assert result["suggestions"] == []


# ---- Confidence tiers ------------------------------------------------------


@pytest.mark.parametrize("evidence,expected", [
    (5, "medium"),
    (9, "medium"),
    (10, "high"),
    (50, "high"),
    (3, "low"),  # below medium threshold
])
def test_confidence_levels_track_evidence_count(evidence: int, expected: str):
    signals = {
        "workspace": "/tmp/ws",
        "signals": [{
            "kind": "rejection_dominant_reason",
            "category": "comp",
            "matches": evidence,
            "evidence_count": evidence,
            "fraction": 1.0,
        }],
    }
    result = propose(signals, today="2026-06-15")
    assert result["suggestions"][0]["confidence"] == expected


# ---- Determinism + safety --------------------------------------------------


def test_unknown_signal_kind_silently_skipped():
    """Forward compatibility: a future harvest may emit signal kinds this
    propose script doesn't know. It must skip them, not crash."""
    signals = {
        "workspace": "/tmp/ws",
        "signals": [
            {"kind": "future_signal_kind_we_dont_know", "evidence_count": 100},
            {"kind": "rejection_dominant_reason", "category": "comp",
             "matches": 3, "evidence_count": 5, "fraction": 0.6},
        ],
    }
    result = propose(signals, today="2026-06-15")
    assert len(result["suggestions"]) == 1
    assert result["suggestions"][0]["kind"] == "rejection_dominant_reason"


def test_determinism_same_input_same_output():
    signals = {
        "workspace": "/tmp/ws",
        "signals": [{
            "kind": "rejection_dominant_reason",
            "category": "comp",
            "matches": 4,
            "evidence_count": 5,
            "fraction": 0.8,
        }],
    }
    a = propose(signals, today="2026-06-15")
    b = propose(signals, today="2026-06-15")
    assert a == b


def test_application_guidance_always_warns_against_auto_write():
    """The application_guidance string must remind callers (the agent) to
    never auto-write to LESSONS.md. This is a contract test."""
    signals = {"workspace": "/tmp/ws", "signals": []}
    result = propose(signals)
    assert "Never auto-write" in result["application_guidance"]
    assert "confirmation" in result["application_guidance"].lower()


# ---- CLI tests --------------------------------------------------------------


def test_cli_reads_signals_file(tmp_path: Path):
    signals_path = tmp_path / "signals.json"
    signals_path.write_text(json.dumps({
        "workspace": "/tmp/ws",
        "signals": [{
            "kind": "rejection_dominant_reason",
            "category": "comp",
            "matches": 4, "evidence_count": 5, "fraction": 0.8,
        }],
    }), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--signals", str(signals_path), "--today", "2026-06-15"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    payload = json.loads(result.stdout)
    assert len(payload["suggestions"]) == 1


def test_cli_reads_signals_stdin():
    signals = json.dumps({
        "workspace": "/tmp/ws",
        "signals": [{
            "kind": "rejection_dominant_reason",
            "category": "comp",
            "matches": 4, "evidence_count": 5, "fraction": 0.8,
        }],
    })
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--signals-stdin", "--today", "2026-06-15"],
        input=signals, capture_output=True, text=True,
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert len(payload["suggestions"]) == 1
