"""Offline guards for the state workforce portal registry (no network).

The 2026-10-13 link check found 13 of 51 portals dead, failing, or hijacked
(employgeorgia.com had become an online-poker site), and the same dead domains were
hardcoded in job-search/scripts/build_search_queries.py. These tests keep the table
well-formed, keep the script in sync with it, and stop retired domains from returning.
"""
import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod  # @dataclass resolves its module through sys.modules
    spec.loader.exec_module(mod)
    return mod


checker = _load("check_state_portals", REPO / "tools" / "check_state_portals.py")
queries = _load("build_search_queries", REPO / "job-search" / "scripts" / "build_search_queries.py")

ABBR = {"tx": "Texas", "ca": "California", "ny": "New York", "fl": "Florida", "il": "Illinois",
        "wa": "Washington", "ma": "Massachusetts", "pa": "Pennsylvania", "ga": "Georgia",
        "co": "Colorado", "az": "Arizona", "or": "Oregon", "mi": "Michigan",
        "nc": "North Carolina", "va": "Virginia"}

# Verified dead (no DNS), failing, or no longer the state's portal on 2026-10-13.
RETIRED = {"joblink.alabama.gov", "employgeorgia.com", "kentuckycareercenter.com",
           "hirelouisiana.com", "masshirecjc.com", "jobs.mt.gov", "jobs.nj.gov",
           "jobzone.ny.gov", "okjobmatch.com", "oregonjobsplus.com", "jobgateway.pa.gov"}


def test_table_has_all_50_states_plus_dc_once():
    states = [s for s, _, _ in checker.load_rows()]
    assert len(states) == 51
    assert len(set(states)) == 51
    assert "DC" in states


def test_every_row_parses_as_a_bare_host():
    """The checker's row regex must see every row (a URL path or scheme would hide it)."""
    text = checker.REF.read_text(encoding="utf-8")
    table_rows = [l for l in text.splitlines()
                  if l.startswith("| ") and not l.startswith(("| State", "|---"))]
    assert len(table_rows) == len(checker.load_rows())


def test_retired_domains_do_not_come_back():
    hosts = {h for _, h, _ in checker.load_rows()} | set(queries.STATE_PORTALS.values())
    assert not hosts & RETIRED, hosts & RETIRED


def test_script_portals_match_the_reference_table():
    table = {s: h for s, h, _ in checker.load_rows()}
    for abbr, host in queries.STATE_PORTALS.items():
        assert table[ABBR[abbr]] == host, f"{abbr}: script {host} != table {table[ABBR[abbr]]}"
