#!/usr/bin/env python3
"""
extract_ats_keywords.py

Run a keyword gap analysis between a job description and a resume. Mirrors the Phase 3 step
in SKILL.md but produces a deterministic, reproducible breakdown the agent can present to the
user before tailoring.

The three output categories match the SKILL.md contract:
  1. present       - keyword appears in both JD and resume (no change needed; may want emphasis)
  2. matchable     - keyword appears in JD; related/adjacent terms appear in resume (rephrase target)
  3. missing       - keyword appears in JD; nothing related in resume (honest gap)

Usage:
    python extract_ats_keywords.py --jd jd.txt --resume resume.txt
    python extract_ats_keywords.py --jd jd.txt --resume resume.txt --json
    python extract_ats_keywords.py --jd-text "..." --resume resume.txt

Inputs must be plain text. For .docx/.pdf, convert first (the docx/pdf skills handle this).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from typing import Iterable


# Stopwords - common English plus job-posting boilerplate that shouldn't count as a "keyword"
STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "then", "else", "for", "to", "of", "in", "on",
    "at", "by", "with", "from", "as", "is", "are", "was", "were", "be", "been", "being", "have",
    "has", "had", "do", "does", "did", "doing", "this", "that", "these", "those", "i", "you",
    "he", "she", "it", "we", "they", "their", "our", "your", "his", "her", "its", "us", "them",
    "me", "my", "mine", "yours", "ours", "theirs", "what", "which", "who", "whom", "whose",
    "when", "where", "why", "how", "all", "any", "both", "each", "few", "more", "most", "other",
    "some", "such", "no", "not", "only", "own", "same", "so", "than", "too", "very", "s", "t",
    "can", "will", "just", "should", "now", "also", "may", "might", "must", "shall", "would",
    "could",
    # Job-posting boilerplate
    "experience", "experienced", "skills", "skill", "ability", "abilities", "knowledge",
    "understanding", "strong", "excellent", "good", "great", "deep", "solid", "proven", "demonstrated",
    "years", "year", "minimum", "preferred", "required", "requirements", "qualifications",
    "responsibilities", "duties", "role", "position", "job", "candidate", "candidates",
    "company", "team", "teams", "work", "working", "works", "worked", "looking", "seeking",
    "join", "us", "we", "our", "office", "remote", "hybrid", "onsite", "etc", "including",
    "include", "includes", "across", "within", "through", "ensure", "ensuring", "manage",
    "managing", "managed", "develop", "developing", "developed", "build", "building", "built",
    "design", "designing", "designed", "implement", "implementing", "implemented",
    "create", "creating", "created", "lead", "leading", "led", "support", "supporting",
    "supported", "collaborate", "collaborating", "collaborated", "drive", "driving", "drove",
    "bonus", "plus", "ideal", "ideally", "nice", "want", "wants", "wanted",
}

# Adjacency map - if JD has a key on the left and resume has any term on the right,
# the JD keyword is "matchable" not "missing"
ADJACENCY: dict[str, list[str]] = {
    "kubernetes": ["k8s", "containerization", "orchestration", "eks", "gke", "aks"],
    "k8s": ["kubernetes"],
    "docker": ["containerization", "containers", "container"],
    "aws": ["amazon web services", "ec2", "s3", "lambda", "rds", "cloudformation"],
    "gcp": ["google cloud", "google cloud platform", "bigquery", "gke"],
    "azure": ["microsoft azure"],
    "terraform": ["iac", "infrastructure as code", "opentofu"],
    "ci/cd": ["continuous integration", "continuous delivery", "jenkins", "github actions",
              "gitlab ci", "circleci"],
    "python": ["py", "django", "flask", "fastapi"],
    "javascript": ["js", "node", "nodejs", "typescript", "ts", "react", "vue"],
    "typescript": ["ts", "javascript"],
    "react": ["reactjs", "next.js", "nextjs"],
    "sql": ["postgres", "postgresql", "mysql", "snowflake", "bigquery", "redshift"],
    "etl": ["data pipeline", "data pipelines", "elt"],
    "machine learning": ["ml", "deep learning", "neural networks", "pytorch", "tensorflow"],
    "ml": ["machine learning", "pytorch", "tensorflow"],
    "data science": ["analytics", "statistics", "modeling"],
    "agile": ["scrum", "sprint", "kanban"],
    "scrum": ["agile"],
    "rest": ["restful", "rest api", "rest apis"],
    "graphql": ["gql"],
    "microservices": ["service-oriented", "soa"],
    "leadership": ["led", "managed", "mentored", "directed"],
}


def _tokenize(text: str) -> list[str]:
    text = text.lower()
    tokens = re.findall(r"[a-z][a-z0-9+#\-\/]{0,30}(?:\.(?:js|net|io|com|ai))?", text)
    cleaned: list[str] = []
    for t in tokens:
        t = t.strip(".,;:!?()[]{}\"'`")
        if t and t not in STOPWORDS and len(t) >= 2:
            cleaned.append(t)
    return cleaned


def _ngrams(tokens: list[str], n: int) -> list[str]:
    return [" ".join(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]


def _extract_candidates(text: str) -> set[str]:
    tokens = _tokenize(text)
    grams = set(tokens) | set(_ngrams(tokens, 2)) | set(_ngrams(tokens, 3))
    grams = {g for g in grams if not g.isdigit()}
    return grams


def _term_in_text(term: str, text_lower: str) -> bool:
    pattern = r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])"
    return re.search(pattern, text_lower) is not None


def _jd_emphasis_score(term: str, jd_lower: str) -> int:
    matches = re.findall(r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])", jd_lower)
    return len(matches)


def analyze(jd: str, resume: str, top_n: int = 30) -> dict:
    if not jd or not jd.strip():
        raise ValueError("job description must be non-empty")
    if not resume or not resume.strip():
        raise ValueError("resume must be non-empty")

    jd_lower = jd.lower()
    resume_lower = resume.lower()

    jd_candidates = _extract_candidates(jd)

    scored = []
    for cand in jd_candidates:
        if len(cand) < 2 or cand in STOPWORDS:
            continue
        emphasis = _jd_emphasis_score(cand, jd_lower)
        if emphasis == 0:
            continue
        scored.append((cand, emphasis))

    scored.sort(key=lambda x: (-x[1], x[0]))
    top_terms = [t for t, _ in scored[:top_n]]

    present: list[dict] = []
    matchable: list[dict] = []
    missing: list[dict] = []

    for term in top_terms:
        emphasis = _jd_emphasis_score(term, jd_lower)
        in_resume = _term_in_text(term, resume_lower)

        if in_resume:
            present.append({"term": term, "jd_mentions": emphasis})
            continue

        adjacents = ADJACENCY.get(term, [])
        matched_adj = [a for a in adjacents if _term_in_text(a, resume_lower)]
        if matched_adj:
            matchable.append({
                "term": term,
                "jd_mentions": emphasis,
                "resume_has_related": matched_adj,
                "suggestion": f"You use {matched_adj[0]!r} on your resume; consider also using "
                              f"the term {term!r} to mirror the JD.",
            })
            continue

        missing.append({"term": term, "jd_mentions": emphasis})

    return {
        "summary": {
            "jd_terms_analyzed": len(top_terms),
            "present_count": len(present),
            "matchable_count": len(matchable),
            "missing_count": len(missing),
        },
        "present": present,
        "matchable": matchable,
        "missing": missing,
    }


def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _format_text(analysis: dict) -> str:
    lines = []
    s = analysis["summary"]
    lines.append("# Keyword Gap Analysis")
    lines.append("")
    lines.append(f"Top {s['jd_terms_analyzed']} JD keywords analyzed:")
    lines.append(f"  - Present in resume:    {s['present_count']}")
    lines.append(f"  - Matchable (rephrase): {s['matchable_count']}")
    lines.append(f"  - Missing (honest gap): {s['missing_count']}")
    lines.append("")

    if analysis["present"]:
        lines.append("## Present (no change needed; consider emphasizing)")
        for p in analysis["present"]:
            lines.append(f"  - {p['term']}  (JD mentions: {p['jd_mentions']})")
        lines.append("")

    if analysis["matchable"]:
        lines.append("## Matchable (rephrase to mirror JD language)")
        for m in analysis["matchable"]:
            related = ", ".join(m["resume_has_related"])
            lines.append(f"  - {m['term']}  (JD mentions: {m['jd_mentions']}; you have: {related})")
            lines.append(f"      {m['suggestion']}")
        lines.append("")

    if analysis["missing"]:
        lines.append("## Missing (honest gaps - flag to the user)")
        for m in analysis["missing"]:
            lines.append(f"  - {m['term']}  (JD mentions: {m['jd_mentions']})")
        lines.append("")
        lines.append("  Address these in the cover letter, learn the skill, or weigh whether the")
        lines.append("  role is still worth applying to.")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group_jd = parser.add_mutually_exclusive_group(required=True)
    group_jd.add_argument("--jd", help="path to job description text file")
    group_jd.add_argument("--jd-text", help="job description as inline text")

    group_resume = parser.add_mutually_exclusive_group(required=True)
    group_resume.add_argument("--resume", help="path to resume text file")
    group_resume.add_argument("--resume-text", help="resume as inline text")

    parser.add_argument("--top-n", type=int, default=30,
                        help="how many top JD keywords to analyze (default 30)")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    args = parser.parse_args(argv)

    try:
        jd_text = _read_text(args.jd) if args.jd else args.jd_text
        resume_text = _read_text(args.resume) if args.resume else args.resume_text
    except OSError as e:
        print(f"error: cannot read input: {e}", file=sys.stderr)
        return 2

    try:
        result = analyze(jd_text, resume_text, top_n=args.top_n)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(_format_text(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
