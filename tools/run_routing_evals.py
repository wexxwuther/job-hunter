#!/usr/bin/env python3
"""Live family-routing evals for the job-hunter family.

Runs every unique trigger-eval query from the 8 members through the real
`claude -p` CLI (the user's actual environment: all installed skills compete)
and records which skill Claude actually invokes, from the stream-json tool
calls, not from self-report.

Scoring per query:
  expected = members whose trigger-evals.json has should_trigger: true
  positive (expected non-empty):
    strict  pass: routed skill in expected
    lenient pass: routed skill in expected or the orchestrator (job-hunter),
                  since the orchestrator legitimately routes onward
  negative (expected empty): pass if no family skill was routed

Usage:
  python tools/run_routing_evals.py --out-dir <dir> --dry-run
  python tools/run_routing_evals.py --out-dir <dir> [--workers 3] [--max N]

Raw stream output is kept per query; reruns skip queries that already have a
result event (so an interrupted run resumes without re-spending).
Cost: each call loads the full user environment (~50-100k tokens).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MEMBERS = ("job-hunter", "career-profile", "job-search", "resume-tailor",
           "cover-letter", "application-tracker", "outcome-learning", "interview-prep")
ORCHESTRATOR = "job-hunter"
ALLOWED_TOOLS = ["Skill"]
DISALLOWED_TOOLS = ["Read", "Glob", "Grep", "Bash", "Write", "Edit", "NotebookEdit",
                    "WebSearch", "WebFetch", "Agent", "Task"]
SKILL_MD_RE = re.compile(r"[\\/]skills[\\/]([^\\/]+)[\\/]SKILL\.md$", re.IGNORECASE)


LABELS = Path(__file__).with_name("routing-labels.json")


def load_cases(repo: Path = REPO, labels_path: Path = LABELS) -> list[dict]:
    """One case per unique query.

    expected = members whose eval says should_trigger: true. A false only means
    "not this member", so a query no member claims MUST have a reviewed label in
    routing-labels.json (raises otherwise). Labels also override member claims.
    """
    cases: dict[str, dict] = {}
    for member in MEMBERS:
        path = repo / member / "evals" / "trigger-evals.json"
        for entry in json.loads(path.read_text(encoding="utf-8")):
            q = entry["query"].strip()
            case = cases.setdefault(q, {"query": q, "expected": [], "allow_none": False,
                                        "sources": [], "label": None})
            case["sources"].append(f"{member}#{entry['id']}:{'T' if entry['should_trigger'] else 'F'}")
            if entry["should_trigger"]:
                case["expected"].append(member)
    labels = json.loads(labels_path.read_text(encoding="utf-8"))["labels"]
    for lab in labels:
        case = cases.get(lab["query"].strip())
        if case is None:
            raise ValueError(f"routing label for unknown query: {lab['query']!r}")
        case.update(expected=list(lab["expected"]), allow_none=bool(lab["allow_none"]), label=lab["why"])
    unlabeled = [c["query"] for c in cases.values() if not c["expected"] and c["label"] is None]
    if unlabeled:
        raise ValueError(f"queries no member claims need a routing label: {unlabeled}")
    return list(cases.values())


def parse_ids(spec: str) -> set[int]:
    """'7,8,13-18' -> {7, 8, 13, 14, 15, 16, 17, 18}"""
    ids: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            lo, hi = part.split("-", 1)
            ids.update(range(int(lo), int(hi) + 1))
        elif part:
            ids.add(int(part))
    return ids


def normalize_skill(name: str) -> str:
    """'plugin:job-search' / 'job-search-v0.2' style names -> bare member name if it is one."""
    bare = name.split(":")[-1].strip()
    return bare


def routed_skill(events: list[dict]) -> tuple[str | None, list[str]]:
    """First skill Claude invoked (Skill tool, or a Read of a SKILL.md), plus all seen."""
    seen: list[str] = []
    for e in events:
        if e.get("type") != "assistant":
            continue
        for c in e.get("message", {}).get("content", []) or []:
            if c.get("type") != "tool_use":
                continue
            inp = c.get("input") or {}
            name = None
            if c.get("name") == "Skill":
                name = inp.get("skill") or inp.get("command") or inp.get("name")
            elif c.get("name") == "Read":
                m = SKILL_MD_RE.search(str(inp.get("file_path", "")))
                name = m.group(1) if m else None
            if name:
                seen.append(normalize_skill(str(name)))
    return (seen[0] if seen else None), seen


def score(case: dict, routed: str | None) -> dict:
    """strict: routed is an expected member (or, if allow_none, no family skill).
    lenient: also accept the orchestrator for in-domain queries (it routes onward)."""
    expected = set(case["expected"])
    no_family = routed not in MEMBERS
    strict = routed in expected or (case.get("allow_none", False) and no_family)
    lenient = strict or (bool(expected) and routed == ORCHESTRATOR)
    return {"strict": strict, "lenient": lenient}


def parse_stream(text: str) -> list[dict]:
    events = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def _kill_tree(proc: subprocess.Popen) -> None:
    """Kill claude and its children (MCP servers) so nothing keeps spending."""
    if proc.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)],
                       capture_output=True)
    else:
        proc.kill()


def _is_done(events: list[dict]) -> bool:
    return any(e.get("type") in ("result", "routing_stop") for e in events)


def run_case(case: dict, idx: int, raw_dir: Path, cwd: Path, timeout: int) -> dict:
    """Stream claude -p output and stop at the first routing signal.

    Once a skill is invoked the routing decision is made; letting the session
    carry on doing the task only spends tokens (observed $0.9-1.4 per query).
    Early-stopped runs have no CLI result event, so their cost is unknown.
    """
    raw = raw_dir / f"{idx:03d}.jsonl"
    events = parse_stream(raw.read_text(encoding="utf-8")) if raw.exists() else []
    if not _is_done(events):
        exe = shutil.which("claude")
        if not exe:
            raise SystemExit("claude CLI not found on PATH")
        cmd = [exe, "-p", "--output-format", "stream-json", "--verbose",
               "--no-session-persistence", "--max-turns", "2",
               "--allowedTools", *ALLOWED_TOOLS, "--disallowedTools", *DISALLOWED_TOOLS]
        proc = subprocess.Popen(cmd, cwd=cwd, text=True, encoding="utf-8", errors="replace",
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL)
        proc.stdin.write(case["query"])
        proc.stdin.close()
        timer = threading.Timer(timeout, _kill_tree, args=(proc,))
        timer.start()
        lines: list[str] = []
        try:
            for line in proc.stdout:
                lines.append(line)
                routed, _ = routed_skill(parse_stream(line))
                if routed:
                    lines.append(json.dumps({"type": "routing_stop", "skill": routed}) + "\n")
                    _kill_tree(proc)
                    break
        finally:
            timer.cancel()
            _kill_tree(proc)
            raw.write_text("".join(lines), encoding="utf-8")
        events = parse_stream(raw.read_text(encoding="utf-8"))
    routed, seen = routed_skill(events)
    result = next((e for e in events if e.get("type") == "result"), {})
    init = next((e for e in events if e.get("type") == "system" and e.get("subtype") == "init"), {})
    return {
        "id": idx, **case, "routed": routed, "all_skills_invoked": seen,
        **score(case, routed),
        "completed": _is_done(events),
        "result_subtype": result.get("subtype") or ("routing_stop" if _is_done(events) else None),
        "cost_usd": result.get("total_cost_usd") or 0.0,
        "model": init.get("model"),
    }


def render_report(rows: list[dict]) -> str:
    pos = [r for r in rows if r["expected"]]
    neg = [r for r in rows if not r["expected"]]  # off-domain: no family skill wanted
    def pct(n, d):
        return f"{n}/{d} ({(100 * n / d):.0f}%)" if d else "0/0"
    models = sorted({r["model"] for r in rows if r["model"]})
    lines = [
        "# job-hunter family routing evals (live claude -p)", "",
        f"- Model(s): {', '.join(models) or 'unknown'}",
        f"- Queries: {len(rows)} ({len(pos)} positive, {len(neg)} negative); completed: {sum(r['completed'] for r in rows)}",
        f"- Positive strict: {pct(sum(r['strict'] for r in pos), len(pos))}; lenient (orchestrator ok): {pct(sum(r['lenient'] for r in pos), len(pos))}",
        f"- Negative (no family skill): {pct(sum(r['strict'] for r in neg), len(neg))}",
        f"- Cost (CLI-reported, completed calls only): ${sum(r['cost_usd'] for r in rows):.2f}; "
        f"early-stopped at first skill call (cost not reported): {sum(r['result_subtype'] == 'routing_stop' for r in rows)}", "",
        "## Misses", "",
        "| # | query | expected | routed | lenient | sources |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows:
        if not r["strict"]:
            q = r["query"].replace("|", "/")[:90]
            lines.append(f"| {r['id']} | {q} | {', '.join(r['expected']) or '(none)'} | "
                         f"{r['routed'] or '(none)'} | {'yes' if r['lenient'] else 'NO'} | {'; '.join(r['sources'])} |")
    lines += ["", "## Conflicts in eval expectations (query claimed by >1 member)", ""]
    for r in rows:
        if len(r["expected"]) > 1:
            lines.append(f"- {r['query'][:90]} -> {', '.join(r['expected'])}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out-dir", required=True, type=Path)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--max", type=int, help="only the first N queries")
    ap.add_argument("--ids", help="only these case numbers, e.g. 7,8,13-18 (numbering as in --dry-run)")
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--dry-run", action="store_true", help="print cases, call nothing")
    args = ap.parse_args(argv)

    numbered = list(enumerate(load_cases(), 1))
    if args.max:
        numbered = numbered[: args.max]
    if args.ids:
        wanted = parse_ids(args.ids)
        numbered = [(i, c) for i, c in numbered if i in wanted]
    if args.dry_run:
        for i, c in numbered:
            exp = ",".join(c["expected"]) + ("|none" if c["allow_none"] else "")
            print(f"{i:3d} {exp or 'none':32s} {c['query'][:80]}")
        print(f"{len(numbered)} cases")
        return 0

    out = args.out_dir.resolve()
    raw_dir, cwd = out / "raw", out / "cwd"
    raw_dir.mkdir(parents=True, exist_ok=True)
    cwd.mkdir(exist_ok=True)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        rows = list(pool.map(lambda ic: run_case(ic[1], ic[0], raw_dir, cwd, args.timeout),
                             numbered))
    (out / "results.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    report = render_report(rows)
    (out / "report.md").write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
