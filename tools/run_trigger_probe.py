#!/usr/bin/env python3
"""Natural-trigger probe: does turn 1 of an outcome case load the expected skill?

Measures how often a member's description makes Claude load the skill, with the
normal tool set of tools/run_outcome_evals.py (Skill, Read, Write, Edit, Glob,
Grep, Bash(python/mkdir/ls), WebSearch, WebFetch) and user hooks disabled.
run_routing_evals.py allows only the Skill tool, which overstates triggering.

Per case and sample: a fresh fixture workspace and session, turn 1 only. The
stream is read until the first Skill tool call (the routing decision); then the
process is killed. Otherwise it runs to its result (--max-turns, budget cap).

Outcomes per sample:
  skill     a Skill call; a hit when it names the expected skill
  answered  finished (result success) without any Skill call: a miss
  capped    stopped by --max-turns (error_max_turns) without a Skill call: a
            miss, counted separately
  errored   anything else (not logged in, killed, timed out, no init event, the
            expected skill missing from the session's listing, or user skills or
            plugins leaking into --family-only): not scored, the run exits 1 and
            a rerun with the same --out-dir retries only these samples

Environments:
  default        the machine's full install (every user skill, plugin and MCP)
  --family-only  --setting-sources project, cwd under a temp folder whose
                 .claude/skills holds only the 9 git-tracked members (tests/
                 excluded): those plus Claude Code's bundled skills load. The
                 closest model of a public install.

Usage:
  python tools/run_trigger_probe.py --scenarios tools/outcome-scenarios/interview-prep.json \
      --out-dir <dir outside the repo> --ids 2-4 --samples 3 --family-only [--dry-run]

Cost: one claude -p call per case and sample. Calls stopped at a Skill call
report no cost, so the CLI-reported total is a floor.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import threading
import uuid
from pathlib import Path, PurePosixPath

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_outcome_evals as roe  # noqa: E402
from run_routing_evals import MEMBERS  # noqa: E402

REPO = roe.REPO
CAPPED = "error_max_turns"


def family_files(repo: Path = REPO) -> list[str]:
    """Git-tracked files of the 9 members, without each member's tests/."""
    proc = subprocess.run(["git", "ls-files", "-z", "--", *MEMBERS], cwd=str(repo),
                          capture_output=True)
    if proc.returncode != 0:
        raise SystemExit(f"git ls-files failed in {repo}: "
                         f"{proc.stderr.decode('utf-8', 'replace').strip()}")
    files = [f for f in proc.stdout.decode("utf-8").split("\0") if f]
    keep = [f for f in files if PurePosixPath(f).parts[1:2] != ("tests",)]
    missing = [m for m in MEMBERS if f"{m}/SKILL.md" not in keep]
    if missing:
        raise SystemExit(f"members without a git-tracked SKILL.md: {missing}")
    return keep


def build_family_env(root: Path, files: list[str], repo: Path = REPO) -> None:
    """root/.claude/skills/<member>/... byte-identical to the repo."""
    skills = root / ".claude" / "skills"
    if skills.exists():
        shutil.rmtree(skills)
    for rel in files:
        dst = skills / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(repo / rel, dst)


def user_skill_names(user_skills_dir: Path | None = None) -> set[str]:
    d = user_skills_dir or Path.home() / ".claude" / "skills"
    return {p.name for p in d.iterdir() if p.is_dir()} if d.is_dir() else set()


def probe_cmd(exe: str, budget: float, max_turns: int, family: bool) -> list[str]:
    cmd = [exe, "-p", "--output-format", "stream-json", "--verbose",
           "--max-turns", str(max_turns), "--max-budget-usd", str(budget),
           "--settings", roe.NO_HOOKS,
           "--allowedTools", *roe.ALLOWED_TOOLS, "--disallowedTools", *roe.DISALLOWED_TOOLS,
           "--session-id", str(uuid.uuid4())]
    if family:
        cmd += ["--setting-sources", "project"]
    return cmd


def _skill_call(events: list[dict]) -> str | None:
    return next((str(c["input"].get("skill")) for c in roe.tool_calls(events)
                 if c["name"] == "Skill"), None)


def run_turn1(cmd: list[str], prompt: str, cwd: Path, raw: Path, timeout: int) -> list[dict]:
    """Stream turn 1; stop reading and kill the process at the first Skill call."""
    proc = subprocess.Popen(cmd, cwd=str(cwd), text=True, encoding="utf-8", errors="replace",
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL)
    proc.stdin.write(prompt)
    proc.stdin.close()
    timer = threading.Timer(timeout, roe._kill_tree, args=(proc,))
    timer.start()
    lines: list[str] = []
    try:
        for line in proc.stdout:
            lines.append(line)
            if _skill_call(roe.parse_stream(line)):
                break
    finally:
        timer.cancel()
        roe._kill_tree(proc)
        raw.write_text("".join(lines), encoding="utf-8")
    return roe.parse_stream("".join(lines))


def classify(events: list[dict], expected: str, family: bool,
             user_skills: set[str] = frozenset()) -> dict:
    init = next((e for e in events if e.get("type") == "system"
                 and e.get("subtype") == "init"), None)
    listed = list((init or {}).get("skills") or [])
    skill = _skill_call(events)
    res = roe.result_event(events)
    err = roe.result_error(events)
    capped = bool(res) and res.get("subtype") == CAPPED
    leaked = sorted((set(listed) & set(user_skills)) - set(MEMBERS)) if family else []
    plugins = list((init or {}).get("plugins") or []) if family else []
    error = outcome = None
    if err and not skill and not capped:
        error = err
    elif init is None:
        error = "no init event (CLI did not start a session)"
    elif expected not in listed:
        error = f"{expected} is not in the session's skill listing ({len(listed)} skills)"
    elif leaked or plugins:
        error = f"family-only env leaked user skills {leaked[:5]} or plugins {plugins[:5]}"
    elif skill:
        outcome = "skill"
    elif res is None:
        error = "no result event (killed or timed out)"
    elif capped:
        outcome = "capped"
    else:
        outcome = "answered"
    calls = roe.tool_calls(events)
    return {
        "outcome": outcome, "error": error, "skill": skill,
        "hit": None if error else (outcome == "skill" and skill == expected),
        "tools_before": [c["name"] for c in calls if c["name"] != "Skill"],
        "n_skills_listed": len(listed), "model": (init or {}).get("model"),
        "cost_usd": (res or {}).get("total_cost_usd"),
        "final_text": str((res or {}).get("result", ""))[:400],
    }


def render_report(rows: list[dict], cases: list[dict], skill: str, env: str,
                  samples: int) -> str:
    by_id = {c["id"]: c for c in cases}
    models = sorted({r["model"] for r in rows if r["model"]})
    listed = sorted({r["n_skills_listed"] for r in rows if not r["error"]})
    lines = [
        f"# {skill} natural-trigger probe (live claude -p)", "",
        "- Environment: " + ("family-only (--setting-sources project; only the 9 members "
                             "plus Claude Code's bundled skills)" if env == "family"
                             else "full install (every user skill, plugin and MCP)")
        + "; user hooks disabled; normal tool set",
        f"- Model(s): {', '.join(models) or 'unknown'}; skills listed: "
        f"{', '.join(map(str, listed)) or 'unknown'}",
        f"- Turn 1 only, {samples} sample(s) per case, stopped at the first Skill call",
        f"- Expected skill loaded: {sum(bool(r['hit']) for r in rows)}/"
        f"{sum(not r['error'] for r in rows)} scored samples "
        f"({sum(bool(r['error']) for r in rows)} errored, not scored)",
        f"- Cost (CLI-reported floor; calls stopped at a Skill call report none): "
        f"${sum(float(r['cost_usd'] or 0) for r in rows):.2f}", "",
        "| # | turn 1 | expected loaded | other skill | answered | capped | errored |",
        "|---|---|---|---|---|---|---|",
    ]
    for cid in sorted({r["id"] for r in rows}):
        rs = [r for r in rows if r["id"] == cid]
        scored = [r for r in rs if not r["error"]]
        other = [r["skill"] for r in scored if r["outcome"] == "skill" and not r["hit"]]
        prompt = " ".join(by_id[cid]["turns"][0].split()) if cid in by_id else ""
        prompt = (prompt[:70] + "...") if len(prompt) > 70 else prompt
        lines.append(
            f"| {cid} | {prompt.replace('|', '/')} | {sum(bool(r['hit']) for r in scored)}/"
            f"{len(scored)} | {', '.join(other) or '-'} | "
            f"{sum(r['outcome'] == 'answered' for r in scored)} | "
            f"{sum(r['outcome'] == 'capped' for r in scored)} | "
            f"{len(rs) - len(scored)} |")
    errs = [r for r in rows if r["error"]]
    if errs:
        lines += ["", "## Errored samples", ""]
        lines += [f"- case {r['id']} sample {r['sample']}: {r['error']}" for r in errs]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None, user_skills_dir: Path | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--scenarios", required=True, type=Path)
    ap.add_argument("--out-dir", required=True, type=Path)
    ap.add_argument("--ids", help="only these eval ids, e.g. 2-4 or 1,5")
    ap.add_argument("--samples", type=int, default=3, help="fresh sessions per case")
    ap.add_argument("--family-only", action="store_true",
                    help="load only the 9 git-tracked members (plus bundled skills)")
    ap.add_argument("--expect", help="skill that should load (default: the evals file's skill_name)")
    ap.add_argument("--timeout", type=int, default=600, help="seconds per sample")
    ap.add_argument("--max-budget-usd", type=float, default=1.5, help="per claude call")
    ap.add_argument("--max-turns", type=int, default=6, help="agent turns per claude call")
    ap.add_argument("--env-root", type=Path,
                    help="folder for the env and workspaces (default: a new temp folder, removed after)")
    ap.add_argument("--dry-run", action="store_true",
                    help="print what would run; no claude calls, nothing written")
    args = ap.parse_args(argv)
    if args.samples < 1:
        ap.error("--samples must be at least 1")

    cases = roe.load_cases(args.scenarios)
    if args.ids:
        wanted = roe.parse_ids(args.ids)
        cases = [c for c in cases if c["id"] in wanted]
    if not cases:
        raise SystemExit("no cases selected")
    expected = args.expect or cases[0]["skill"]
    if not expected:
        raise SystemExit("no expected skill: pass --expect or set skill_name in the evals file")
    env = "family" if args.family_only else "full"
    files = family_files() if args.family_only else []

    if args.dry_run:
        print(f"env: {env}; expected skill: {expected}; samples per case: {args.samples}")
        if files:
            counts = {m: sum(f.startswith(m + "/") for f in files) for m in MEMBERS}
            print("family env .claude/skills: " + ", ".join(f"{m} ({n} files)" for m, n in counts.items()))
        print("command: " + " ".join(probe_cmd("claude", args.max_budget_usd, args.max_turns,
                                                args.family_only)))
        for c in cases:
            print(f"case {c['id']} x{args.samples}: fixture {c['fixture']} "
                  f"({', '.join(sorted(c['files']))})")
            print(f"  turn 1: {c['turns'][0]}")
        return 0

    out = args.out_dir.resolve()
    (out / "raw").mkdir(parents=True, exist_ok=True)
    res_path = out / "results.json"
    rows = json.loads(res_path.read_text(encoding="utf-8")) if res_path.exists() else []
    other = {(r["env"], r["expected"]) for r in rows} - {(env, expected)}
    if other:
        raise SystemExit(f"{out} holds a different run {sorted(other)}; use a new --out-dir")
    rows = [r for r in rows if not r["error"]]
    done = {(r["id"], r["sample"]) for r in rows}
    todo = [(c, s) for c in cases for s in range(1, args.samples + 1) if (c["id"], s) not in done]

    user_skills = user_skill_names(user_skills_dir) if args.family_only else set()
    if todo:
        exe = shutil.which("claude")
        if not exe:
            raise SystemExit("claude CLI not found on PATH")
        root = args.env_root.resolve() if args.env_root else Path(tempfile.mkdtemp(prefix="jh-trigger-"))
        try:
            if args.family_only:
                build_family_env(root, files)
            for c, s in todo:
                ws = root / "ws" / f"{c['id']:03d}-s{s}"
                roe.build_workspace(ws, c["files"])
                events = run_turn1(probe_cmd(exe, args.max_budget_usd, args.max_turns, args.family_only),
                                   c["turns"][0], ws, out / "raw" / f"{c['id']:03d}-s{s}.jsonl",
                                   args.timeout)
                r = {"id": c["id"], "sample": s, "env": env, "expected": expected,
                     **classify(events, expected, args.family_only, user_skills)}
                rows.append(r)
                res_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
                print(json.dumps({k: r[k] for k in ("id", "sample", "outcome", "skill",
                                                   "n_skills_listed", "cost_usd", "error")}),
                      flush=True)
        finally:
            if not args.env_root:
                shutil.rmtree(root, ignore_errors=True)

    selected = {c["id"] for c in cases}
    shown = sorted((r for r in rows if r["id"] in selected and r["sample"] <= args.samples),
                   key=lambda r: (r["id"], r["sample"]))
    skill = json.loads(args.scenarios.read_text(encoding="utf-8")).get("skill", expected)
    report = render_report(shown, cases, skill, env, args.samples)
    (out / "report.md").write_text(report, encoding="utf-8")
    print(report)
    n_err = sum(bool(r["error"]) for r in shown)
    if n_err:
        print(f"ERROR: {n_err}/{len(shown)} samples errored; rerun the same --out-dir to retry them",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
