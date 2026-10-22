"""Tests for scripts/build_search_queries.py Tier 2 industry boards.

Signal (2026-10-21, a construction project manager's live search): --industry construction
was not a recognized industry, so Tier 2 fell back to one generic "job board" query and no
construction board was searched.
"""
import importlib.util
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
SCRIPT = SKILL / "scripts" / "build_search_queries.py"
REFERENCE = SKILL / "references" / "niche-boards-by-industry.md"


def _load():
    spec = importlib.util.spec_from_file_location("job_search_build_search_queries", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod  # @dataclass resolves its module through sys.modules
    spec.loader.exec_module(mod)
    return mod


bsq = _load()

CONSTRUCTION_DOMAINS = ("constructionjobs.com", "ihireconstruction.com", "careers.agc.org",
                        "careerhq.cmaanet.org")


def test_construction_industry_produces_construction_board_queries():
    qs = bsq.build_queries("construction project manager", "Benton Harbor, MI",
                           industry="construction")
    for domain in CONSTRUCTION_DOMAINS:
        assert any(q.startswith(f"site:{domain} ") for q in qs.tier_2), domain
    assert not any("job board" in q for q in qs.tier_2), qs.tier_2


def test_construction_industry_is_case_insensitive():
    qs = bsq.build_queries("construction manager", "Benton Harbor, MI", industry="Construction")
    assert any(q.startswith("site:constructionjobs.com ") for q in qs.tier_2)


def test_construction_board_queries_carry_role_and_location():
    qs = bsq.build_queries("construction project manager", "Benton Harbor, MI",
                           industry="construction")
    for q in qs.tier_2:
        assert '"construction project manager"' in q
        assert '"Benton Harbor, MI"' in q


def test_unknown_industry_still_falls_back_to_generic_query():
    qs = bsq.build_queries("beekeeper", "Benton Harbor, MI", industry="apiculture")
    assert qs.tier_2 == ['apiculture job board beekeeper "Benton Harbor, MI"']


def test_cli_help_lists_construction(capsys):
    try:
        bsq.main(["--help"])
    except SystemExit:
        pass
    assert "construction" in capsys.readouterr().out


def test_reference_table_lists_the_construction_boards():
    text = REFERENCE.read_text(encoding="utf-8")
    assert "## Construction" in text
    section = text.split("## Construction", 1)[1].split("\n## ", 1)[0]
    for domain in CONSTRUCTION_DOMAINS:
        assert domain in section.lower(), domain
