"""
Tests for scripts/generate_tracker_html.py

Covers:
- Backward compat: rows without score_breakdown render with legacy match-strength tag only
- New v4 rendering: rows with score_breakdown produce the score badge + expandable
  sub-score breakdown + filter bar + interactive JS
- Sort order: weighted_global descending when any row has a score
- CL43 drift test: the CSS asset file is the source of truth for tracker styles

Run from skill root:
    python -m pytest tests/test_generate_tracker_html.py -v
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "scripts" / "generate_tracker_html.py"
CSS_ASSET = Path(__file__).parent.parent / "assets" / "templates" / "tracker.css"
sys.path.insert(0, str(SCRIPT.parent))

from generate_tracker_html import render  # noqa: E402


LEGACY_POSTING = {
    "company": "Stripe",
    "title": "Senior PM, Payments",
    "url": "https://stripe.com/jobs/1",
    "location": "Remote / US",
    "salary": "$200k-260k",
    "posted": "2026-04-22",
    "status": "applied",
    "resume_file": "Resume_Stripe.docx",
    "cover_letter_file": "CoverLetter_Stripe.docx",
    "notes": "Strong match.",
    "match_strength": "Strong",
}

SCORED_POSTING = dict(LEGACY_POSTING, score_breakdown={
    "cv_match": 4.5,
    "comp_vs_target": 4.5,
    "cultural_signals": 4.0,
    "posting_legitimacy": 5.0,
    "red_flags_penalty": 0.0,
    "weighted_global": 4.5,
    "recommendation": "apply",
})

LOW_SCORED_POSTING = dict(LEGACY_POSTING, company="GhostCo",
                          title="Suspicious Role", url="https://ghost.example/1",
                          match_strength="Possible",
                          score_breakdown={
                              "cv_match": 4.0,
                              "comp_vs_target": 4.0,
                              "cultural_signals": 3.0,
                              "posting_legitimacy": 2.0,
                              "red_flags_penalty": 0.0,
                              "weighted_global": 3.3,
                              "recommendation": "skip",
                          })

PENALTY_POSTING = dict(LEGACY_POSTING, company="EquityOnly",
                       title="Founding PM (equity)", url="https://equity.example/1",
                       score_breakdown={
                           "cv_match": 5.0,
                           "comp_vs_target": 5.0,
                           "cultural_signals": 5.0,
                           "posting_legitimacy": 5.0,
                           "red_flags_penalty": 0.5,
                           "weighted_global": 2.5,
                           "recommendation": "skip",
                       })


# ---- Backward-compat tests --------------------------------------------------


def test_legacy_input_renders_without_score_badge():
    out = render([LEGACY_POSTING])
    assert 'class="score-badge' not in out
    assert 'class="match match-strong"' in out
    assert "Strong" in out


def test_legacy_input_omits_filter_bar():
    """When no row has a score_breakdown, the filter bar (score-axis controls) shouldn't
    render — it would be useless and confusing."""
    out = render([LEGACY_POSTING])
    assert '<div class="filters">' not in out
    assert 'Min score:' not in out


def test_legacy_input_omits_interactive_js():
    """No filter, no expand — no JS payload."""
    out = render([LEGACY_POSTING])
    assert '<script>' not in out


def test_legacy_header_says_match():
    out = render([LEGACY_POSTING])
    assert '<th>Match</th>' in out


# ---- New v4 rendering tests ------------------------------------------------


def test_scored_input_renders_score_badge():
    out = render([SCORED_POSTING])
    assert 'class="score-badge score-apply"' in out
    assert '4.5' in out
    assert 'Apply' in out


def test_scored_input_renders_subscore_grid():
    out = render([SCORED_POSTING])
    assert 'class="subscore-grid"' in out
    assert 'CV match' in out
    assert 'Comp vs target' in out
    assert 'Cultural signals' in out
    assert 'Posting legitimacy' in out


def test_scored_input_renders_filter_bar():
    out = render([SCORED_POSTING])
    assert '<div class="filters">' in out
    assert 'Apply only' in out
    assert 'Min score:' in out
    assert 'id="min-score"' in out


def test_scored_input_includes_js():
    out = render([SCORED_POSTING])
    assert '<script>' in out
    assert 'data-filter' in out
    assert 'setupExpand' in out
    assert 'setupFilter' in out


def test_scored_header_says_score():
    out = render([SCORED_POSTING])
    assert 'Score / Match' in out


def test_skip_recommendation_renders_grey():
    out = render([LOW_SCORED_POSTING])
    assert 'class="score-badge score-skip"' in out
    assert 'Skip' in out


def test_specific_reason_renders_amber():
    item = dict(SCORED_POSTING, score_breakdown=dict(
        SCORED_POSTING["score_breakdown"],
        weighted_global=3.7,
        recommendation="apply_if_specific_reason",
    ))
    out = render([item])
    assert 'class="score-badge score-specific"' in out
    assert 'Apply if reason' in out


def test_penalty_row_shows_when_nonzero():
    out = render([PENALTY_POSTING])
    assert 'subscore-penalty' in out
    assert 'Red-flag penalty' in out
    # 0.5 penalty -> -50%
    assert '50%' in out


def test_penalty_row_hidden_when_zero():
    """The penalty *div* must not be rendered for zero-penalty postings. The CSS class
    name will appear in the bundled stylesheet — check for the div tag, not the selector."""
    out = render([SCORED_POSTING])
    assert '<div class="subscore-penalty">' not in out
    assert 'Red-flag penalty' not in out


def test_data_attributes_for_filter():
    """The interactive JS reads data-score and data-rec from each row. If these go missing,
    the filter silently breaks. This is a load-bearing safety test."""
    out = render([SCORED_POSTING, LOW_SCORED_POSTING])
    assert 'data-score="4.50"' in out
    assert 'data-rec="apply"' in out
    assert 'data-score="3.30"' in out
    assert 'data-rec="skip"' in out


# ---- Sort order tests -------------------------------------------------------


def test_sort_by_weighted_global_descending():
    """When multiple rows have scores, the highest weighted_global must come first.
    This is the user-facing promise of 'sort by score by default'."""
    items = [LOW_SCORED_POSTING, SCORED_POSTING, PENALTY_POSTING]
    out = render(items)
    # Stripe (4.5) appears before GhostCo (3.3) appears before EquityOnly (2.5)
    stripe_idx = out.find("Stripe")
    ghost_idx = out.find("GhostCo")
    equity_idx = out.find("EquityOnly")
    assert 0 < stripe_idx < ghost_idx < equity_idx, (
        f"Sort order wrong: stripe={stripe_idx}, ghost={ghost_idx}, equity={equity_idx}"
    )


def test_mixed_scored_and_unscored_puts_scored_first():
    """If only some rows have scores, the scored ones come first (sort_key tuple's first
    element is 0 for scored, 1 for unscored)."""
    out = render([LEGACY_POSTING, SCORED_POSTING])
    # SCORED_POSTING is Stripe; LEGACY_POSTING is also Stripe. Differentiate by giving
    # legacy a different company name for this test.
    legacy = dict(LEGACY_POSTING, company="LegacyCo")
    out = render([legacy, SCORED_POSTING])
    # Stripe (scored 4.5) before LegacyCo (no score)
    assert 0 < out.find("Stripe") < out.find("LegacyCo")


# ---- CL43 drift test: CSS asset is the source of truth ---------------------


def test_css_asset_exists():
    """The CSS lives in the asset file, not inline in the script. If anyone moves the CSS
    back inline, this test fails. (failure mode #14 / CL43 mitigation)"""
    assert CSS_ASSET.exists(), f"tracker.css asset missing at {CSS_ASSET}"


def test_css_asset_loaded_into_output():
    """Specific declarations from tracker.css must appear in the rendered HTML output.
    If the script bundles inline CSS that has drifted from the asset, this catches it."""
    css_text = CSS_ASSET.read_text(encoding="utf-8")
    out = render([SCORED_POSTING])
    # Pick a few load-bearing declarations: these define the score badge, the bar fill, the
    # filter UI, and the expand-row mechanism — all things the script promises in its
    # docstring.
    load_bearing_selectors = [
        ".score-badge",
        ".score-apply",
        ".score-specific",
        ".score-skip",
        ".subscore-bar-fill",
        ".score-detail-row.expanded",
        ".filters button",
    ]
    for selector in load_bearing_selectors:
        assert selector in css_text, (
            f"Asset CSS is missing load-bearing selector '{selector}'"
        )
        assert selector in out, (
            f"Rendered HTML is missing load-bearing selector '{selector}' — "
            f"asset and script have drifted apart"
        )


def test_script_has_no_inline_css_block():
    """Past iteration v4, the script must NOT contain a top-level CSS = '...' string.
    All CSS lives in assets/templates/tracker.css. If a refactor inlines the CSS back into
    the script, this test fails and points at the asset file as the canonical home."""
    script_text = (Path(__file__).parent.parent / "scripts" /
                   "generate_tracker_html.py").read_text(encoding="utf-8")
    # Allow comments mentioning CSS; reject a top-level CSS = "..." assignment of >200 chars
    # (the old inline block was ~1.5KB).
    import re
    css_assignments = re.findall(r'^CSS\s*=\s*["\'](.+?)["\']', script_text,
                                 re.MULTILINE | re.DOTALL)
    big_assignments = [a for a in css_assignments if len(a) > 200]
    assert not big_assignments, (
        f"generate_tracker_html.py contains an inline CSS = '...' block of "
        f"{len(big_assignments[0])} chars; the asset file at "
        f"assets/templates/tracker.css is the source of truth (CL43)"
    )


# ---- Error-path tests ------------------------------------------------------


def test_empty_list_renders_empty_table():
    out = render([])
    assert '<table>' in out
    assert '0 positions tracked' in out


def test_non_list_raises():
    with pytest.raises(ValueError):
        render({"not": "a list"})


def test_non_dict_item_raises():
    with pytest.raises(ValueError):
        render(["not a dict"])


# ---- CLI smoke test --------------------------------------------------------


def test_cli_writes_file(tmp_path):
    inp = tmp_path / "in.json"
    out = tmp_path / "tracker.html"
    inp.write_text(json.dumps([SCORED_POSTING, LEGACY_POSTING]))
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(inp), "--out", str(out)],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert 'class="score-badge' in content
    assert 'Application Tracker' in content
