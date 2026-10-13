#!/usr/bin/env python3
"""
parse_resume.py

Extract plain text from a resume in DOCX, PDF, MD, TXT, or HTML format. Lets the job-hunter
skill read resumes without depending on sibling docx/pdf skills (standalone contract).

For DOCX: uses python-docx (PEP 723 inline metadata declares the dependency).
For PDF: uses pypdf (also PEP 723).
For MD/TXT/HTML: reads as UTF-8 text. HTML is stripped of tags via stdlib html.parser.

Usage:
    python parse_resume.py resume.docx
    python parse_resume.py resume.pdf --out resume.txt
    python parse_resume.py resume.md --json

Run with `uv run` to get the inline-declared deps without polluting global Python:
    uv run scripts/parse_resume.py resume.docx
"""
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "python-docx>=1.1.0",
#   "pypdf>=4.0.0",
# ]
# ///

from __future__ import annotations

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path


class _HTMLStripper(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._chunks: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style"}:
            self._skip += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self._skip > 0:
            self._skip -= 1

    def handle_data(self, data: str) -> None:
        if self._skip == 0:
            self._chunks.append(data)

    def text(self) -> str:
        return "".join(self._chunks)


def _strip_html(html: str) -> str:
    stripper = _HTMLStripper()
    stripper.feed(html)
    text = stripper.text()
    return re.sub(r"\n{3,}", "\n\n", text).strip()


_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
_MC_FALLBACK = "{http://schemas.openxmlformats.org/markup-compatibility/2006}Fallback"


def _paragraph_text(p) -> tuple[str, list]:
    """Visible text of one w:p plus any text boxes anchored in it.

    Text-box content (w:txbxContent) is returned separately so it becomes its own
    lines; mc:Fallback is skipped because Word may store the same box twice
    (DrawingML Choice + VML Fallback).
    """
    chunks: list[str] = []
    boxes: list = []

    def walk(el) -> None:
        for ch in el:
            tag = ch.tag
            if not isinstance(tag, str) or tag == _MC_FALLBACK:
                continue
            if tag == _W + "txbxContent":
                boxes.append(ch)
                continue
            if tag == _W + "t":
                chunks.append(ch.text or "")
            elif tag in (_W + "tab", _W + "br", _W + "cr"):
                chunks.append(" ")
            walk(ch)

    walk(p)
    return "".join(chunks).strip(), boxes


def _block_lines(container) -> list[str]:
    """Lines from a body / cell / header / text box, in document order."""
    lines: list[str] = []
    for el in container:
        tag = el.tag
        if tag == _W + "p":
            text, boxes = _paragraph_text(el)
            if text:
                lines.append(text)
            for box in boxes:
                lines.extend(_block_lines(box))
        elif tag == _W + "tbl":
            for tr in el.findall(_W + "tr"):
                # One w:tc per visible cell: a horizontally merged cell is a single
                # w:tc with gridSpan, so it is read once (python-docx's row.cells
                # repeats it per grid column).
                cells = [c for c in (_block_lines(tc) for tc in tr.findall(_W + "tc")) if c]
                if not cells:
                    continue
                if all(len(c) == 1 for c in cells):
                    lines.append(" | ".join(c[0] for c in cells))   # data row
                else:
                    for c in cells:                                 # layout table
                        lines.extend(c)
        elif tag in (_W + "sdt", _W + "customXml"):
            content = el.find(_W + "sdtContent") if tag == _W + "sdt" else el
            if content is not None:
                lines.extend(_block_lines(content))
    return lines


def _header_footer_lines(doc, kinds: tuple[str, ...]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for section in doc.sections:
        for kind in kinds:
            part = getattr(section, kind)
            if part.is_linked_to_previous:   # no definition of its own; don't create one
                continue
            for line in _block_lines(part._element):
                if line not in seen:
                    seen.add(line)
                    out.append(line)
    return out


def _parse_docx(path: Path) -> str:
    """Header (contact details often live here), body in document order including
    tables and text boxes, then footer."""
    try:
        from docx import Document
    except ImportError as e:
        raise RuntimeError(
            "python-docx is not installed. Run with `uv run scripts/parse_resume.py ...` "
            "or `pip install python-docx`."
        ) from e
    doc = Document(str(path))
    parts = _header_footer_lines(doc, ("first_page_header", "header", "even_page_header"))
    parts += _block_lines(doc.element.body)
    parts += _header_footer_lines(doc, ("first_page_footer", "footer", "even_page_footer"))
    return "\n".join(parts)


def _parse_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as e:
        raise RuntimeError(
            "pypdf is not installed. Run with `uv run scripts/parse_resume.py ...` "
            "or `pip install pypdf`."
        ) from e
    reader = PdfReader(str(path))
    pages: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        text = text.strip()
        if text:
            pages.append(text)
    return "\n\n".join(pages)


def _parse_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace").strip()


def _parse_html(path: Path) -> str:
    return _strip_html(path.read_text(encoding="utf-8", errors="replace"))


PARSERS = {
    ".docx": _parse_docx,
    ".pdf": _parse_pdf,
    ".md": _parse_text,
    ".markdown": _parse_text,
    ".txt": _parse_text,
    ".text": _parse_text,
    ".rst": _parse_text,
    ".html": _parse_html,
    ".htm": _parse_html,
}


def parse(path: str | Path) -> str:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"resume not found: {p}")
    if not p.is_file():
        raise IsADirectoryError(f"not a file: {p}")
    ext = p.suffix.lower()
    parser = PARSERS.get(ext)
    if not parser:
        raise ValueError(
            f"unsupported resume format: {ext!r}. Supported: {sorted(PARSERS.keys())}"
        )
    text = parser(p)
    if not text.strip():
        hint = (" It is probably a scanned image with no text layer."
                if ext == ".pdf" else "")
        raise ValueError(
            f"no text could be extracted from {p.name}.{hint} Ask the user for a DOCX, "
            "TXT, or pasted copy of the resume; do not guess its contents."
        )
    return text


def _basic_sections(text: str) -> dict[str, str]:
    section_patterns = [
        ("summary", r"(?:summary|profile|objective)"),
        ("experience", r"(?:experience|employment|work\s+history|professional\s+experience)"),
        ("education", r"education"),
        ("skills", r"(?:skills|technical\s+skills|core\s+competencies)"),
        ("certifications", r"(?:certifications?|licenses?)"),
        ("projects", r"projects?"),
    ]
    out: dict[str, str] = {}
    text_lines = text.splitlines()
    indices: list[tuple[str, int]] = []
    for i, line in enumerate(text_lines):
        stripped = line.strip()
        if not stripped or len(stripped) > 60:
            continue
        for key, pattern in section_patterns:
            if re.match(rf"^\s*{pattern}\s*$", stripped, re.IGNORECASE):
                indices.append((key, i))
                break
    indices.sort(key=lambda x: x[1])
    for j, (key, start) in enumerate(indices):
        end = indices[j + 1][1] if j + 1 < len(indices) else len(text_lines)
        body = "\n".join(text_lines[start + 1:end]).strip()
        if body:
            out[key] = body
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("resume", help="path to resume file")
    parser.add_argument("--out", default=None, help="write extracted text here (default stdout)")
    parser.add_argument("--json", action="store_true",
                        help="emit JSON with raw text plus best-effort section breakdown")
    args = parser.parse_args(argv)

    try:
        text = parse(args.resume)
    except (FileNotFoundError, IsADirectoryError, ValueError, RuntimeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    if args.json:
        payload = {
            "source": str(Path(args.resume).resolve()),
            "format": Path(args.resume).suffix.lower(),
            "text": text,
            "sections": _basic_sections(text),
            "char_count": len(text),
            "line_count": text.count("\n") + 1,
        }
        out = json.dumps(payload, indent=2)
    else:
        out = text

    if args.out:
        Path(args.out).write_text(out + "\n", encoding="utf-8")
        print(f"wrote {len(out)} chars to {args.out}", file=sys.stderr)
    else:
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
