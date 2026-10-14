#!/usr/bin/env python3
"""Re-check every state workforce portal in job-search/references/state-workforce-commissions.md.

Network check (not run in CI). For each portal: HTTP status, final URL after redirects, and
<title>, so a lapsed/parked/hijacked domain is visible, not only a 404. Many state portals
block scripts (403, connection reset, bot-check pages); confirm those in a real browser before
calling them dead, and confirm any replacement against the agency's own .gov page.

Usage: python tools/check_state_portals.py [--json out.json]
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import re
import socket
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path

REF = Path(__file__).resolve().parent.parent / "job-search" / "references" / "state-workforce-commissions.md"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/130.0 Safari/537.36")
ROW = re.compile(r"^\| ([A-Za-z ]+) \| ([a-z0-9.\-]+\.[a-z]+) \| (.+?) \|$")


def load_rows(ref: Path = REF) -> list[tuple[str, str, str]]:
    return [m.groups() for line in ref.read_text(encoding="utf-8").splitlines()
            if (m := ROW.match(line))]


def check(state: str, host: str, agency: str) -> dict:
    out = {"state": state, "host": host, "agency": agency}
    req = urllib.request.Request(f"https://{host}",
                                 headers={"User-Agent": UA, "Accept": "text/html,*/*"})
    try:
        with urllib.request.urlopen(req, timeout=25, context=ssl.create_default_context()) as r:
            body = r.read(200_000).decode("utf-8", errors="replace")
            t = re.search(r"<title[^>]*>(.*?)</title>", body, re.I | re.S)
            out.update(status=r.status, final_url=r.geturl(),
                       title=" ".join(t.group(1).split())[:100] if t else "")
    except urllib.error.HTTPError as e:
        out.update(status=e.code, final_url=e.geturl(), title="")
    except (urllib.error.URLError, socket.timeout, ssl.SSLError, OSError) as e:
        reason = getattr(e, "reason", e)
        out.update(status=None, error=f"{type(reason).__name__}: {reason}"[:150])
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--json", type=Path, help="write raw results here")
    args = ap.parse_args(argv)
    rows = load_rows()
    with cf.ThreadPoolExecutor(max_workers=12) as pool:
        results = list(pool.map(lambda r: check(*r), rows))
    if args.json:
        args.json.write_text(json.dumps(results, indent=2), encoding="utf-8")
    problems = 0
    for r in results:
        ok = r.get("status") == 200
        problems += not ok
        moved = "" if r["host"] in (r.get("final_url") or "") else f" -> {r.get('final_url')}"
        line = (f"{'ok ' if ok else 'CHECK'} {r['state']:15s} {r.get('status') or 'ERR'!s:4s} "
                f"{r['host']}{moved} | {r.get('title') or r.get('error', '')}")
        print(line.encode("ascii", "replace").decode())
    print(f"\n{len(results)} portals, {problems} need a closer look (403/timeouts are often bot-blocking)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
