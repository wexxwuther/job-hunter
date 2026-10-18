#!/usr/bin/env python3
"""Live outcome evals for a job-hunter family member.

Runs each outcome eval through the real `claude -p` CLI (the user's actual
environment: every installed skill loads) inside a fresh fictional workspace,
then grades the eval's assertions against what Claude actually did.

A scenarios file turns each eval's parenthetical setup ("tracker.json has the
Globex entry ...") into real files, and its prompt into one or more user
turns; turns after the first resume the same session. Assertions and
expected_output are read from the member's outcome-evals.json by id, so the
scenarios file cannot drift from the eval it runs.

Grading (automatic, case-insensitive): mentions_all / mentions_any /
mentions_none over the assistant's text plus its tool-call inputs (commands,
written file contents) across all turns. Tool results (e.g. the posting text
read from disk) are input, not output, and are not graded. Assertions are a
floor, not the verdict: put a manual verdict per case against expected_output
in <out-dir>/manual-review.json ({"<id>": {"verdict": ..., "notes": ...}}) and
rerun (completed cases are reused, not re-spent) to merge it into the report.

User hooks are disabled for the eval sessions (--settings disableAllHooks):
the user's Stop/memory hooks would otherwise steer the session into unrelated
work. Skills, plugins and MCP config still load.

Usage:
  python tools/run_outcome_evals.py --scenarios tools/outcome-scenarios/interview-prep.json \
      --out-dir <dir outside the repo> [--ids 1,3] [--max-budget-usd 5] [--invoke-skill]

Natural routing (default) also measures whether the skill triggers at all in a
plain environment; --invoke-skill measures the skill's behavior once loaded.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import threading
import uuid
from pathlib import Path, PurePosixPath, PureWindowsPath

REPO = Path(__file__).resolve().parent.parent
ALLOWED_TOOLS = ["Skill", "Read", "Write", "Edit", "Glob", "Grep",
                 "Bash(python:*)", "Bash(mkdir:*)", "Bash(ls:*)", "WebSearch", "WebFetch"]
DISALLOWED_TOOLS = ["Agent", "Task", "NotebookEdit"]
NO_HOOKS = '{"disableAllHooks": true}'
KINDS = ("mentions_all", "mentions_any", "mentions_none")


def parse_ids(spec: str) -> set[int]:
    ids: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            lo, hi = part.split("-", 1)
            ids.update(range(int(lo), int(hi) + 1))
        elif part:
            ids.add(int(part))
    return ids


def load_cases(scenarios_path: Path) -> list[dict]:
    """Scenario cases joined with their eval's assertions and expected_output."""
    sc = json.loads(Path(scenarios_path).read_text(encoding="utf-8"))
    evals_file = Path(sc["evals_file"])
    if not evals_file.is_absolute():
        evals_file = REPO / evals_file
    evals_doc = json.loads(evals_file.read_text(encoding="utf-8"))
    evals = {e["id"]: e for e in evals_doc["evals"]}
    cases = []
    for c in sc["cases"]:
        if c["id"] not in evals:
            raise ValueError(f"scenario for unknown eval id {c['id']} in {evals_file}")
        if c["fixture"] not in sc["fixtures"]:
            raise ValueError(f"case {c['id']}: unknown fixture {c['fixture']!r}")
        ev = evals[c["id"]]
        files = {**sc["fixtures"][c["fixture"]], **c.get("files", {})}
        cases.append({"id": c["id"], "skill": evals_doc.get("skill_name", ""),
                      "fixture": c["fixture"], "files": files,
                      "turns": list(c["turns"]), "setup_note": c.get("note", ""),
                      "eval_prompt": ev["prompt"], "expected_output": ev["expected_output"],
                      "assertions": ev["assertions"]})
    missing = sorted(set(evals) - {c["id"] for c in cases})
    if missing:
        print(f"note: no scenario for eval ids {missing}", file=sys.stderr)
    return cases


def build_workspace(ws: Path, files: dict[str, str]) -> None:
    """Fresh workspace holding exactly the fixture files."""
    for rel in files:
        if PurePosixPath(rel).is_absolute() or PureWindowsPath(rel).is_absolute() \
                or PureWindowsPath(rel).drive or ".." in PureWindowsPath(rel).parts:
            raise ValueError(f"fixture path must be relative and inside the workspace: {rel!r}")
    if ws.exists():
        shutil.rmtree(ws)
    ws.mkdir(parents=True)
    for rel, content in files.items():
        p = ws / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8", newline="\n")


def parse_stream(text: str) -> list[dict]:
    events = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events


def haystack(events: list[dict]) -> str:
    """Assistant text + tool-call inputs. Tool results are not output."""
    parts = []
    for e in events:
        if e.get("type") != "assistant":
            continue
        for c in e.get("message", {}).get("content", []) or []:
            if c.get("type") == "text":
                parts.append(c.get("text", ""))
            elif c.get("type") == "tool_use":
                parts.append(json.dumps(c.get("input") or {}, ensure_ascii=False))
    return "\n".join(parts)


def tool_calls(events: list[dict]) -> list[dict]:
    calls = []
    for e in events:
        if e.get("type") != "assistant":
            continue
        for c in e.get("message", {}).get("content", []) or []:
            if c.get("type") == "tool_use":
                calls.append({"name": c.get("name"), "input": c.get("input") or {}})
    return calls


def grade(assertions: list[dict], hay: str) -> list[dict]:
    low = hay.lower()
    out = []
    for a in assertions:
        kind, values = a["kind"], a["values"]
        if kind not in KINDS:
            raise ValueError(f"unknown assertion kind {kind!r}")
        found = [v for v in values if v.lower() in low]
        if kind == "mentions_all":
            missing = [v for v in values if v not in found]
            out.append({**a, "passed": not missing, "missing": missing})
        elif kind == "mentions_any":
            out.append({**a, "passed": bool(found), "found": found})
        else:
            out.append({**a, "passed": not found, "found": found})
    return out


def result_event(events: list[dict]) -> dict | None:
    return next((e for e in events if e.get("type") == "result"), None)


def result_error(events: list[dict]) -> str | None:
    r = result_event(events)
    if r and (r.get("is_error") or str(r.get("subtype", "")).startswith("error")):
        return str(r.get("result") or r.get("subtype") or "error")
    return None


def _kill_tree(proc) -> None:
    if proc.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True)
    else:
        proc.kill()


def claude_cmd(exe: str, turn: int, session_id: str, budget: float, max_turns: int) -> list[str]:
    cmd = [exe, "-p", "--output-format", "stream-json", "--verbose",
           "--max-turns", str(max_turns), "--max-budget-usd", str(budget),
           "--settings", NO_HOOKS,
           "--allowedTools", *ALLOWED_TOOLS, "--disallowedTools", *DISALLOWED_TOOLS]
    cmd += ["--session-id", session_id] if turn == 1 else ["--resume", session_id]
    return cmd


def _run_turn(cmd: list[str], prompt: str, cwd: Path, raw: Path, timeout: int) -> list[dict]:
    proc = subprocess.Popen(cmd, cwd=str(cwd), text=True, encoding="utf-8", errors="replace",
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL)
    proc.stdin.write(prompt)
    proc.stdin.close()
    timer = threading.Timer(timeout, _kill_tree, args=(proc,))
    timer.start()
    lines: list[str] = []
    try:
        for line in proc.stdout:
            lines.append(line)
    finally:
        timer.cancel()
        _kill_tree(proc)
        raw.write_text("".join(lines), encoding="utf-8")
    return parse_stream("".join(lines))


def _done(events: list[dict]) -> bool:
    return result_event(events) is not None and result_error(events) is None


def run_case(case: dict, out: Path, timeout: int, budget: float, max_turns: int,
             invoke: bool = False) -> dict:
    raw_dir, ws = out / "raw", out / "ws" / f"{case['id']:03d}"
    raws = [raw_dir / f"{case['id']:03d}-t{n}.jsonl" for n in range(1, len(case["turns"]) + 1)]
    turns = [parse_stream(r.read_text(encoding="utf-8")) if r.exists() else [] for r in raws]
    if not all(_done(t) for t in turns):
        exe = shutil.which("claude")
        if not exe:
            raise SystemExit("claude CLI not found on PATH")
        build_workspace(ws, case["files"])
        session_id = str(uuid.uuid4())
        turns = []
        for n, (prompt, raw) in enumerate(zip(case["turns"], raws), 1):
            if n == 1 and invoke:
                prompt = f"/{case['skill']} {prompt}"
            events = _run_turn(claude_cmd(exe, n, session_id, budget, max_turns),
                               prompt, ws, raw, timeout)
            turns.append(events)
            if not _done(events):
                break
    all_events = [e for t in turns for e in t]
    error = next((result_error(t) or "no result event (killed or timed out)"
                  for t in turns if not _done(t)), None)
    if len(turns) < len(case["turns"]) and error is None:
        error = "turn missing"
    hay = haystack(all_events)
    graded = grade(case["assertions"], hay) if error is None else []
    results = [result_event(t) or {} for t in turns]
    init = next((e for e in all_events if e.get("type") == "system" and e.get("subtype") == "init"), {})
    calls = tool_calls(all_events)
    return {
        "id": case["id"], "skill": case["skill"], "fixture": case["fixture"], "eval_prompt": case["eval_prompt"],
        "turns": case["turns"], "setup_note": case["setup_note"],
        "expected_output": case["expected_output"], "workspace": str(ws),
        "invoked_explicitly": invoke,
        "errored": error is not None, "error": error,
        "assertions": graded,
        "auto_pass": None if error else all(g["passed"] for g in graded),
        "skills_invoked": list(dict.fromkeys(
            str(c["input"].get("skill")) for c in calls if c["name"] == "Skill")),
        "tool_calls": [{"name": c["name"],
                        "summary": str(c["input"].get("command") or c["input"].get("file_path")
                                       or c["input"].get("url") or c["input"].get("query")
                                       or c["input"].get("skill") or "")[:300]} for c in calls],
        "permission_denials": [d for r in results for d in (r.get("permission_denials") or [])],
        "final_texts": [str(r.get("result", "")) for r in results],
        "cost_usd": round(sum(float(r.get("total_cost_usd") or 0) for r in results), 4),
        "num_turns": [r.get("num_turns") for r in results],
        "model": init.get("model"),
        "manual_verdict": None, "manual_notes": None,
    }


def render_report(rows: list[dict], skill: str) -> str:
    scored = [r for r in rows if not r["errored"]]
    reviewed = [r for r in scored if r["manual_verdict"]]
    models = sorted({r["model"] for r in rows if r["model"]})
    lines = [
        f"# {skill} outcome evals (live claude -p)", "",
        f"- Model(s): {', '.join(models) or 'unknown'}",
        "- Mode: " + ("skill explicitly invoked (turn 1 starts with /<skill>)"
                      if any(r["invoked_explicitly"] for r in rows)
                      else "natural routing (user hooks disabled)"),
        f"- Cases: {len(rows)} ({len(rows) - len(scored)} errored, not scored)",
        f"- Assertions (automatic floor): {sum(bool(r['auto_pass']) for r in scored)}/{len(scored)} cases pass all",
        "- Manual review vs expected_output: "
        + (", ".join(f"{v}: {sum(r['manual_verdict'] == v for r in reviewed)}"
                     for v in sorted({r['manual_verdict'] for r in reviewed})) or "not recorded"),
        f"- Cost (CLI-reported): ${sum(r['cost_usd'] for r in rows):.2f}", "",
        "| # | auto | manual | skills | cost | failed assertions |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows:
        failed = "; ".join(f"{g['kind']}: {g.get('missing') or g.get('found')}"
                           for g in r["assertions"] if not g["passed"])
        auto = "ERR" if r["errored"] else ("pass" if r["auto_pass"] else "FAIL")
        # a slash-loaded skill makes no Skill tool call
        skills = ", ".join(r["skills_invoked"]) or (
            "/" + r["skill"] + " (slash)" if r["invoked_explicitly"] else "(none)")
        lines.append(f"| {r['id']} | {auto} | {r['manual_verdict'] or '-'} | {skills} | "
                     f"${r['cost_usd']:.2f} | {failed.replace('|', '/') or '-'} |")
    for r in rows:
        lines += ["", f"## Case {r['id']}", "",
                  f"- Eval prompt: {r['eval_prompt']}"]
        if r["setup_note"]:
            lines.append(f"- Setup: {r['setup_note']}")
        lines.append(f"- Expected: {r['expected_output']}")
        if r["errored"]:
            lines.append(f"- ERRORED: {r['error']}")
        if r["permission_denials"]:
            lines.append(f"- Permission denials: {len(r['permission_denials'])} "
                         f"({', '.join(sorted({str(d.get('tool_name')) for d in r['permission_denials']}))})")
        lines.append("- Tools: " + (", ".join(
            f"{c['name']}" for c in r["tool_calls"]) or "(none)"))
        if r["manual_notes"]:
            lines.append(f"- Manual review ({r['manual_verdict']}): {r['manual_notes']}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--scenarios", required=True, type=Path)
    ap.add_argument("--out-dir", required=True, type=Path)
    ap.add_argument("--ids", help="only these eval ids, e.g. 1,3-5")
    ap.add_argument("--timeout", type=int, default=900, help="seconds per turn")
    ap.add_argument("--max-budget-usd", type=float, default=5.0, help="per claude call")
    ap.add_argument("--max-turns", type=int, default=40, help="agent turns per claude call")
    ap.add_argument("--invoke-skill", action="store_true",
                    help="start turn 1 with /<skill> so the outcome is measured even when "
                         "natural routing would miss (use a separate --out-dir)")
    args = ap.parse_args(argv)

    cases = load_cases(args.scenarios)
    if args.ids:
        wanted = parse_ids(args.ids)
        cases = [c for c in cases if c["id"] in wanted]
    skill = json.loads(args.scenarios.read_text(encoding="utf-8")).get("skill", args.scenarios.stem)
    out = args.out_dir.resolve()
    (out / "raw").mkdir(parents=True, exist_ok=True)
    rows = [run_case(c, out, args.timeout, args.max_budget_usd, args.max_turns, args.invoke_skill)
            for c in cases]
    review_path = out / "manual-review.json"
    if review_path.exists():
        review = json.loads(review_path.read_text(encoding="utf-8"))
        for r in rows:
            rv = review.get(str(r["id"]))
            if rv:
                r["manual_verdict"], r["manual_notes"] = rv.get("verdict"), rv.get("notes")
    (out / "results.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    report = render_report(rows, skill)
    (out / "report.md").write_text(report, encoding="utf-8")
    print(report)
    n_err = sum(r["errored"] for r in rows)
    if n_err:
        print(f"ERROR: {n_err}/{len(rows)} cases errored; rerun the same --out-dir to retry them",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
