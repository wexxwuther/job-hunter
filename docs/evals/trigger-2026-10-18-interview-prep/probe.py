"""Trigger-only probe: does turn 1 of an outcome case load the skill, with the normal tool set?

Reuses the repo runner's case loading, workspace build and tool allow-list. Each sample is a
fresh workspace + session; the process is killed at the first Skill tool call (the routing
decision is made), otherwise it runs to its result (capped by --max-turns / budget).

envs:
  full   = this machine's full install (all user skills/plugins/MCP), hooks disabled
  family = --setting-sources project, cwd under famenv/ (whose .claude/skills holds only the
           8 job-hunter members), so only those + Claude Code's bundled skills load

usage: python probe.py --env family --ids 2-4 --samples 3 --out out-family
"""
import argparse, json, shutil, subprocess, sys, threading, uuid
from pathlib import Path

REPO = Path(r"E:\Git\job-hunter-public")
sys.path.insert(0, str(REPO / "tools"))
import run_outcome_evals as roe  # noqa: E402

HERE = Path(__file__).resolve().parent
SCEN = REPO / "tools" / "outcome-scenarios" / "interview-prep.json"


def run_sample(case, env, ws, raw, max_turns, budget, timeout):
    roe.build_workspace(ws, case["files"])
    exe = shutil.which("claude")
    cmd = [exe, "-p", "--output-format", "stream-json", "--verbose",
           "--max-turns", str(max_turns), "--max-budget-usd", str(budget),
           "--settings", roe.NO_HOOKS, "--allowedTools", *roe.ALLOWED_TOOLS,
           "--disallowedTools", *roe.DISALLOWED_TOOLS, "--session-id", str(uuid.uuid4())]
    if env in ("family", "draft"):
        cmd += ["--setting-sources", "project"]
    proc = subprocess.Popen(cmd, cwd=str(ws), text=True, encoding="utf-8", errors="replace",
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    proc.stdin.write(case["turns"][0])
    proc.stdin.close()
    timer = threading.Timer(timeout, roe._kill_tree, args=(proc,))
    timer.start()
    lines, skill, stopped = [], None, False
    try:
        for line in proc.stdout:
            lines.append(line)
            evs = roe.parse_stream(line)
            calls = roe.tool_calls(evs)
            sk = next((c["input"].get("skill") for c in calls if c["name"] == "Skill"), None)
            if sk:
                skill, stopped = str(sk), True
                break
    finally:
        timer.cancel()
        roe._kill_tree(proc)
        raw.write_text("".join(lines), encoding="utf-8")
    events = roe.parse_stream("".join(lines))
    init = next((e for e in events if e.get("subtype") == "init"), {})
    res = roe.result_event(events) or {}
    calls = roe.tool_calls(events)
    return {"skill": skill, "stopped_at_skill": stopped,
            "tools_before": [c["name"] for c in calls if c["name"] != "Skill"],
            "n_skills_loaded": len(init.get("skills") or []),
            "ip_in_listing": "interview-prep" in (init.get("skills") or []),
            "model": init.get("model"),
            "error": roe.result_error(events) if res else (None if stopped else "no result event"),
            "cost_usd": res.get("total_cost_usd"),
            "final_text": str(res.get("result", ""))[:400]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", choices=["full", "family", "draft"], required=True)
    ap.add_argument("--ids", required=True)
    ap.add_argument("--samples", type=int, default=3)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-turns", type=int, default=6)
    ap.add_argument("--budget", type=float, default=1.5)
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--scenarios", default=str(SCEN))
    a = ap.parse_args()
    wanted = roe.parse_ids(a.ids)
    cases = [c for c in roe.load_cases(Path(a.scenarios)) if c["id"] in wanted]
    out = (HERE / a.out).resolve()
    (out / "raw").mkdir(parents=True, exist_ok=True)
    ws_root = {"family": HERE / "famenv" / "ws", "draft": HERE / "famenv-draft" / "ws", "full": HERE / "fullenv" / "ws"}[a.env]
    res_path = out / "results.json"
    rows = json.loads(res_path.read_text(encoding="utf-8")) if res_path.exists() else []
    done = {(r["id"], r["sample"]) for r in rows if not r.get("error")}
    rows = [r for r in rows if (r["id"], r["sample"]) in done]
    for c in cases:
        for s in range(1, a.samples + 1):
            if (c["id"], s) in done:
                continue
            tag = f"{a.out}-{c['id']:03d}-s{s}"
            r = run_sample(c, a.env, ws_root / tag, out / "raw" / f"{c['id']:03d}-s{s}.jsonl",
                           a.max_turns, a.budget, a.timeout)
            r.update({"id": c["id"], "sample": s, "env": a.env})
            rows.append(r)
            res_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
            print(json.dumps({k: r[k] for k in ("id", "sample", "skill", "tools_before",
                                               "n_skills_loaded", "cost_usd", "error")}), flush=True)
    hits = {}
    for r in rows:
        hits.setdefault(r["id"], []).append(r["skill"] == "interview-prep")
    for i, h in sorted(hits.items()):
        print(f"case {i}: interview-prep loaded {sum(h)}/{len(h)}")


if __name__ == "__main__":
    main()
