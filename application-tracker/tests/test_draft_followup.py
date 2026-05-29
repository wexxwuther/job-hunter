"""
Tests for scripts/draft_followup.py

Covers:
- check_in template renders with company/role/applied date
- thank_you template renders with conversation detail
- Generic 'thanks for your time' placeholder appears when no detail given (prompts user to add)
- Both templates fit under 150 words
- Salutation handles missing/unknown contact name gracefully
- when_phrase handles 'today' / 'yesterday' / 'N days ago' correctly
- scan-stale returns only status=applied entries older than threshold
- scan-stale handles both list-of-entries and {entries: [...]} tracker shapes
- scan-stale gracefully handles missing tracker / malformed JSON / missing date fields
- scan-stale's --today override gives deterministic test results
- CLI usable for both subcommands

Run from skill root:
    python -m pytest tests/test_draft_followup.py -v
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).parent.parent
SCRIPT = SKILL_ROOT / "scripts" / "draft_followup.py"
sys.path.insert(0, str(SCRIPT.parent))

from draft_followup import (  # noqa: E402
    DEFAULT_QUALIFICATION_LINE,
    DEFAULT_STALE_DAYS,
    USER_NAME_PLACEHOLDER,
    draft_check_in,
    draft_thank_you,
    scan_stale_applications,
)


# ---- check_in template -----------------------------------------------------


def test_check_in_includes_company_role_date():
    body = draft_check_in("Stripe", "Senior PM", "2026-05-10")
    assert "Stripe" in body
    assert "Senior PM" in body
    # Date should be rendered friendly, not raw ISO — but raw is OK fallback
    assert "May 10" in body or "2026-05-10" in body


def test_check_in_uses_default_qualification_placeholder():
    body = draft_check_in("Stripe", "Senior PM", "2026-05-10")
    assert "[Add one specific qualification" in body, (
        "default placeholder should prompt user to add a specific qualification"
    )


def test_check_in_accepts_custom_qualification():
    custom = "My work at Acme scaling payments from 10k to 1M requests/day."
    body = draft_check_in("Stripe", "Senior PM", "2026-05-10",
                          qualification=custom)
    assert custom in body
    assert "[Add one specific qualification" not in body


def test_check_in_salutation_unknown_contact():
    body = draft_check_in("Stripe", "Senior PM", "2026-05-10",
                          contact_name=None)
    assert "Hi there" in body


def test_check_in_salutation_known_contact():
    body = draft_check_in("Stripe", "Senior PM", "2026-05-10",
                          contact_name="Maria")
    assert "Hi Maria" in body


def test_check_in_under_150_words_with_placeholders():
    """The default-placeholder version should already be under the 150-word
    target. Once a user fills in placeholders with real text the count grows,
    but the skeleton should leave room."""
    body = draft_check_in("Stripe", "Senior PM", "2026-05-10")
    word_count = len(body.split())
    assert word_count < 150, f"check_in body is {word_count} words; target < 150"


def test_check_in_includes_user_name_placeholder():
    """The sign-off must remind the user to substitute their actual name."""
    body = draft_check_in("Stripe", "Senior PM", "2026-05-10")
    assert USER_NAME_PLACEHOLDER in body


# ---- thank_you template ----------------------------------------------------


def test_thank_you_with_conversation_detail():
    detail = "your team's move from monolith to event-driven"
    body = draft_thank_you("Stripe", "Senior PM",
                            interview_date="2026-05-18",
                            conversation_detail=detail)
    assert detail in body
    assert "Stripe" in body
    assert "Senior PM" in body


def test_thank_you_without_detail_prompts_user_to_add_one():
    """If the user didn't provide a detail, the placeholder should explicitly
    push them to add one — generic 'thanks for your time' lines are why
    thank-you notes get ignored."""
    body = draft_thank_you("Stripe", "Senior PM",
                            interview_date="2026-05-18")
    assert "[Add one specific thing discussed" in body


def test_thank_you_when_phrase_yesterday():
    """Interview yesterday → email should say 'yesterday' in the when_phrase."""
    from datetime import timedelta
    yesterday_str = (datetime.now().date() - timedelta(days=1)).strftime("%Y-%m-%d")
    body = draft_thank_you("Stripe", "Senior PM",
                            interview_date=yesterday_str,
                            conversation_detail="x")
    assert "yesterday" in body.lower()


def test_thank_you_under_150_words_with_placeholders():
    body = draft_thank_you("Stripe", "Senior PM",
                            interview_date="2026-05-18")
    word_count = len(body.split())
    assert word_count < 150, f"thank_you body is {word_count} words; target < 150"


# ---- scan-stale logic ------------------------------------------------------


def _write_tracker(path: Path, entries: list[dict]) -> None:
    path.write_text(json.dumps(entries), encoding="utf-8")


def test_scan_stale_returns_only_applied_over_threshold(tmp_path: Path):
    tracker = tmp_path / "tracker.json"
    _write_tracker(tracker, [
        # 10 days stale → should be flagged
        {"company": "Acme", "title": "PM", "status": "applied", "applied_date": "2026-05-10"},
        # 3 days only → not stale enough
        {"company": "Beta", "title": "PM", "status": "applied", "applied_date": "2026-05-17"},
        # 30 days but status=interviewing → NOT a check-in target
        {"company": "Gamma", "title": "PM", "status": "interviewing", "applied_date": "2026-04-20"},
        # 30 days but status=rejected → not a target
        {"company": "Delta", "title": "PM", "status": "rejected", "applied_date": "2026-04-20"},
    ])
    today = datetime.strptime("2026-05-20", "%Y-%m-%d")
    stale = scan_stale_applications(tracker, stale_days=7, today=today)
    assert len(stale) == 1
    assert stale[0].company == "Acme"
    assert stale[0].days_stale == 10


def test_scan_stale_supports_object_entries_shape(tmp_path: Path):
    """Tracker JSON may be {"entries": [...]} as well as a bare list."""
    tracker = tmp_path / "tracker.json"
    tracker.write_text(json.dumps({"entries": [
        {"company": "Acme", "title": "PM", "status": "applied", "applied_date": "2026-05-10"},
    ]}), encoding="utf-8")
    today = datetime.strptime("2026-05-20", "%Y-%m-%d")
    stale = scan_stale_applications(tracker, stale_days=7, today=today)
    assert len(stale) == 1
    assert stale[0].company == "Acme"


def test_scan_stale_missing_tracker_returns_empty(tmp_path: Path):
    stale = scan_stale_applications(tmp_path / "nonexistent.json", stale_days=7)
    assert stale == []


def test_scan_stale_malformed_json_returns_empty(tmp_path: Path):
    tracker = tmp_path / "tracker.json"
    tracker.write_text("not even close to JSON", encoding="utf-8")
    stale = scan_stale_applications(tracker, stale_days=7)
    assert stale == []


def test_scan_stale_skips_entries_missing_applied_date(tmp_path: Path):
    tracker = tmp_path / "tracker.json"
    _write_tracker(tracker, [
        {"company": "NoDateCo", "title": "PM", "status": "applied"},  # no date
        {"company": "WithDate", "title": "PM", "status": "applied", "applied_date": "2026-05-10"},
    ])
    today = datetime.strptime("2026-05-20", "%Y-%m-%d")
    stale = scan_stale_applications(tracker, stale_days=7, today=today)
    assert len(stale) == 1
    assert stale[0].company == "WithDate"


def test_scan_stale_does_NOT_fall_back_to_posted_field(tmp_path: Path):
    """Regression test (v5.1.1): the canonical tracker.json schema (from
    generate_tracker_html.py) uses 'posted' for when the COMPANY posted the
    role, not when the USER applied. scan-stale must NOT use 'posted' as a
    fallback for 'applied_date' — a posting that was up for 30 days when
    the user just applied today should NOT be flagged as stale.
    """
    tracker = tmp_path / "tracker.json"
    _write_tracker(tracker, [
        # Company posted 30 days ago, but user has no applied_date field
        # (or just applied today). Must NOT be flagged as stale.
        {"company": "OldPosting", "title": "PM", "status": "applied",
         "posted": "2026-04-20"},
    ])
    today = datetime.strptime("2026-05-20", "%Y-%m-%d")
    stale = scan_stale_applications(tracker, stale_days=7, today=today)
    assert stale == [], (
        f"Entries without applied_date must not be flagged as stale based on "
        f"the 'posted' field. Got: {stale}"
    )


def test_scan_stale_custom_threshold(tmp_path: Path):
    tracker = tmp_path / "tracker.json"
    _write_tracker(tracker, [
        {"company": "Acme", "title": "PM", "status": "applied", "applied_date": "2026-05-15"},
    ])
    today = datetime.strptime("2026-05-20", "%Y-%m-%d")
    # 5 days stale, threshold 14 → NOT flagged
    assert scan_stale_applications(tracker, stale_days=14, today=today) == []
    # threshold 3 → IS flagged
    stale = scan_stale_applications(tracker, stale_days=3, today=today)
    assert len(stale) == 1


# ---- CLI tests --------------------------------------------------------------


def test_cli_check_in_emits_email(tmp_path: Path):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "draft",
         "--template", "check_in",
         "--company", "Stripe",
         "--role", "Senior PM",
         "--applied-date", "2026-05-10"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "Stripe" in result.stdout
    assert "Senior PM" in result.stdout


def test_cli_check_in_requires_applied_date():
    """check_in without --applied-date should exit with error."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "draft",
         "--template", "check_in",
         "--company", "Stripe",
         "--role", "Senior PM"],
        capture_output=True, text=True,
    )
    assert result.returncode != 0
    assert "applied-date" in result.stderr.lower()


def test_cli_thank_you_works_without_interview_date(tmp_path: Path):
    """interview-date is optional for thank_you; falls back to 'recently'."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "draft",
         "--template", "thank_you",
         "--company", "Stripe",
         "--role", "Senior PM"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "Stripe" in result.stdout
    assert "recently" in result.stdout


def test_cli_scan_stale_emits_json(tmp_path: Path):
    tracker = tmp_path / "tracker.json"
    _write_tracker(tracker, [
        {"company": "Acme", "title": "PM", "status": "applied", "applied_date": "2026-05-10"},
        {"company": "Beta", "title": "PM", "status": "interviewing", "applied_date": "2026-04-20"},
    ])
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "scan-stale",
         "--tracker", str(tracker),
         "--stale-days", "7",
         "--today", "2026-05-20"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    payload = json.loads(result.stdout)
    assert payload["stale_count"] == 1
    assert payload["stale_applications"][0]["company"] == "Acme"
    assert payload["stale_days_threshold"] == 7


# ---- Load-bearing safety: skill never auto-sends ---------------------------


def test_no_smtp_or_send_imports_in_script():
    """Load-bearing safety: the script must not import any mail/send library.
    The 'user copy-pastes' boundary is what keeps the trust model intact —
    the skill drafts, the user owns sending.
    """
    src = SCRIPT.read_text(encoding="utf-8")
    forbidden = [
        "import smtplib",
        "from smtplib",
        "import imaplib",
        "from imaplib",
        "import email.mime",
        "sendmail",
        "send_message",
    ]
    for needle in forbidden:
        assert needle not in src, (
            f"draft_followup.py contains '{needle}' — this script must NEVER "
            f"send mail. The user copy-pastes; the skill never owns the send step."
        )
