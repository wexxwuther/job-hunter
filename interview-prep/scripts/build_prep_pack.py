#!/usr/bin/env python3
"""
build_prep_pack.py

Build a stage-specific interview prep pack from the context that
load_application.py produced. Deterministic: it never writes a fact about the
user that is not already in their submitted resume, cover letter, or a facts
file the user confirmed. Anything it cannot ground becomes a [CONFIRM: ...]
slot for the agent to fill WITH the user.

One rule makes the pack checkable: every line that speaks as the user (an
answer, a STAR story, a gap bridge) is a blockquote line starting with "> ".
Questions, tips, research notes, and lessons are never blockquoted. The
`claims` subcommand pulls exactly those lines out so the family
anti-fabrication gate (verify_no_fabrication.py) checks what the user will
say, and nothing else.

Subcommands:

  stages     list the interview stages and their focus.
  build      write the prep pack (markdown) and the gate's source file. Refuses
             to overwrite an existing pack unless --force.
  source     rewrite only the gate's source file, e.g. after the user states a
             new fact (never touches the pack).
  questions  ordered question list for mock-interview mode (JSON).
  claims     extract the answer lines from a (filled) pack for the gate, and
             count unresolved [CONFIRM: ...] slots. Exit 3 while any remain.

Research notes (optional --research JSON list) must carry a source URL the
agent found itself. A note whose URL came from inside the posting is rejected;
a note without a URL is listed as unverified; interviewer notes that touch
personal life are rejected. Research never becomes a claim about the user.

Usage:
  python build_prep_pack.py stages
  python build_prep_pack.py build --context context.json --stage hiring_manager \\
      [--facts facts.txt] [--research research.json] --out InterviewPrep.md --source-out source.txt
  python build_prep_pack.py source --context context.json --facts facts.txt --out source.txt
  python build_prep_pack.py questions --context context.json --stage skills [--count 8]
  python build_prep_pack.py claims --pack InterviewPrep.md --out claims.txt
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

CONFIRM_RE = re.compile(r"\[CONFIRM:[^\]]*\]")
LABEL_RE = re.compile(r"^\*\*[^*]{1,40}:\*\*\s*")
URL_RE = re.compile(r"https?://[^\s<>\"')\]]+", re.IGNORECASE)
# bullets: - * and the Unicode bullet, small square and black circle (escaped: ASCII source)
BULLET_RE = re.compile(r"^\s*(?:[-*\u2022\u25aa\u25cf]|\d{1,2}[.)])\s+(.*)$")
MAX_REQUIREMENTS = 8
STOPWORDS = set("""
a about above across after again all also an and any are as at be been being both but by
can could did do does doing for from had has have having he her here his how i if in into
is it its job just may me more most must my no nor not of on once only or other our out
over own per role same she should so some such than that the their them then there these
they this those through to too under until up us very was we were what when where which
while who whom why will with would you your able ability strong excellent good great new
work working year years team teams including experience experienced required requirements
preferred plus etc skills skill knowledge using use used within well across demonstrated
proven""".split())

# "5+ years", "3 yrs", "two years of": a tenure requirement. Keyword overlap cannot
# tell whether dates add up, so these are never matched to a line; the user does
# the arithmetic on the dates they actually sent.
TENURE_RE = re.compile(r"\b(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s*\+?\s*(?:years?|yrs?)\b", re.IGNORECASE)

REQUIREMENT_HINT = re.compile(
    r"\b(experience|ability|able to|knowledge|required|must|proficien|familiar|skill|"
    r"certif|licen|degree|background in|comfortable)\w*", re.IGNORECASE)

PERSONAL_TERMS = re.compile(
    r"\b(home address|address is|lives? (?:in|at|on)|spouse|wife|husband|partner's|"
    r"children|kids|religio\w*|church|political|politics|votes?|health|medical|"
    r"diagnos\w*|dating|divorce\w*|birthday|date of birth|net worth|salary history)\b",
    re.IGNORECASE)

# Each stage: who usually runs it, what it tests, a question bank, and good
# questions for the user to ask. Questions carry keywords used only to suggest
# which of the user's real examples might fit; the user confirms the fit.
STAGES = {
    "recruiter_screen": {
        "label": "Recruiter / phone screen",
        "focus": "Motivation, basic fit, logistics (pay range, location, start date). "
                 "Short, clear answers; no deep stories yet.",
        "questions": [
            ("Tell me about yourself.", "opener", []),
            ("Why are you interested in this role?", "motivation", []),
            ("Why are you looking to leave (or why did you leave) your current role?",
             "motivation", []),
            ("What are your pay expectations?", "logistics", []),
            ("When could you start, and is the location or schedule workable for you?",
             "logistics", []),
            ("Walk me through your most relevant experience for this job.", "experience", []),
        ],
        "ask": [
            "What does the rest of the interview process look like, and who will I meet?",
            "What is the budgeted pay range for this role?",
            "Why is this position open?",
        ],
    },
    "hiring_manager": {
        "label": "Hiring manager interview",
        "focus": "Can you do this job, how do you work, would they want to manage you. "
                 "Expect requirement-by-requirement questions and 2-3 full STAR stories.",
        "questions": [
            ("Tell me about yourself.", "opener", []),
            ("What do you know about what this team does, and why does it appeal to you?",
             "motivation", []),
            ("Tell me about a time you had to learn something new quickly.", "behavioral",
             ["learned", "taught myself", "certified", "course", "ramp", "picked up"]),
            ("Tell me about a time something went wrong and what you did.", "behavioral",
             ["fixed", "resolved", "issue", "problem", "error", "incident", "recovered"]),
            ("How do you prioritize when everything is urgent?", "situational",
             ["prioritized", "deadline", "schedule", "managed", "workload", "planned"]),
            ("What kind of management style works best for you?", "fit", []),
        ],
        "ask": [
            "What would success look like in the first 90 days?",
            "What is the hardest part of this job that the posting does not mention?",
            "How do you give feedback to your team?",
        ],
    },
    "skills": {
        "label": "Skills / technical / practical assessment",
        "focus": "Showing you can do the work: a coding or tools exercise, a clinical or "
                 "safety scenario, a trade test, a teaching demo, a writing sample. Talk "
                 "through your reasoning; say what you would check or ask.",
        "questions": [
            ("Walk me through how you would approach this task, step by step.", "skills",
             ["process", "steps", "approach", "method", "procedure", "built", "designed"]),
            ("What would you check first if this went wrong?", "skills",
             ["troubleshot", "diagnosed", "inspected", "tested", "debugged", "checked"]),
            ("Tell me about the most complex piece of work you have done in this area.",
             "behavioral", ["complex", "built", "designed", "led", "delivered", "installed"]),
            ("How do you make sure your work is safe, correct, or up to standard?", "skills",
             ["quality", "safety", "standard", "compliance", "review", "accuracy", "audit"]),
            ("Which tools, equipment, or methods are you strongest with?", "skills", []),
        ],
        "ask": [
            "What tools, equipment, or systems does the team use day to day?",
            "How is quality or safety checked on this team?",
            "What does a typical week of this work look like?",
        ],
    },
    "behavioral_panel": {
        "label": "Behavioral / panel interview",
        "focus": "Several interviewers, mostly 'tell me about a time' questions scored "
                 "against a rubric. Every answer: Situation, Task, Action, Result, in about "
                 "two minutes, with what YOU did.",
        "questions": [
            ("Tell me about a time you disagreed with a coworker or manager.", "behavioral",
             ["disagreed", "conflict", "resolved", "negotiated", "aligned", "stakeholder"]),
            ("Tell me about a time you helped a difficult customer, patient, client, or "
             "student.", "behavioral",
             ["customer", "client", "patient", "student", "complaint", "service", "support"]),
            ("Tell me about a time you led something without being the boss.", "behavioral",
             ["led", "organized", "coordinated", "mentored", "trained", "initiated"]),
            ("Tell me about a mistake you made and what you learned.", "behavioral",
             ["mistake", "learned", "improved", "changed", "corrected"]),
            ("Tell me about your proudest accomplishment at work.", "behavioral",
             ["achieved", "award", "improved", "increased", "reduced", "launched", "delivered"]),
            ("Tell me about a time you worked under pressure.", "behavioral",
             ["deadline", "pressure", "urgent", "emergency", "shift", "peak", "rush"]),
        ],
        "ask": [
            "What do the best people in this role do differently?",
            "How does the team support each other when things get busy?",
            "What are you hoping the new person will bring to the team?",
        ],
    },
    "case_presentation": {
        "label": "Case study / presentation",
        "focus": "You get a problem or prepare a presentation. They watch how you structure "
                 "it, state assumptions, use evidence, and handle questions.",
        "questions": [
            ("Walk us through your approach and the assumptions you made.", "skills",
             ["analyzed", "planned", "strategy", "assessed", "researched"]),
            ("What data or information would you want that you did not have?", "skills",
             ["data", "report", "analysis", "metrics", "research"]),
            ("What would you do first in your first month on this problem?", "situational",
             []),
            ("Tell me about a time you presented a recommendation and someone pushed back.",
             "behavioral", ["presented", "recommended", "proposal", "persuaded", "pitched"]),
        ],
        "ask": [
            "How close is this case to a problem the team is facing now?",
            "Who would I work with to put a recommendation like this into practice?",
        ],
    },
    "final": {
        "label": "Final round / executive / culture",
        "focus": "Senior leaders checking judgment, motivation, and whether you will stay. "
                 "Fewer details, more why; connect your story to where the organization is "
                 "going.",
        "questions": [
            ("Why this organization, and why now?", "motivation", []),
            ("Where do you want to be in a few years?", "motivation", []),
            ("Tell me about the hardest decision you have made at work.", "behavioral",
             ["decided", "decision", "chose", "tradeoff", "recommended"]),
            ("What would your last manager say you should work on?", "fit", []),
            ("Is there anything that would stop you from accepting an offer?", "logistics", []),
        ],
        "ask": [
            "What are the biggest priorities for the organization this year?",
            "What would make you say, a year from now, that hiring me was the right call?",
            "Is there anything about my background that gives you pause?",
        ],
    },
}

CHECKLIST = [
    "Re-read the resume and cover letter you actually sent (in this pack's sources).",
    "Confirm date, time, time zone, format (phone / video / in person), and who you meet.",
    "Test the video link or plan the route and parking; arrive or log in 10 minutes early.",
    "Have 2-3 STAR stories ready to tell in about two minutes each, out loud.",
    "Write down your questions to ask; pick at least two.",
    "Within 24-48 hours after: a thank-you note (application-tracker drafts it).",
]


def tokens(text: str) -> set:
    out = set()
    for word in re.findall(r"[a-z0-9+#]+", text.lower()):
        if len(word) < 3 or word in STOPWORDS:
            continue
        out.add(word[:5] if len(word) >= 5 else word)
    return out


def extract_requirements(posting: str) -> list:
    """Requirement-like lines from the posting: bullet lines first, else hint sentences."""
    reqs = []
    for line in posting.splitlines():
        m = BULLET_RE.match(line)
        if m:
            item = m.group(1).strip().rstrip(".;")
            if 3 <= len(item.split()) <= 30:
                reqs.append(item)
    if not reqs:
        for sentence in re.split(r"(?<=[.;!?])\s+|\n+", posting):
            sentence = sentence.strip().rstrip(".;")
            if REQUIREMENT_HINT.search(sentence) and 4 <= len(sentence.split()) <= 35:
                reqs.append(sentence)
    seen, unique = set(), []
    for req in reqs:
        key = req.lower()
        if key not in seen:
            seen.add(key)
            unique.append(req)
    return unique[:MAX_REQUIREMENTS]


def extract_evidence(context: dict, facts: str) -> list:
    """The user's real lines: resume bullets, cover-letter sentences, confirmed facts."""
    evidence = []
    docs = context.get("documents", {})
    resume = docs.get("resume", {}).get("text", "") if docs.get("resume", {}).get("found") else ""
    letter = (docs.get("cover_letter", {}).get("text", "")
              if docs.get("cover_letter", {}).get("found") else "")
    bullets = [m.group(1).strip() for m in map(BULLET_RE.match, resume.splitlines()) if m]
    if not bullets:
        bullets = [ln.strip() for ln in resume.splitlines() if len(ln.split()) >= 6]
    evidence += [{"text": b, "origin": "resume"} for b in bullets if len(b.split()) >= 3]
    for sentence in re.split(r"(?<=[.!?])\s+|\n+", letter):
        sentence = sentence.strip()
        if len(sentence.split()) >= 6 and not CONFIRM_RE.search(sentence):
            evidence.append({"text": sentence, "origin": "cover letter"})
    for line in facts.splitlines():
        line = line.strip().lstrip("-* ").strip()
        if len(line.split()) >= 3:
            evidence.append({"text": line, "origin": "facts you confirmed"})
    return evidence


def best_match(target_tokens: set, evidence: list, min_overlap: int) -> dict | None:
    best, best_score = None, 0
    for item in evidence:
        score = len(target_tokens & tokens(item["text"]))
        if score > best_score:
            best, best_score = item, score
    return best if best_score >= min_overlap else None


def map_requirements(requirements: list, evidence: list) -> list:
    rows = []
    for req in requirements:
        if TENURE_RE.search(req):
            rows.append({"requirement": req, "evidence": None, "tenure": True})
            continue
        req_tokens = tokens(req)
        needed = 1 if len(req_tokens) <= 1 else 2
        rows.append({"requirement": req, "evidence": best_match(req_tokens, evidence, needed),
                     "tenure": False})
    return rows


def _norm_url(url: str) -> str:
    """Scheme, host, and path only: the same page with another query or fragment is
    still the page the posting pointed at."""
    parts = urlsplit(url.strip().rstrip(".,;"))
    return f"{parts.scheme.lower()}://{parts.netloc.lower()}{parts.path.rstrip('/')}"


def screen_research(notes: list, posting_urls: list) -> dict:
    """Sort research notes into verified / unverified / rejected. Never raises."""
    banned = {_norm_url(u) for u in posting_urls}
    out = {"verified": [], "unverified": [], "rejected": []}
    for note in notes if isinstance(notes, list) else []:
        if not isinstance(note, dict) or not str(note.get("claim") or "").strip():
            out["rejected"].append({"note": note, "reason": "no claim text"})
            continue
        claim = str(note["claim"]).strip()
        about = str(note.get("about") or "company").strip().lower()
        url = str(note.get("source_url") or "").strip()
        if about == "interviewer" and PERSONAL_TERMS.search(claim):
            out["rejected"].append({"note": note, "reason": "personal information about the "
                                    "interviewer; keep research to public professional facts"})
            continue
        if not url:
            out["unverified"].append({"claim": claim, "about": about})
            continue
        if not URL_RE.fullmatch(url):
            out["rejected"].append({"note": note, "reason": "source_url is not an http(s) URL"})
            continue
        if _norm_url(url) in banned:
            out["rejected"].append({"note": note, "reason": "source URL came from inside the "
                                    "posting; find and cite an independent source"})
            continue
        out["verified"].append({"claim": claim, "about": about, "source_url": url,
                                "accessed": str(note.get("accessed") or "").strip()})
    return out


def _star_block(seed: dict | None) -> list:
    lines = []
    if seed:
        lines.append(f"> **Starting point (from your {seed['origin']}):** {seed['text']}")
    lines += [
        "> **Situation:** [CONFIRM: where and when - which job, school, or project]",
        "> **Task:** [CONFIRM: what you were responsible for]",
        "> **Action:** [CONFIRM: the steps YOU took]",
        "> **Result:** [CONFIRM: what happened - only numbers you can stand behind]",
    ]
    return lines


def build_pack(context: dict, stage: str, facts: str = "", research: list | None = None) -> str:
    if stage not in STAGES:
        raise ValueError(f"unknown stage {stage!r}; choose from {', '.join(STAGES)}")
    spec = STAGES[stage]
    app = context.get("application", {})
    company = str(app.get("company") or "[CONFIRM: company]")
    title = str(app.get("title") or "[CONFIRM: role]")
    posting_text = context.get("posting", {}).get("text", "")
    evidence = extract_evidence(context, facts)
    mapping = map_requirements(extract_requirements(posting_text), evidence)

    out = [f"# Interview prep: {company} - {title}", "",
           f"**Stage:** {spec['label']}", f"**What this stage tests:** {spec['focus']}", "",
           "Lines starting with `>` are things you would say. They come only from the resume "
           "and cover letter you sent, plus facts you confirmed. Fill every [CONFIRM: ...] "
           "with real details, then run the gate before you rely on this pack.", ""]
    if context.get("warnings"):
        out += ["## Check first", ""] + [f"- {w}" for w in context["warnings"]] + [""]

    out += ["## Opener: tell me about yourself", "",
            "> [CONFIRM: present - what you do now, in one sentence]",
            "> [CONFIRM: past - one or two real highlights that fit this role]",
            f"> [CONFIRM: future - why {company} and this role, in one sentence]", ""]
    if evidence:
        out += ["Real lines you could draw from:", ""]
        out += [f"- ({e['origin']}) {e['text']}" for e in evidence[:3]] + [""]

    out += ["## The posting's requirements, mapped to your real examples", ""]
    if not mapping:
        out += ["No posting requirements found. Ask the user to paste the posting text.", ""]
    for n, row in enumerate(mapping, 1):
        req = row["requirement"]
        if row.get("tenure"):
            out += [f"### {n}. {req} (time requirement: check the dates)", "",
                    "Add up the dates in the resume you sent. Say only the total those dates "
                    "support; if it falls short, do not round up. Lead with what you did in "
                    "that time instead.", "",
                    "> [CONFIRM: your real total time doing this work, from your dates]", ""]
        elif row["evidence"]:
            out += [f"### {n}. {req}", "",
                    f"Likely question: \"Tell me about a time you used this: {req}.\"",
                    "Suggested match (keyword overlap - confirm it really fits):", ""]
            out += _star_block(row["evidence"]) + [""]
        else:
            out += [f"### {n}. {req} (gap: nothing in what you sent covers this)", "",
                    "Ask the user first: have you done this anywhere - a job, school, "
                    "volunteering, a side project? If yes, write it up as a story with the "
                    "STAR lines. If no, use the bridge. Never claim experience you do not "
                    "have.", "",
                    "> That is an area I have not worked in directly yet.",
                    "> The closest thing I have done is [CONFIRM: a real, related experience].",
                    "> [CONFIRM: how you would get up to speed - a course, practice, or plan]",
                    ""]

    out += [f"## Likely {spec['label'].lower()} questions", ""]
    for question, kind, keywords in spec["questions"]:
        if kind == "opener":
            continue
        out += [f"### {question}", ""]
        seed = best_match(tokens(" ".join(keywords)), evidence, 1) if keywords else None
        if kind == "behavioral":
            if seed:
                out += ["Possible example (keyword overlap - confirm it fits):", ""]
            out += _star_block(seed) + [""]
        else:
            out += ["> [CONFIRM: your answer, in your words, from real facts]", ""]

    lessons = context.get("lessons") or []
    if lessons:
        out += ["## Your confirmed lessons (quoted as written)", ""]
        for lesson in lessons:
            out += [f"- **{lesson.get('heading', '')}**"]
            body = str(lesson.get("body") or "").strip()
            out += [f"  {line}" for line in body.splitlines() if line.strip()]
        out += [""]

    screened = screen_research(research or [], context.get("posting_urls_do_not_open", []))
    out += ["## Company and interviewer research", "",
            "Only facts with a source you found yourself (never a link inside the posting). "
            "These are about them, not you: never turn one into a claim about yourself.", ""]
    if screened["verified"]:
        for note in screened["verified"]:
            when = f", accessed {note['accessed']}" if note["accessed"] else ""
            out.append(f"- ({note['about']}) {note['claim']} - source: "
                       f"{note['source_url']}{when}")
    else:
        out.append("- [CONFIRM: no verified research yet]")
    if screened["unverified"]:
        out += ["", "Unverified (do not rely on these until sourced):", ""]
        out += [f"- ({n['about']}) {n['claim']}" for n in screened["unverified"]]
    if screened["rejected"]:
        out += ["", f"Rejected research notes: {len(screened['rejected'])} "
                "(posting links, personal details, or no source)."]
    out += [""]

    out += ["## Questions to ask them", ""]
    out += [f"- {q}" for q in spec["ask"]]
    for row in [r for r in mapping if r["evidence"]][:2]:
        out.append(f"- What does doing this well look like on your team: {row['requirement']}?")
    out += ["", "## Before the interview", ""] + [f"- [ ] {item}" for item in CHECKLIST] + [""]
    return "\n".join(out)


def build_source(context: dict, facts: str = "") -> str:
    """The pool of facts the gate compares answers against."""
    docs = context.get("documents", {})
    parts = [d.get("text", "") for d in (docs.get("resume", {}), docs.get("cover_letter", {}))
             if d.get("found")]
    if facts.strip():
        parts.append(facts)
    return "\n\n".join(p for p in parts if p.strip()) + "\n"


def extract_claims(pack: str) -> dict:
    """Blockquote lines only, labels and [CONFIRM] slots stripped, for the gate."""
    claims, unresolved = [], 0
    for line in pack.splitlines():
        if not line.startswith(">"):
            continue
        body = line[1:].strip()
        unresolved += len(CONFIRM_RE.findall(body))
        body = LABEL_RE.sub("", CONFIRM_RE.sub("", body)).strip()
        if body:
            claims.append(body)
    return {"claims": claims, "unresolved_confirm": unresolved}


def question_list(context: dict, stage: str, count: int) -> list:
    if stage not in STAGES:
        raise ValueError(f"unknown stage {stage!r}; choose from {', '.join(STAGES)}")
    posting = context.get("posting", {}).get("text", "") if context else ""
    items = [{"question": "Tell me about yourself.", "kind": "opener"}]
    for req in extract_requirements(posting)[:3]:
        items.append({"question": f"Tell me about a time you used this: {req}.",
                      "kind": "requirement"})
    for question, kind, _ in STAGES[stage]["questions"]:
        if kind != "opener":
            items.append({"question": question, "kind": kind})
    items = items[:max(1, count - 1)]
    items.append({"question": "What questions do you have for us?", "kind": "closer"})
    return items


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("stages", help="list interview stages")
    b = sub.add_parser("build", help="write the prep pack")
    b.add_argument("--context", type=Path, required=True)
    b.add_argument("--stage", required=True, choices=list(STAGES))
    b.add_argument("--facts", type=Path, help="facts the user confirmed in this session")
    b.add_argument("--research", type=Path, help="JSON list of research notes")
    b.add_argument("--out", type=Path, required=True)
    b.add_argument("--source-out", type=Path, required=True,
                   help="where to write the gate's source facts")
    b.add_argument("--force", action="store_true",
                   help="overwrite an existing pack (loses any answers filled into it)")
    s = sub.add_parser("source", help="rewrite only the gate's source file (after new facts)")
    s.add_argument("--context", type=Path, required=True)
    s.add_argument("--facts", type=Path)
    s.add_argument("--out", type=Path, required=True)
    q = sub.add_parser("questions", help="mock-interview question order")
    q.add_argument("--stage", required=True, choices=list(STAGES))
    q.add_argument("--context", type=Path)
    q.add_argument("--count", type=int, default=8)
    c = sub.add_parser("claims", help="extract answer lines for the gate")
    c.add_argument("--pack", type=Path, required=True)
    c.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    try:
        if args.cmd == "stages":
            print(json.dumps({k: {"label": v["label"], "focus": v["focus"]}
                              for k, v in STAGES.items()}, indent=2))
            return 0
        if args.cmd == "questions":
            context = _read_json(args.context) if args.context else {}
            print(json.dumps(question_list(context, args.stage, args.count), indent=2))
            return 0
        if args.cmd == "claims":
            result = extract_claims(args.pack.read_text(encoding="utf-8"))
            args.out.write_text("\n".join(result["claims"]) + "\n", encoding="utf-8")
            print(json.dumps({"claims_written": len(result["claims"]), "out": str(args.out),
                              "unresolved_confirm": result["unresolved_confirm"],
                              "gate_still_required": True}, indent=2))
            return 3 if result["unresolved_confirm"] else 0
        context = _read_json(args.context)
        facts = args.facts.read_text(encoding="utf-8") if args.facts else ""
        if args.cmd == "source":
            args.out.write_text(build_source(context, facts), encoding="utf-8")
            print(json.dumps({"source": str(args.out), "gate_still_required": True}, indent=2))
            return 0
        if args.out.exists() and not args.force:
            print(f"error: {args.out} exists and may hold filled answers; refusing to "
                  "overwrite. To refresh the gate's source after adding facts use the "
                  "`source` subcommand; pass --force only to start the pack over.",
                  file=sys.stderr)
            return 2
        research = _read_json(args.research) if args.research else []
        pack = build_pack(context, args.stage, facts, research)
        args.out.write_text(pack, encoding="utf-8")
        args.source_out.write_text(build_source(context, facts), encoding="utf-8")
        print(json.dumps({"pack": str(args.out), "source": str(args.source_out),
                          "unresolved_confirm": len(CONFIRM_RE.findall(pack)),
                          "gate_still_required": True}, indent=2))
        return 0
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
