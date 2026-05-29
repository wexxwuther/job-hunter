#!/usr/bin/env python3
"""draft_cover_letter.py — assemble a STRUCTURED cover-letter draft from the
user's real source facts, never inventing values.

Design rule (the whole point of this script): it fills factual slots ONLY from
the source material it is given. Anything it cannot ground in the source becomes
a visible `[CONFIRM: ...]` placeholder for the user to fill — it is NEVER
fabricated. The agent then runs the assembled draft through
verify_no_fabrication.py before finalizing.

This script is deterministic and pure: same inputs -> same output. It does NOT
call an LLM, fetch the web, or send mail. It produces a skeleton the agent fills
with the user's confirmed facts; the agent supplies the persuasive prose, this
script enforces the structure and the grounding discipline.

Usage:
    python draft_cover_letter.py \
        --company "Stripe" --role "Senior Product Manager" \
        --applicant "Jordan Lee" \
        --highlights highlights.txt \
        [--out CoverLetter_Stripe_SeniorPM.md]

`highlights.txt` is one grounded qualification per line, each ideally tied to a
posting requirement with ` :: ` (e.g.
    Led the payments rewrite that cut checkout latency 30% :: scale payment systems
). A line with no ` :: ` is used as a standalone qualification. Lines are taken
verbatim from the user's confirmed facts — the script does not embellish them.

Exit codes: 0 ok; 2 usage/IO error.
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path


GREETING_PLACEHOLDER = "[CONFIRM: hiring manager name, or use 'Hiring Team']"


def _read_lines(path: str) -> list[str]:
    text = Path(path).read_text(encoding="utf-8")
    return [ln.strip() for ln in text.splitlines() if ln.strip()]


def build_letter(company: str, role: str, applicant: str,
                 highlights: list[str]) -> str:
    """Assemble the markdown letter skeleton from grounded inputs only.

    Every interpolated value comes from an argument (i.e. from the user's
    confirmed facts). Slots with no grounded value are emitted as [CONFIRM: ...].
    """
    company = company.strip() or "[CONFIRM: company name]"
    role = role.strip() or "[CONFIRM: role title]"
    applicant = applicant.strip() or "[CONFIRM: your name]"

    # Body paragraphs: one per highlight, each tying a real qualification to a
    # posting requirement when the user supplied the mapping via ' :: '.
    body_paras: list[str] = []
    if not highlights:
        body_paras.append(
            "[CONFIRM: add 2-3 of your real qualifications, each tied to a "
            "requirement in the posting. Do not invent accomplishments or "
            "numbers — use only what is on your resume or that you can state.]"
        )
    for h in highlights:
        if " :: " in h:
            qual, req = (part.strip() for part in h.split(" :: ", 1))
            body_paras.append(
                f"{qual}. That maps directly to your need to {req} — "
                "[CONFIRM: one sentence connecting this to the role, no new facts]."
            )
        else:
            body_paras.append(
                f"{h}. [CONFIRM: one sentence connecting this to the role, no new facts]."
            )

    body = "\n\n".join(body_paras)

    letter = f"""# Cover Letter — {company} — {role}

{GREETING_PLACEHOLDER},

I'm writing to apply for the {role} position at {company}. [CONFIRM: one-sentence
hook stating why this role/company, grounded in something real — a product you use,
the mission, a problem you've solved before. No invented relationship.]

{body}

I'd welcome the chance to discuss how my background fits what {company} is building.
Thank you for your time and consideration.

Sincerely,
{applicant}
"""
    return letter


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--company", required=True)
    p.add_argument("--role", required=True)
    p.add_argument("--applicant", required=True)
    p.add_argument("--highlights", help="path to a file with one grounded qualification per line")
    p.add_argument("--out", help="output .md path; prints to stdout if omitted")
    args = p.parse_args(argv)

    highlights: list[str] = []
    if args.highlights:
        try:
            highlights = _read_lines(args.highlights)
        except OSError as exc:
            print(f"error: cannot read --highlights: {exc}", file=sys.stderr)
            return 2

    letter = build_letter(args.company, args.role, args.applicant, highlights)

    if args.out:
        try:
            Path(args.out).write_text(letter, encoding="utf-8")
        except OSError as exc:
            print(f"error: cannot write --out: {exc}", file=sys.stderr)
            return 2
        print(f"wrote {args.out}")
    else:
        sys.stdout.write(letter)
    return 0


if __name__ == "__main__":
    sys.exit(main())
