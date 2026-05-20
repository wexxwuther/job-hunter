#!/usr/bin/env python3
"""
draft_followup.py

Draft a short, polite follow-up email for a job application. Two templates:

  check_in       : 7-14 days after applying, no response yet. Reiterate one
                   relevant qualification, ask whether the role is still active,
                   include a concrete CTA.
  thank_you      : 24-48 hours after a phone screen, onsite, or other interview.
                   Reference one specific thing discussed, reiterate one strong
                   qualification, propose concrete next-step.

Outputs an email body to stdout (or --out) the user can copy-paste. The script
NEVER sends the email. The "send" step is the user's, by design (different
trust model; this skill stays out of the mail server).

Also offers a `scan-stale` mode that reads tracker.json and lists applications
at status=applied that are older than --stale-days (default 7). Useful for
"show me what I should follow up on" prompts.

Usage:
    python draft_followup.py draft --template check_in \\
        --company Stripe --role 'Senior PM' --applied-date 2026-05-10
    python draft_followup.py draft --template thank_you \\
        --company Stripe --role 'Senior PM' --interview-date 2026-05-18 \\
        --conversation-detail "your team's move from monolith to event-driven"
    python draft_followup.py scan-stale --tracker tracker.json [--stale-days 7]

Privacy: reads only the inputs you pass on the command line plus tracker.json
if you point to it. Sends nothing.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

# Templates kept short on purpose. Research summary (Yesware, Backlinko 2024):
# follow-ups in the 7-10 day window after no response have a meaningfully higher
# open + reply rate than longer-form re-pitches. Under 150 words is the target.

DEFAULT_STALE_DAYS = 7

CHECK_IN_TEMPLATE = """Subject: Following up — {role} at {company}

Hi{salutation},

I wanted to follow up on my application for the {role} position at {company}, which I submitted on {applied_date_friendly}. I remain very interested in the role and wanted to check in on the timing of the search.

{qualification_line}

If it would be helpful, I'm happy to share additional examples of my work or jump on a brief call. Looking forward to hearing about next steps.

Best regards,
{user_name_placeholder}
"""

THANK_YOU_TEMPLATE = """Subject: Thank you — {role} at {company}

Hi{salutation},

Thank you for taking the time to speak with me {when_phrase} about the {role} role at {company}. I particularly enjoyed our discussion of {conversation_detail}.

{qualification_line}

I'm even more interested in the role after our conversation. Please let me know if there is anything else I can provide as you continue your evaluation.

Best regards,
{user_name_placeholder}
"""

USER_NAME_PLACEHOLDER = "[your name]"
DEFAULT_QUALIFICATION_LINE = (
    "[Add one specific qualification that maps to a stated requirement — "
    "e.g., 'My work scaling the payments platform at $previous_company "
    "from 10k to 1M requests/day directly addresses the scale challenges "
    "in the job description.']"
)


@dataclass
class StaleEntry:
    company: str
    role: str
    applied_date: str
    days_stale: int
    url: str | None


def _friendly_date(date_str: str) -> str:
    """Render an ISO date as 'May 10' for use in the email body. Falls back to
    the input string if it isn't parseable (don't crash on weird input)."""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%B %-d") if sys.platform != "win32" else dt.strftime("%B %#d")
    except ValueError:
        return date_str


def _salutation(contact_name: str | None) -> str:
    if not contact_name or contact_name.strip().lower() in ("", "unknown", "team"):
        return " there"
    name = contact_name.strip()
    return f" {name}"


def _when_phrase(interview_date: str | None) -> str:
    """Render '2026-05-18' as 'on May 18' or 'yesterday' / 'today' if appropriate."""
    if not interview_date:
        return "recently"
    try:
        dt = datetime.strptime(interview_date, "%Y-%m-%d").date()
    except ValueError:
        return f"on {interview_date}"
    today = datetime.now().date()
    delta = (today - dt).days
    if delta == 0:
        return "earlier today"
    if delta == 1:
        return "yesterday"
    if delta < 7:
        return f"{delta} days ago"
    return f"on {_friendly_date(interview_date)}"


def draft_check_in(company: str, role: str, applied_date: str,
                   contact_name: str | None = None,
                   qualification: str | None = None) -> str:
    return CHECK_IN_TEMPLATE.format(
        role=role,
        company=company,
        applied_date_friendly=_friendly_date(applied_date),
        salutation=_salutation(contact_name),
        qualification_line=qualification or DEFAULT_QUALIFICATION_LINE,
        user_name_placeholder=USER_NAME_PLACEHOLDER,
    )


def draft_thank_you(company: str, role: str, interview_date: str | None = None,
                    conversation_detail: str | None = None,
                    contact_name: str | None = None,
                    qualification: str | None = None) -> str:
    detail = conversation_detail or (
        "[Add one specific thing discussed — a problem they raised, a project they mentioned, "
        "an architecture question you went deep on. Generic 'thanks for your time' lines "
        "are why thank-you notes get ignored.]"
    )
    return THANK_YOU_TEMPLATE.format(
        role=role,
        company=company,
        when_phrase=_when_phrase(interview_date),
        conversation_detail=detail,
        salutation=_salutation(contact_name),
        qualification_line=qualification or DEFAULT_QUALIFICATION_LINE,
        user_name_placeholder=USER_NAME_PLACEHOLDER,
    )


def scan_stale_applications(tracker_path: Path, stale_days: int = DEFAULT_STALE_DAYS,
                             today: datetime | None = None) -> list[StaleEntry]:
    """Read tracker.json and return entries at status=applied older than stale_days.
    Other statuses (interviewing/offer/rejected/withdrawn) are NEVER returned —
    this scan is for the specific 'applied with no response' case only."""
    today_date = (today or datetime.now()).date()

    if not tracker_path.is_file():
        return []
    try:
        data = json.loads(tracker_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []

    # tracker.json may be a list of entries OR an object with an "entries" key.
    # Defensively support both shapes.
    if isinstance(data, dict) and "entries" in data:
        entries = data["entries"]
    elif isinstance(data, list):
        entries = data
    else:
        return []

    stale: list[StaleEntry] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        if entry.get("status") != "applied":
            continue
        applied_str = entry.get("applied") or entry.get("posted") or entry.get("applied_date")
        if not applied_str:
            continue
        try:
            applied_dt = datetime.strptime(applied_str, "%Y-%m-%d").date()
        except ValueError:
            continue
        delta = (today_date - applied_dt).days
        if delta >= stale_days:
            stale.append(StaleEntry(
                company=entry.get("company", "unknown company"),
                role=entry.get("title", entry.get("role", "unknown role")),
                applied_date=applied_str,
                days_stale=delta,
                url=entry.get("url"),
            ))
    return stale


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_draft = sub.add_parser("draft", help="draft a follow-up email body")
    p_draft.add_argument("--template", required=True, choices=["check_in", "thank_you"])
    p_draft.add_argument("--company", required=True)
    p_draft.add_argument("--role", required=True)
    p_draft.add_argument("--applied-date",
                         help="ISO date the user applied (required for check_in)")
    p_draft.add_argument("--interview-date",
                         help="ISO date of the interview (optional for thank_you)")
    p_draft.add_argument("--conversation-detail",
                         help="one specific thing discussed (optional for thank_you)")
    p_draft.add_argument("--contact-name",
                         help="recruiter or hiring manager name, if known")
    p_draft.add_argument("--qualification",
                         help="one strong qualification to reiterate (optional)")
    p_draft.add_argument("--out", type=Path, help="write email to file instead of stdout")

    p_scan = sub.add_parser("scan-stale",
                            help="list applications stale at status=applied")
    p_scan.add_argument("--tracker", required=True, type=Path,
                        help="path to tracker.json")
    p_scan.add_argument("--stale-days", type=int, default=DEFAULT_STALE_DAYS,
                        help=f"days at status=applied to consider stale (default {DEFAULT_STALE_DAYS})")
    p_scan.add_argument("--today", help="override today's date as YYYY-MM-DD (for testing)")

    args = parser.parse_args(argv)

    if args.cmd == "draft":
        if args.template == "check_in":
            if not args.applied_date:
                print("error: --applied-date is required for check_in", file=sys.stderr)
                return 2
            body = draft_check_in(
                company=args.company,
                role=args.role,
                applied_date=args.applied_date,
                contact_name=args.contact_name,
                qualification=args.qualification,
            )
        else:  # thank_you
            body = draft_thank_you(
                company=args.company,
                role=args.role,
                interview_date=args.interview_date,
                conversation_detail=args.conversation_detail,
                contact_name=args.contact_name,
                qualification=args.qualification,
            )

        if args.out:
            args.out.write_text(body, encoding="utf-8")
            print(f"wrote email to {args.out}", file=sys.stderr)
        else:
            print(body)
        return 0

    if args.cmd == "scan-stale":
        today = None
        if args.today:
            today = datetime.strptime(args.today, "%Y-%m-%d")
        stale = scan_stale_applications(args.tracker, args.stale_days, today)
        print(json.dumps({
            "tracker": str(args.tracker),
            "stale_days_threshold": args.stale_days,
            "stale_count": len(stale),
            "stale_applications": [
                {
                    "company": s.company,
                    "role": s.role,
                    "applied_date": s.applied_date,
                    "days_stale": s.days_stale,
                    "url": s.url,
                }
                for s in stale
            ],
        }, indent=2))
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
