"""Tests for scripts/expand_role_synonyms.py

Signal (2026-10-21, a construction project manager's live search, Benton Harbor MI, $120k+):
"project manager" expanded to "PMP" (a certification, so the queries searched for the
credential) and "PgM" (an abbreviation postings rarely use), and there was no entry for
construction project-management titles at all.
"""
import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "expand_role_synonyms.py"


def _load():
    spec = importlib.util.spec_from_file_location("job_search_expand_role_synonyms", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


ers = _load()

# Certifications, licenses and credentials that are NOT job titles. A synonym is turned
# into a search query, so a credential here searches for the credential instead of the
# job. Deliberately NOT listed: RN, LPN, LVN, NP, APRN, FNP, PA, PT. Those are licenses
# too, but postings use them as the job title itself ("RN - Med Surg", "LPN").
NON_TITLE_CERTIFICATIONS = {
    "pmp", "capm", "pgmp", "pe", "cpa", "cfa", "cissp", "phr", "shrm-cp", "shrm-scp",
    "leed ap",
}


def test_no_synonym_or_adjacent_list_contains_a_certification():
    offenders = []
    for table_name, table in (("SYNONYMS", ers.SYNONYMS), ("ADJACENT", ers.ADJACENT)):
        for key, terms in table.items():
            for term in [key] + list(terms):
                if term.strip().lower() in NON_TITLE_CERTIFICATIONS:
                    offenders.append(f"{table_name}[{key!r}]: {term}")
    assert not offenders, offenders


def test_project_manager_synonyms_are_titles_only():
    syns = ers.expand("project manager")["synonyms"]
    assert "PMP" not in syns
    assert "PgM" not in syns
    assert "program manager" in syns


def test_construction_project_manager_has_construction_titles():
    result = ers.expand("construction project manager")
    assert result["canonical"] == "construction project manager"
    syns = [s.lower() for s in result["synonyms"]]
    for title in ("construction manager", "senior construction project manager",
                  "project executive", "owner's representative"):
        assert title in syns, title


def test_construction_manager_has_construction_titles():
    result = ers.expand("construction manager")
    assert result["canonical"] == "construction manager"
    syns = [s.lower() for s in result["synonyms"]]
    assert "construction project manager" in syns
    assert "senior construction manager" in syns


def test_construction_project_manager_adjacent_roles():
    adjacent = [s.lower() for s in
                ers.expand("construction project manager", include_adjacent=True)["adjacent"]]
    assert "construction superintendent" in adjacent
    assert "estimator" in adjacent
    assert "construction project manager" not in adjacent


@pytest.mark.parametrize("spelling", [
    "Construction Project Manager",
    "  construction   project manager ",
    "CONSTRUCTION PROJECT MANAGER",
])
def test_key_lookup_normalizes_case_and_spaces(spelling):
    assert ers.expand(spelling)["canonical"] == "construction project manager"


@pytest.mark.parametrize("spelling", [
    "Owner's Representative",
    "owners representative",
    "Owner\u2019s Representative",  # typographic apostrophe, as pasted from a posting
])
def test_reverse_lookup_handles_apostrophe_variants(spelling):
    result = ers.expand(spelling)
    assert result["canonical"] == "construction project manager"
    syns = [s.lower() for s in result["synonyms"]]
    assert "construction project manager" in syns
    assert "owner's representative" not in syns  # the input itself is not repeated


def test_unknown_role_still_returns_no_synonyms():
    result = ers.expand("chief vibes officer")
    assert result["synonyms"] == []
    assert result["all_search_terms"] == ["chief vibes officer"]
