#!/usr/bin/env python3
"""
generate_tracker_html.py

Render the Phase-4 Application Tracker HTML from a list of targeted positions. Bundles a
clean inline-CSS template (from assets/templates/tracker.css) so the file is fully self-
contained (no external assets, opens correctly when emailed or shared).

Input JSON shape (the file the agent maintains across Phase 3 and Phase 4):
[
  {
    "company": "Stripe",
    "title": "Senior Product Manager, Payments",
    "url": "https://stripe.com/jobs/listing/123",
    "location": "Remote / US",
    "salary": "$200k-260k",
    "posted": "2026-04-22",
    "status": "applied",
    "resume_file": "Resume_Stripe_SeniorPM.docx",
    "cover_letter_file": "CoverLetter_Stripe_SeniorPM.docx",
    "notes": "Strong match on payments background; emphasize platform-thinking in interview.",
    "match_strength": "Strong",
    "score_breakdown": {
      "cv_match": 4.5,
      "comp_vs_target": 4.5,
      "cultural_signals": 4.0,
      "posting_legitimacy": 5.0,
      "red_flags_penalty": 0.0,
      "weighted_global": 4.5,
      "recommendation": "apply"
    }
  },
  ...
]

`score_breakdown` is OPTIONAL (added in iteration v4); rows without it render as before.
When present, it produces an expandable sub-score breakdown row and the global score is
shown as the primary at-a-glance signal. Default sort is by weighted_global descending.

Status values: "to apply", "applied", "interviewing", "offer", "rejected", "withdrawn".
Match strength: "Strong", "Good", "Possible" (case-insensitive). Used as the at-a-glance
tag when score_breakdown is absent.

Usage:
    python generate_tracker_html.py tracker.json --out ApplicationTracker.html
    cat tracker.json | python generate_tracker_html.py - --out ApplicationTracker.html
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from datetime import datetime
from pathlib import Path


CSS_ASSET = Path(__file__).parent.parent / "assets" / "templates" / "tracker.css"


def _load_css() -> str:
    """Load the CSS asset. Failure here is an installation bug (asset missing), not a
    user-input problem — surface it loudly so the user knows the install is broken."""
    if not CSS_ASSET.exists():
        raise FileNotFoundError(
            f"tracker.css asset missing at {CSS_ASSET}. The skill install is broken; "
            f"reinstall via .install.ps1 or copy assets/templates/tracker.css from source."
        )
    return CSS_ASSET.read_text(encoding="utf-8")


def _status_class(status: str) -> str:
    return "status-" + status.lower().replace(" ", "")


def _match_class(strength: str) -> str:
    s = strength.lower().strip()
    if s == "strong":
        return "match-strong"
    if s == "good":
        return "match-good"
    return "match-possible"


def _recommendation_class(rec: str) -> str:
    if rec == "apply":
        return "score-apply"
    if rec == "apply_if_specific_reason":
        return "score-specific"
    return "score-skip"


def _recommendation_label(rec: str) -> str:
    return {
        "apply": "Apply",
        "apply_if_specific_reason": "Apply if reason",
        "skip": "Skip",
    }.get(rec, rec)


def _bar_class(value: float) -> str:
    if value < 2.5:
        return "low"
    if value < 4.0:
        return "mid"
    return "high"


def _safe(value, default: str = "") -> str:
    if value is None or value == "":
        return default
    return html.escape(str(value))


def _file_links(item: dict) -> str:
    parts = []
    for label, key in (("Resume", "resume_file"), ("Cover Letter", "cover_letter_file")):
        f = item.get(key)
        if f:
            parts.append(f'<a href="{html.escape(f)}">{label}</a>')
    return "".join(parts) or "&mdash;"


def _count_by(items: list[dict], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        val = (item.get(key) or "unknown").strip().lower()
        counts[val] = counts.get(val, 0) + 1
    return counts


def _render_score_badge(breakdown: dict | None) -> str:
    """Primary at-a-glance signal. When score_breakdown is absent, fall back to the legacy
    match-strength tag for backward compat."""
    if not breakdown:
        return ""
    global_score = breakdown.get("weighted_global")
    rec = breakdown.get("recommendation", "skip")
    if global_score is None:
        return ""
    return (
        f'<span class="score-badge {_recommendation_class(rec)}" '
        f'data-row-toggle title="Click to expand sub-score breakdown">'
        f'{global_score:.1f}'
        f'<span class="rec-arrow">{html.escape(_recommendation_label(rec))}</span>'
        f'</span>'
    )


def _render_subscore_row(breakdown: dict) -> str:
    """Expandable row showing the 5 sub-scores as horizontal bars."""
    rows = []
    for label, key, scale_max in (
        ("CV match", "cv_match", 5.0),
        ("Comp vs target", "comp_vs_target", 5.0),
        ("Cultural signals", "cultural_signals", 5.0),
        ("Posting legitimacy", "posting_legitimacy", 5.0),
    ):
        v = breakdown.get(key)
        if v is None:
            continue
        v = float(v)
        pct = (v / scale_max) * 100
        bar_cls = _bar_class(v)
        rows.append(
            f'<div class="subscore-row">'
            f'  <div class="subscore-label">{label}</div>'
            f'  <div class="subscore-bar-track">'
            f'    <div class="subscore-bar-fill {bar_cls}" style="width: {pct:.1f}%"></div>'
            f'  </div>'
            f'  <div class="subscore-value">{v:.1f}</div>'
            f'</div>'
        )

    penalty = breakdown.get("red_flags_penalty")
    penalty_html = ""
    if penalty is not None and float(penalty) > 0:
        penalty_html = (
            f'<div class="subscore-penalty">'
            f'Red-flag penalty: −{float(penalty):.0%} (multiplier applied to global)'
            f'</div>'
        )

    return f'<div class="subscore-grid">{"".join(rows)}</div>{penalty_html}'


def _has_any_score_breakdown(items: list[dict]) -> bool:
    return any(item.get("score_breakdown") for item in items)


def _sort_key(item: dict) -> tuple:
    """Sort by weighted_global descending if present, else by match_strength order."""
    breakdown = item.get("score_breakdown") or {}
    global_score = breakdown.get("weighted_global")
    if global_score is not None:
        return (0, -float(global_score))
    match_order = {"strong": 0, "good": 1, "possible": 2}
    m = (item.get("match_strength") or "possible").lower().strip()
    return (1, match_order.get(m, 3))


def render(items: list[dict], generated_at: str | None = None) -> str:
    if not isinstance(items, list):
        raise ValueError("input must be a JSON array of application objects")
    if not items:
        items = []

    # Validate item types BEFORE sort/render so type errors surface as ValueError, not as
    # an internal AttributeError from inside _sort_key.
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"each item must be an object, got {type(item).__name__} at index {i}")

    generated_at = generated_at or datetime.now().strftime("%Y-%m-%d %H:%M")

    # Sort by score before rendering.
    items = sorted(items, key=_sort_key)

    show_scores = _has_any_score_breakdown(items)
    css = _load_css()

    status_counts = _count_by(items, "status")
    status_summary = ", ".join(
        f"{count} {name}" for name, count in sorted(status_counts.items(), key=lambda x: -x[1])
    ) if status_counts else "no applications yet"

    rows: list[str] = []
    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"each item must be an object, got {type(item).__name__}")
        company = _safe(item.get("company"), "&mdash;")
        title = _safe(item.get("title"), "&mdash;")
        url = item.get("url", "")
        title_html = (f'<a href="{html.escape(url)}" target="_blank" rel="noopener">'
                      f'{title}</a>') if url else title
        status = _safe(item.get("status"), "to apply")
        status_lower = (item.get("status") or "to apply").lower()
        match = _safe(item.get("match_strength"), "Possible")
        match_class = _match_class(item.get("match_strength", "Possible"))
        location = _safe(item.get("location"), "&mdash;")
        salary = _safe(item.get("salary"), "&mdash;")
        posted = _safe(item.get("posted"), "&mdash;")
        # v5.1.1: applied_date is the canonical field for WHEN THE USER APPLIED,
        # distinct from `posted` (when the company posted the role). The agent
        # should set this when status moves to 'applied'. scan-stale in
        # draft_followup.py reads ONLY this field — see SKILL.md Phase 4.
        applied_date = _safe(item.get("applied_date"), "&mdash;")
        notes = _safe(item.get("notes"), "")
        files = _file_links(item)

        breakdown = item.get("score_breakdown")
        score_cell = _render_score_badge(breakdown) if show_scores else ""
        match_cell = f'<span class="match {match_class}">{match}</span>'

        # The score column replaces the match column when any row has scores; when no rows
        # have scores at all, we fall back to the legacy match-only column to preserve
        # backward compatibility with existing tracker.json files.
        score_col_data = (
            f'data-score="{breakdown["weighted_global"]:.2f}" '
            f'data-rec="{breakdown.get("recommendation", "")}"'
        ) if (breakdown and breakdown.get("weighted_global") is not None) else ""

        rows.append(f"""
        <tr class="posting-row" data-row-id="{idx}" {score_col_data}>
          <td><strong>{company}</strong></td>
          <td>{title_html}</td>
          <td>{location}</td>
          <td>{salary}</td>
          <td>{posted}</td>
          <td>{applied_date}</td>
          {'<td>' + score_cell + ' ' + match_cell + '</td>' if show_scores else '<td>' + match_cell + '</td>'}
          <td><span class="status {_status_class(status_lower)}">{status}</span></td>
          <td class="files">{files}</td>
          <td class="notes">{notes}</td>
        </tr>""")

        if show_scores and breakdown:
            rows.append(f"""
        <tr class="score-detail-row" data-detail-for="{idx}">
          <td colspan="9">{_render_subscore_row(breakdown)}</td>
        </tr>""")

    pills = "".join(
        f'<div class="pill"><strong>{count}</strong> {name}</div>'
        for name, count in sorted(status_counts.items(), key=lambda x: -x[1])
    )

    filter_bar = ""
    if show_scores:
        filter_bar = """
<div class="filters">
  <label>Filter:</label>
  <button data-filter="all" class="active">All</button>
  <button data-filter="apply">Apply only</button>
  <button data-filter="apply_if_specific_reason">+ if reason</button>
  <button data-filter="skip">+ skip</button>
  <label style="margin-left: 1rem;">Min score:</label>
  <input type="number" id="min-score" min="0" max="5" step="0.1" value="0">
</div>"""

    score_header = "Match" if not show_scores else "Score / Match"

    # Interactive JS for sort + filter + expand (self-contained, no external libs).
    js = """
<script>
(function() {
  function setupExpand() {
    document.querySelectorAll('.score-badge[data-row-toggle]').forEach(function(badge) {
      badge.addEventListener('click', function(e) {
        e.stopPropagation();
        var row = badge.closest('tr');
        var idx = row.getAttribute('data-row-id');
        var detail = document.querySelector('.score-detail-row[data-detail-for="' + idx + '"]');
        if (detail) detail.classList.toggle('expanded');
      });
    });
  }
  function setupFilter() {
    var buttons = document.querySelectorAll('.filters button[data-filter]');
    var minScore = document.getElementById('min-score');
    function apply() {
      var activeBtn = document.querySelector('.filters button[data-filter].active');
      var recFilter = activeBtn ? activeBtn.getAttribute('data-filter') : 'all';
      var minVal = minScore ? parseFloat(minScore.value) || 0 : 0;
      document.querySelectorAll('tr.posting-row').forEach(function(row) {
        var score = parseFloat(row.getAttribute('data-score') || '0');
        var rec = row.getAttribute('data-rec') || '';
        var matchesRec = (recFilter === 'all') || (rec === recFilter)
          || (recFilter === 'apply_if_specific_reason' && (rec === 'apply' || rec === 'apply_if_specific_reason'))
          || (recFilter === 'skip');
        var matchesScore = score >= minVal;
        var idx = row.getAttribute('data-row-id');
        var detail = document.querySelector('.score-detail-row[data-detail-for="' + idx + '"]');
        if (matchesRec && matchesScore) {
          row.classList.remove('hidden');
        } else {
          row.classList.add('hidden');
          if (detail) detail.classList.remove('expanded');
        }
      });
    }
    buttons.forEach(function(btn) {
      btn.addEventListener('click', function() {
        buttons.forEach(function(b) { b.classList.remove('active'); });
        btn.classList.add('active');
        apply();
      });
    });
    if (minScore) minScore.addEventListener('input', apply);
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() { setupExpand(); setupFilter(); });
  } else {
    setupExpand();
    setupFilter();
  }
})();
</script>"""

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Application Tracker</title>
<style>{css}</style>
</head>
<body>
<h1>Application Tracker</h1>
<div class="summary">{len(items)} positions tracked &middot; {status_summary} &middot;
generated {html.escape(generated_at)}</div>
<div class="totals">{pills}</div>
{filter_bar}
<table>
  <thead>
    <tr>
      <th>Company</th><th>Role</th><th>Location</th><th>Salary</th><th>Posted</th><th>Applied</th>
      <th>{score_header}</th><th>Status</th><th>Files</th><th>Notes</th>
    </tr>
  </thead>
  <tbody>{"".join(rows)}</tbody>
</table>
{js if show_scores else ""}
</body>
</html>
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="path to tracker JSON, or '-' for stdin")
    parser.add_argument("--out", required=True, help="output HTML path")
    args = parser.parse_args(argv)

    try:
        if args.input == "-":
            items = json.load(sys.stdin)
        else:
            with open(args.input, "r", encoding="utf-8") as f:
                items = json.load(f)
    except json.JSONDecodeError as e:
        print(f"error: invalid JSON: {e}", file=sys.stderr)
        return 2
    except OSError as e:
        print(f"error: cannot read input: {e}", file=sys.stderr)
        return 2

    try:
        html_out = render(items)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 3

    try:
        Path(args.out).write_text(html_out, encoding="utf-8")
    except OSError as e:
        print(f"error: cannot write output: {e}", file=sys.stderr)
        return 2

    print(f"wrote tracker for {len(items)} positions to {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
