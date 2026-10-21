"""Offline guards for the Claude Code plugin manifests (no network, no claude CLI).

`/plugin marketplace add wexxwuther/job-hunter` clones the repo and reads
`.claude-plugin/marketplace.json` at the REPO ROOT. Until 2026-10-21 that file only existed
under `plugin/`, and the plugin's `skills/` tree there is generated and gitignored, so the
documented GitHub install failed with "Marketplace file not found". The root manifest now
lists the 8 member dirs directly. These tests keep it complete and in step with the
`plugin/` manifest that `build_plugin.py` packages into the plugin zip.
"""
import importlib.util
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ROOT_PLUGIN = REPO / ".claude-plugin" / "plugin.json"
ROOT_MARKET = REPO / ".claude-plugin" / "marketplace.json"
ZIP_PLUGIN = REPO / "plugin" / "job-hunter" / ".claude-plugin" / "plugin.json"
ZIP_MARKET = REPO / "plugin" / ".claude-plugin" / "marketplace.json"


def _json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _members():
    spec = importlib.util.spec_from_file_location("build_plugin", REPO / "build_plugin.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.MEMBERS


def test_root_marketplace_exists_for_github_install():
    assert ROOT_MARKET.is_file(), "GitHub marketplace add reads .claude-plugin/marketplace.json"
    assert ROOT_PLUGIN.is_file()


def test_root_marketplace_points_at_repo_root_plugin():
    market = _json(ROOT_MARKET)
    assert market["name"] == _json(ZIP_MARKET)["name"]
    [entry] = market["plugins"]
    assert entry["name"] == "job-hunter"
    assert entry["source"] == "./"


def test_root_plugin_lists_every_member_once():
    skills = _json(ROOT_PLUGIN)["skills"]
    assert len(skills) == len(set(skills))
    assert sorted(s.removeprefix("./") for s in skills) == sorted(_members())


def test_every_listed_skill_dir_has_a_skill_md():
    for s in _json(ROOT_PLUGIN)["skills"]:
        assert s.startswith("./")
        assert (REPO / s.removeprefix("./") / "SKILL.md").is_file(), s


def test_every_member_dir_in_repo_is_listed():
    on_disk = {p.parent.name for p in REPO.glob("*/SKILL.md")}
    listed = {s.removeprefix("./") for s in _json(ROOT_PLUGIN)["skills"]}
    assert on_disk == listed


def test_root_and_zip_manifests_agree_on_metadata():
    root = _json(ROOT_PLUGIN)
    root.pop("skills")
    assert root == _json(ZIP_PLUGIN)


def test_plugin_version_matches_orchestrator_meta():
    meta = _json(REPO / "job-hunter" / "_meta.json")
    assert _json(ROOT_PLUGIN)["version"] == meta["version"]
