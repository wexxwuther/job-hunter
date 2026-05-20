"""
Tests for scripts/harvest_outcomes.py

Covers:
- Cold-start: <5 outcomes returns no_op_reason and empty signals
- Empty workspace returns no_op
- 5+ outcomes with no dominant pattern returns empty signals
- 5+ outcomes with a dominant rejection reason emits the signal
- Recommendation calibration: counts true_positive, false_positive, false_negative
- Parse handles entries with missing optional fields
- CLI writes to --out or stdout

Run from skill root:
    python -m pytest tests/test_harvest_outcomes.py -v
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).parent.parent
SCRIPT = SKILL_ROOT / "scripts" / "harvest_outcomes.py"
sys.path.insert(0, str(SCRIPT.parent))

from harvest_outcomes import (  # noqa: E402
    MIN_CLOSED_OUTCOMES,
    POSITIVE_OUTCOMES,
    _has_user_decisions,
    harvest,
    parse_outcomes,
)
from init_workspace import init_workspace  # noqa: E402


# ---- Fixtures --------------------------------------------------------------


def _make_outcome_entry(company: str, outcome: str, reason: str = "",
                        agent_rec: str = "apply") -> str:
    """Synthesize one OUTCOMES.md entry block in the documented format."""
    return (
        f"## {company} — Senior Role — 2026-06-01\n\n"
        f"**Posting URL:** https://example.com/{company.lower()}\n"
        f"**Agent recommendation at time of apply:** {agent_rec}\n"
        f"**Outcome:** {outcome}\n"
        f"**Reason (yours or theirs):** {reason}\n\n"
    )


def _write_outcomes(workspace: Path, entries: list[str]) -> None:
    """Drop entries into .job-hunter/OUTCOMES.md after init."""
    init_workspace(workspace)
    path = workspace / ".job-hunter" / "OUTCOMES.md"
    existing = path.read_text(encoding="utf-8")
    path.write_text(existing + "\n" + "\n".join(entries), encoding="utf-8")


# ---- Cold-start guard ------------------------------------------------------


def test_empty_workspace_returns_no_op(tmp_path: Path):
    result = harvest(tmp_path)
    assert result["outcomes_found"] == 0
    assert result["signals"] == []
    assert "no_op_reason" in result
    assert "need >=5" in result["no_op_reason"]


def test_initialized_but_empty_outcomes_returns_no_op(tmp_path: Path):
    init_workspace(tmp_path)
    result = harvest(tmp_path)
    assert result["outcomes_found"] == 0
    assert result["signals"] == []
    assert "have 0" in result["no_op_reason"]


def test_three_outcomes_below_threshold_returns_no_op(tmp_path: Path):
    _write_outcomes(tmp_path, [
        _make_outcome_entry("Acme", "rejected_after_screen", "comp below target"),
        _make_outcome_entry("Beta", "rejected_after_screen", "comp below target"),
        _make_outcome_entry("Gamma", "rejected_after_screen", "comp below target"),
    ])
    result = harvest(tmp_path)
    assert result["outcomes_found"] == 3
    assert result["signals"] == []
    assert "have 3" in result["no_op_reason"]


# ---- Dominant rejection reason ---------------------------------------------


def test_five_rejections_with_dominant_comp_reason_emits_signal(tmp_path: Path):
    """4 of 5 rejections cite comp → dominant pattern surfaces."""
    _write_outcomes(tmp_path, [
        _make_outcome_entry("Acme", "rejected_after_screen", "comp below target"),
        _make_outcome_entry("Beta", "rejected_after_screen", "pay was too low"),
        _make_outcome_entry("Gamma", "rejected_after_screen", "salary not enough"),
        _make_outcome_entry("Delta", "rejected_after_screen", "comp below target"),
        _make_outcome_entry("Epsilon", "rejected_after_screen", "team fit was off"),
    ])
    result = harvest(tmp_path)
    assert result["outcomes_found"] == 5

    rejection_signals = [s for s in result["signals"] if s["kind"] == "rejection_dominant_reason"]
    assert len(rejection_signals) == 1
    signal = rejection_signals[0]
    assert signal["category"] == "comp"
    assert signal["matches"] == 4
    assert signal["evidence_count"] == 5
    assert signal["fraction"] == 0.8


def test_five_rejections_with_diffuse_reasons_no_dominant_signal(tmp_path: Path):
    """No reason dominates 50%+ → no dominant-reason signal."""
    _write_outcomes(tmp_path, [
        _make_outcome_entry("Acme", "rejected_after_screen", "comp"),
        _make_outcome_entry("Beta", "rejected_after_screen", "culture fit"),
        _make_outcome_entry("Gamma", "rejected_after_screen", "remote policy"),
        _make_outcome_entry("Delta", "rejected_after_screen", "wrong seniority"),
        _make_outcome_entry("Epsilon", "rejected_after_screen", "ghosted"),
    ])
    result = harvest(tmp_path)
    rejection_signals = [s for s in result["signals"] if s["kind"] == "rejection_dominant_reason"]
    assert rejection_signals == [], \
        "No category hits 50% — should emit no dominant-reason signal"


# ---- Recommendation calibration --------------------------------------------


def test_recommendation_calibration_computes_precision(tmp_path: Path):
    """5 entries, 3 apply→accept, 1 apply→reject, 1 skip→accept → precision = 0.75."""
    _write_outcomes(tmp_path, [
        _make_outcome_entry("Acme", "accepted_offer", agent_rec="apply"),
        _make_outcome_entry("Beta", "accepted_offer", agent_rec="apply"),
        _make_outcome_entry("Gamma", "accepted_offer", agent_rec="apply"),
        _make_outcome_entry("Delta", "rejected_after_screen", agent_rec="apply"),
        _make_outcome_entry("Epsilon", "accepted_offer", agent_rec="skip"),
    ])
    result = harvest(tmp_path)
    cal_signals = [s for s in result["signals"] if s["kind"] == "recommendation_calibration"]
    assert len(cal_signals) == 1
    cal = cal_signals[0]
    assert cal["true_positive"] == 3
    assert cal["false_positive"] == 1
    assert cal["false_negative"] == 1
    assert abs(cal["precision"] - 0.75) < 1e-9


def test_calibration_skipped_when_agent_rec_missing(tmp_path: Path):
    """If entries lack agent_rec field, calibration signal is omitted."""
    init_workspace(tmp_path)
    path = tmp_path / ".job-hunter" / "OUTCOMES.md"
    # Write 5 entries WITHOUT the agent recommendation line
    entries = []
    for i in range(5):
        entries.append(
            f"## Acme{i} — Senior — 2026-06-01\n\n"
            f"**Posting URL:** https://example.com/{i}\n"
            f"**Outcome:** accepted_offer\n"
            f"**Reason (yours or theirs):** great fit\n\n"
        )
    path.write_text(path.read_text() + "\n" + "\n".join(entries), encoding="utf-8")
    result = harvest(tmp_path)
    cal_signals = [s for s in result["signals"] if s["kind"] == "recommendation_calibration"]
    assert cal_signals == []


# ---- Parser behavior -------------------------------------------------------


def test_parse_skips_template_preamble():
    """Entries are only emitted from `## ` blocks, not the preamble."""
    text = (
        "# Outcomes — what actually happened\n\n"
        "Some preamble that includes the literal word **Outcome:** as a doc example.\n"
    )
    entries = parse_outcomes(text)
    assert entries == [], "preamble must not be parsed as an entry"


def test_parse_skips_entries_with_unrecognized_outcome():
    """Junk outcome values are silently skipped, not treated as valid data."""
    text = (
        "## Acme — Role — 2026-06-01\n\n"
        "**Outcome:** something_weird\n"
        "**Reason:** test\n"
    )
    entries = parse_outcomes(text)
    assert entries == []


def test_parse_handles_missing_optional_fields():
    """Entries with only the outcome field still parse, missing optionals are absent."""
    text = (
        "## Acme — Role — 2026-06-01\n\n"
        "**Outcome:** accepted_offer\n"
    )
    entries = parse_outcomes(text)
    assert len(entries) == 1
    assert entries[0]["outcome"] == "accepted_offer"
    assert "reason" not in entries[0]
    assert "agent_rec" not in entries[0]


# ---- decisions_present flag -------------------------------------------------


def test_decisions_present_false_when_only_template(tmp_path: Path):
    """Regression test (E2E-2 finding): an empty template should NOT count as
    'decisions present'. The template's privacy notice and docs are not user
    content. The flag should only flip to true after the append marker."""
    init_workspace(tmp_path)
    result = harvest(tmp_path)
    assert result["decisions_present"] is False, (
        "decisions_present must be False when DECISIONS.md only contains the "
        "template scaffolding (no user/agent entries after the append marker)"
    )


def test_decisions_present_true_when_user_appended_entry(tmp_path: Path):
    init_workspace(tmp_path)
    path = tmp_path / ".job-hunter" / "DECISIONS.md"
    text = path.read_text(encoding="utf-8")
    new_text = text + "\n## 2026-06-15 — Skipped Acme\n\n**Reason:** location\n"
    path.write_text(new_text, encoding="utf-8")
    result = harvest(tmp_path)
    assert result["decisions_present"] is True


def test_has_user_decisions_marker_missing_fallback():
    """If the append marker has been hand-deleted, fall back to looking for
    any dated entry heading. Empty body → False. Body with dated entry → True."""
    assert _has_user_decisions("") is False
    assert _has_user_decisions("just some preamble without marker") is False
    assert _has_user_decisions(
        "preamble\n\n## 2026-06-15 — Decided X\n**Reason:** because\n"
    ) is True


# ---- CLI tests --------------------------------------------------------------


def test_cli_emits_json_to_stdout(tmp_path: Path):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--workspace", str(tmp_path)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    payload = json.loads(result.stdout)
    assert payload["outcomes_found"] == 0
    assert "no_op_reason" in payload


def test_cli_writes_to_out_file(tmp_path: Path):
    out_path = tmp_path / "signals.json"
    result = subprocess.run(
        [sys.executable, str(SCRIPT),
         "--workspace", str(tmp_path), "--out", str(out_path)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert out_path.is_file()
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["outcomes_found"] == 0
