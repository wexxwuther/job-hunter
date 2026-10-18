#!/usr/bin/env python3
"""
load_application.py

Gather everything interview-prep needs about ONE tracked application into a
single JSON context: the tracker entry, the text of the resume and cover letter
the user actually submitted for it, the posting text, the URLs found inside the
posting (which the agent must NOT open), and the user's confirmed lessons.

Reads only. It never writes tracker.json (application-tracker owns that file),
never fetches anything from the network, and never invents a missing value: a
missing document or posting is reported as missing so the agent can ask.

Inputs:
  --tracker   tracker.json written by application-tracker. Either a JSON list of
              entries or {"entries": [...]} (the same shapes draft_followup.py
              accepts).
  --company   company to prep for (case and punctuation insensitive).
  --role      optional role/title filter when the company has several entries.
  --index     pick an entry by its position in the tracker (0-based) instead.
  --posting   optional file with the full posting text (best source).
  --postings  optional postings.json from job-search; its `summary` for the
              same URL is used only if --posting is not given.
  --workspace optional workspace folder; defaults to the tracker's folder.
              `.job-hunter/LESSONS.md` and relative document paths resolve here.

Exit codes:
  0  context written (warnings may still be present: read them)
  2  could not pick one application (no tracker, bad JSON, no match, or
     several matches). The JSON on stdout carries "error" and, for several
     matches, "candidates" so the agent can ask the user which one.

Usage:
  python load_application.py --tracker tracker.json --company "Acme" [--role "Analyst"]
  python load_application.py --tracker tracker.json --index 3 --posting posting.txt --out context.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree

LESSONS_MARKER = "<!-- Confirmed lessons appended below this line -->"
READABLE_SUFFIXES = (".md", ".txt", ".docx", ".pdf")
URL_RE = re.compile(r"https?://[^\s<>\"')\]]+", re.IGNORECASE)
COMPANY_SUFFIXES = {"inc", "llc", "ltd", "corp", "corporation", "co", "company", "plc", "gmbh"}

# Status -> what the agent should know before prepping. Interview prep fits
# `interviewing`; anything else is still allowed (the tracker may be behind),
# but the agent must confirm with the user and may offer a tracker update.
STATUS_NOTES = {
    "interviewing": None,
    "applied": "Tracker says 'applied', not 'interviewing'. Confirm the interview is "
               "scheduled; offer to update the tracker through application-tracker.",
    "to apply": "Tracker says 'to apply': the user may not have applied yet. Confirm before "
                "prepping; the submitted documents may not exist.",
    "offer": "Tracker says 'offer'. Interview prep is for interviews; confirm there is "
             "another interview round before prepping.",
    "rejected": "Tracker says 'rejected'. Confirm the user really has an interview for "
                "this application before prepping.",
    "withdrawn": "Tracker says 'withdrawn'. Confirm the user really has an interview for "
                 "this application before prepping.",
    "no_response_after_21d": "Tracker marks this as closed after 21 days of silence. Confirm "
                             "the employer came back with an interview.",
}

W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


class SelectionError(Exception):
    """Raised when exactly one application cannot be chosen."""

    def __init__(self, message: str, candidates: list | None = None):
        super().__init__(message)
        self.candidates = candidates or []


def normalize_company(name: str) -> str:
    words = re.findall(r"[a-z0-9]+", (name or "").lower())
    while words and words[-1] in COMPANY_SUFFIXES:
        words.pop()
    return " ".join(words)


def normalize_text(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", (text or "").lower()))


def load_entries(tracker_path: Path) -> list:
    if not tracker_path.is_file():
        raise SelectionError(f"tracker not found: {tracker_path}. Ask the user where their "
                             "tracker.json is, or track the application first.")
    try:
        data = json.loads(tracker_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise SelectionError(f"tracker is not valid JSON: {exc}") from exc
    if isinstance(data, dict) and isinstance(data.get("entries"), list):
        data = data["entries"]
    if not isinstance(data, list):
        raise SelectionError("tracker must be a JSON list of entries or {\"entries\": [...]}")
    return data


def _summary(index: int, entry: dict) -> dict:
    return {"index": index, "company": entry.get("company", ""),
            "title": entry.get("title", ""), "status": entry.get("status", "")}


def select_entry(entries: list, company: str | None, role: str | None,
                 index: int | None) -> tuple[int, dict]:
    if index is not None:
        if not 0 <= index < len(entries) or not isinstance(entries[index], dict):
            raise SelectionError(f"no tracker entry at index {index} "
                                 f"(tracker has {len(entries)} entries)")
        return index, entries[index]
    if not company or not normalize_company(company):
        raise SelectionError("give --company (or --index) to choose the application")
    want = normalize_company(company)
    rows = [(i, e) for i, e in enumerate(entries) if isinstance(e, dict)]
    exact = [(i, e) for i, e in rows if normalize_company(e.get("company", "")) == want]
    matches = exact or [(i, e) for i, e in rows
                        if want in normalize_company(e.get("company", ""))]
    if role and normalize_text(role):
        want_role = normalize_text(role)
        matches = [(i, e) for i, e in matches if want_role in normalize_text(e.get("title", ""))]
    if not matches:
        raise SelectionError(f"no tracked application matches company={company!r}"
                             + (f" role={role!r}" if role else "")
                             + ". Ask the user which application, or track it first.",
                             [_summary(i, e) for i, e in rows])
    if len(matches) > 1:
        raise SelectionError("several tracked applications match; ask the user which one "
                             "(then pass --index)", [_summary(i, e) for i, e in matches])
    return matches[0]


def _docx_text(path: Path) -> str:
    """Paragraph text from word/document.xml, in document order (stdlib only)."""
    with zipfile.ZipFile(path) as z:
        root = ElementTree.fromstring(z.read("word/document.xml"))
    lines = []
    for para in root.iter(f"{W_NS}p"):
        text = "".join(node.text or "" for node in para.iter(f"{W_NS}t")).strip()
        if text:
            lines.append(text)
    return "\n".join(lines)


def _pdf_text(path: Path) -> str:
    try:
        from pypdf import PdfReader  # optional dependency
    except ImportError as exc:
        raise ValueError("reading PDF needs the pypdf package; ask the user for a .docx, "
                         ".md or pasted text instead") from exc
    return "\n".join((page.extract_text() or "") for page in PdfReader(str(path)).pages)


def read_document(field: str, value, base: Path) -> dict:
    """Read one submitted document named on the tracker entry. Never raises."""
    doc = {"field": field, "path": None, "found": False, "text": "", "warning": None}
    if not value:
        doc["warning"] = f"tracker entry has no {field}; ask the user for the version they sent"
        return doc
    path = Path(str(value))
    if not path.is_absolute():
        path = base / path
    doc["path"] = str(path)
    if path.suffix.lower() not in READABLE_SUFFIXES:
        doc["warning"] = (f"{field} has unsupported type {path.suffix or '(none)'}; "
                          f"readable: {', '.join(READABLE_SUFFIXES)}")
        return doc
    if not path.is_file():
        doc["warning"] = f"{field} not found at {path}; ask the user for the version they sent"
        return doc
    try:
        if path.suffix.lower() == ".docx":
            text = _docx_text(path)
        elif path.suffix.lower() == ".pdf":
            text = _pdf_text(path)
        else:
            text = path.read_text(encoding="utf-8")
    except (OSError, ValueError, KeyError, zipfile.BadZipFile, ElementTree.ParseError,
            UnicodeDecodeError) as exc:
        doc["warning"] = f"could not read {field} at {path}: {exc}"
        return doc
    if not text.strip():
        doc["warning"] = (f"{field} at {path} has no extractable text (scanned?); ask the "
                          "user to paste it")
        return doc
    doc["found"] = True
    doc["text"] = text
    return doc


def read_lessons(workspace: Path) -> tuple[list, str | None]:
    """Confirmed lessons only: entries after the template's append marker."""
    path = workspace / ".job-hunter" / "LESSONS.md"
    if not path.is_file():
        return [], "no .job-hunter/LESSONS.md; continuing without lessons"
    text = path.read_text(encoding="utf-8")
    idx = text.find(LESSONS_MARKER)
    if idx == -1:
        return [], ("LESSONS.md has no append marker; not reading it (the template "
                    "scaffolding would be mistaken for lessons)")
    lessons = []
    for chunk in re.split(r"(?m)^## ", text[idx + len(LESSONS_MARKER):])[1:]:
        heading, _, body = chunk.partition("\n")
        lessons.append({"heading": heading.strip(), "body": body.strip()})
    return lessons, None


def find_posting(entry: dict, posting_file: Path | None, postings_file: Path | None) -> dict:
    if posting_file is not None:
        if posting_file.is_file():
            text = posting_file.read_text(encoding="utf-8")
            if text.strip():
                return {"source": "posting file", "text": text}
        return {"source": "none", "text": "",
                "warning": f"posting file missing or empty: {posting_file}"}
    if postings_file is not None and postings_file.is_file():
        try:
            postings = json.loads(postings_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            postings = []
        url = entry.get("url")
        for posting in postings if isinstance(postings, list) else []:
            if isinstance(posting, dict) and url and posting.get("url") == url \
                    and str(posting.get("summary") or "").strip():
                return {"source": "postings.json summary (partial)",
                        "text": str(posting["summary"]),
                        "warning": "only the search summary is available; ask the user to "
                                   "paste the full posting for better questions"}
    return {"source": "none", "text": "",
            "warning": "no posting text; ask the user to paste the posting. Do not open the "
                       "tracker URL to fetch it without telling the user."}


def build_context(tracker: Path, company: str | None = None, role: str | None = None,
                  index: int | None = None, posting: Path | None = None,
                  postings: Path | None = None, workspace: Path | None = None) -> dict:
    entries = load_entries(tracker)
    idx, entry = select_entry(entries, company, role, index)
    base = workspace or tracker.resolve().parent
    status = str(entry.get("status", "")).strip().lower()
    warnings = []
    note = STATUS_NOTES.get(status, f"unknown tracker status {status!r}; confirm the "
                                    "interview with the user")
    if note:
        warnings.append(note)
    resume = read_document("resume_file", entry.get("resume_file"), base)
    letter = read_document("cover_letter_file", entry.get("cover_letter_file"), base)
    posting_info = find_posting(entry, posting, postings)
    lessons, lesson_warning = read_lessons(base)
    for item in (resume.get("warning"), letter.get("warning"), posting_info.get("warning"),
                 lesson_warning):
        if item:
            warnings.append(item)
    return {
        "tracker_index": idx,
        "application": entry,
        "status": status,
        "status_is_interviewing": status == "interviewing",
        "documents": {"resume": resume, "cover_letter": letter},
        "posting": posting_info,
        "posting_urls_do_not_open": sorted({u.rstrip(".,;:!?") for u in
                                            URL_RE.findall(posting_info["text"])}),
        "lessons": lessons,
        "warnings": warnings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--tracker", type=Path, required=True)
    parser.add_argument("--company")
    parser.add_argument("--role")
    parser.add_argument("--index", type=int)
    parser.add_argument("--posting", type=Path)
    parser.add_argument("--postings", type=Path)
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    try:
        context = build_context(args.tracker, args.company, args.role, args.index,
                                args.posting, args.postings, args.workspace)
    except SelectionError as exc:
        print(json.dumps({"error": str(exc), "candidates": exc.candidates}, indent=2))
        return 2
    except (OSError, UnicodeDecodeError) as exc:
        print(json.dumps({"error": f"could not read input: {exc}", "candidates": []}, indent=2))
        return 2
    if args.out:
        args.out.write_text(json.dumps(context, indent=2, ensure_ascii=False) + "\n",
                            encoding="utf-8")
        print(f"wrote {args.out}", file=sys.stderr)
    else:
        # ASCII escapes so a non-UTF-8 console (Windows cp1252) cannot crash the print.
        print(json.dumps(context, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
