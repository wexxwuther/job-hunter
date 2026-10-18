"""Unit tests for the natural-trigger probe (no live calls; replays stream fixtures)."""
import importlib.util
import io
import json
import shutil
import subprocess
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location(
    "run_trigger_probe", Path(__file__).with_name("run_trigger_probe.py"))
probe = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(probe)

REPO = Path(__file__).resolve().parent.parent
FIXTURES = Path(__file__).with_name("trigger-fixtures")
IP_SCENARIOS = REPO / "tools" / "outcome-scenarios" / "interview-prep.json"
_REAL_POPEN = subprocess.Popen


def _lines(name):
    return (FIXTURES / name).read_text(encoding="utf-8").splitlines(keepends=True)


def _events(name):
    return [json.loads(x) for x in _lines(name)]


class _FakeProc:
    pid = 0

    def __init__(self, lines):
        self.stdin = io.StringIO()
        self.consumed = []

        def gen():
            for line in lines:
                self.consumed.append(line)
                yield line
        self.stdout = gen()

    def poll(self):
        return 0


def _fake_claude(monkeypatch, streams):
    """streams: list of line lists, one per call (the last repeats)."""
    calls = []
    monkeypatch.setattr(probe.shutil, "which", lambda name: "claude")

    def popen(cmd, **kw):
        if cmd[0] == "git":  # family_files() runs the real git
            return _REAL_POPEN(cmd, **kw)
        proc = _FakeProc(streams[min(len(calls), len(streams) - 1)])
        calls.append({"cmd": cmd, "cwd": Path(kw["cwd"]), "proc": proc})
        return proc
    monkeypatch.setattr(probe.subprocess, "Popen", popen)
    return calls


def _run(tmp_path, *extra, user_skills_dir=None):
    out = tmp_path / "out"
    rc = probe.main(["--scenarios", str(IP_SCENARIOS), "--out-dir", str(out),
                     "--env-root", str(tmp_path / "env"), *extra],
                    user_skills_dir=user_skills_dir or tmp_path / "no-user-skills")
    rows = json.loads((out / "results.json").read_text(encoding="utf-8"))
    return rc, rows, (out / "report.md").read_text(encoding="utf-8")


# --- replaying fixtures --------------------------------------------------------

def test_skill_hit_stops_reading_at_the_first_skill_call(tmp_path, monkeypatch):
    calls = _fake_claude(monkeypatch, [_lines("skill-hit.jsonl")])
    rc, rows, report = _run(tmp_path, "--ids", "3", "--samples", "2")
    assert rc == 0
    assert len(calls) == 2, "one fresh session per sample"
    assert [r["sample"] for r in rows] == [1, 2]
    r = rows[0]
    assert (r["outcome"], r["skill"], r["hit"], r["error"]) == ("skill", "interview-prep", True, None)
    assert r["tools_before"] == ["Read"]
    assert r["cost_usd"] is None, "a call stopped at the Skill call reports no cost"
    assert r["n_skills_listed"] == 21
    consumed = "".join(calls[0]["proc"].consumed)
    assert "AFTER-SKILL" not in consumed, "the stream must not be read past the routing decision"
    raw = (tmp_path / "out" / "raw" / "003-s1.jsonl").read_text(encoding="utf-8")
    assert "toolu_2" in raw and "AFTER-SKILL" not in raw
    row = next(ln for ln in report.splitlines() if ln.startswith("| 3 |"))
    assert row.startswith("| 3 | Research Globex before my interview. Here is the posting: Senior")
    assert row.endswith("| 2/2 | - | 0 | 0 | 0 |"), "a multi-line prompt must not break the table"


def test_direct_answer_is_a_scored_miss_with_its_cost(tmp_path, monkeypatch):
    _fake_claude(monkeypatch, [_lines("direct-answer.jsonl")])
    rc, rows, report = _run(tmp_path, "--ids", "3", "--samples", "1")
    assert rc == 0, "a miss is a result, not a runner error"
    r = rows[0]
    assert (r["outcome"], r["skill"], r["hit"], r["error"]) == ("answered", None, False, None)
    assert r["tools_before"] == ["WebSearch"]
    assert r["cost_usd"] == pytest.approx(0.31)
    assert r["final_text"].startswith("Here is a quick briefing")
    assert "| 0/1 | - | 1 | 0 | 0 |" in report


def test_errored_sample_is_not_scored_fails_the_run_and_is_retried(tmp_path, monkeypatch):
    calls = _fake_claude(monkeypatch, [_lines("skill-hit.jsonl"), _lines("errored.jsonl"),
                                       _lines("skill-hit.jsonl")])
    rc, rows, report = _run(tmp_path, "--ids", "3", "--samples", "2")
    assert rc == 1
    assert rows[1]["error"] == "Not logged in - Please run /login"
    assert rows[1]["hit"] is None and rows[1]["outcome"] is None
    assert "| 1/1 |" in report, "errored samples are not in the denominator"
    assert "sample 2: Not logged in" in report
    rc, rows, report = _run(tmp_path, "--ids", "3", "--samples", "2")
    assert rc == 0
    assert len(calls) == 3, "only the errored sample is re-spent"
    assert [(r["sample"], r["hit"]) for r in rows] == [(1, True), (2, True)]


# --- classification edge cases ---------------------------------------------------

def test_max_turns_without_a_skill_call_is_a_capped_miss():
    events = _events("direct-answer.jsonl")[:-2] + [
        {"type": "result", "subtype": "error_max_turns", "is_error": True, "total_cost_usd": 1.2}]
    r = probe.classify(events, "interview-prep", family=True)
    assert (r["outcome"], r["hit"], r["error"]) == ("capped", False, None)


def test_a_different_skill_is_a_miss_that_names_the_skill():
    events = [json.loads(json.dumps(e).replace('"skill": "interview-prep"', '"skill": "job-hunter"'))
              for e in _events("skill-hit.jsonl")]
    r = probe.classify(events, "interview-prep", family=False)
    assert (r["outcome"], r["skill"], r["hit"]) == ("skill", "job-hunter", False)


def test_killed_without_a_result_or_skill_call_is_errored():
    r = probe.classify(_events("direct-answer.jsonl")[:3], "interview-prep", family=False)
    assert r["error"].startswith("no result event") and r["hit"] is None


def test_no_init_event_is_errored():
    r = probe.classify([], "interview-prep", family=False)
    assert r["error"].startswith("no init event")


def test_expected_skill_missing_from_the_listing_is_errored_not_a_miss():
    events = _events("direct-answer.jsonl")
    events[0]["skills"] = [s for s in events[0]["skills"] if s != "interview-prep"]
    r = probe.classify(events, "interview-prep", family=False)
    assert r["hit"] is None and "not in the session's skill listing" in r["error"]


def test_family_only_rejects_leaked_user_skills_and_plugins():
    events = _events("skill-hit.jsonl")
    events[0]["skills"] = events[0]["skills"] + ["my-private-skill"]
    r = probe.classify(events, "interview-prep", family=True, user_skills={"my-private-skill", "job-hunter"})
    assert r["hit"] is None and "my-private-skill" in r["error"]
    assert probe.classify(events, "interview-prep", family=False,
                          user_skills={"my-private-skill"})["hit"] is True, "full env expects user skills"
    events = _events("skill-hit.jsonl")
    events[0]["plugins"] = [{"name": "some-plugin"}]
    assert "some-plugin" in probe.classify(events, "interview-prep", family=True)["error"]
    member_named = probe.classify(_events("skill-hit.jsonl"), "interview-prep", family=True,
                                  user_skills={"job-hunter"})
    assert member_named["hit"] is True, "a user install of a member is not a leak"


# --- environments ----------------------------------------------------------------

def test_family_only_runs_in_a_project_env_with_exactly_the_tracked_members(tmp_path, monkeypatch):
    calls = _fake_claude(monkeypatch, [_lines("skill-hit.jsonl")])
    user = tmp_path / "user-skills"
    (user / "my-private-skill").mkdir(parents=True)
    rc, rows, report = _run(tmp_path, "--ids", "2", "--samples", "1", "--family-only",
                            user_skills_dir=user)
    assert rc == 0 and rows[0]["env"] == "family"
    cmd = calls[0]["cmd"]
    assert cmd[cmd.index("--setting-sources") + 1] == "project"
    assert '{"disableAllHooks": true}' in cmd
    assert cmd[cmd.index("--max-turns") + 1] == "6"
    skills = tmp_path / "env" / ".claude" / "skills"
    assert calls[0]["cwd"].is_relative_to(tmp_path / "env"), "cwd must be under the env folder"
    assert sorted(p.name for p in skills.iterdir()) == sorted(probe.MEMBERS)
    assert not list(skills.glob("*/tests")), "member tests are not part of an install"
    tracked = probe.family_files()
    copied = sorted(p.relative_to(skills).as_posix() for p in skills.rglob("*") if p.is_file())
    assert copied == sorted(tracked)
    ip = "interview-prep/SKILL.md"
    assert (skills / ip).read_bytes() == (REPO / ip).read_bytes()
    assert (calls[0]["cwd"] / "posting.txt").exists(), "fixture workspace is the cwd"
    assert "family-only" in report


def test_full_env_has_no_setting_sources_and_temp_env_is_removed(tmp_path, monkeypatch):
    calls = _fake_claude(monkeypatch, [_lines("direct-answer.jsonl")])
    out = tmp_path / "out"
    assert probe.main(["--scenarios", str(IP_SCENARIOS), "--out-dir", str(out),
                       "--ids", "1", "--samples", "1"]) == 0
    assert "--setting-sources" not in calls[0]["cmd"]
    assert not calls[0]["cwd"].exists(), "the default temp env is cleaned up"


def test_family_files_uses_git_tracked_files_without_tests(tmp_path):
    if not shutil.which("git"):
        pytest.skip("git not on PATH")
    repo = tmp_path / "repo"
    for m in probe.MEMBERS:
        (repo / m / "tests").mkdir(parents=True)
        (repo / m / "SKILL.md").write_text("---\nname: x\n---\n", encoding="utf-8")
        (repo / m / "tests" / "test_x.py").write_text("", encoding="utf-8")
    (repo / "tools").mkdir()
    (repo / "tools" / "x.py").write_text("", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    (repo / "interview-prep" / "scratch.md").write_text("untracked", encoding="utf-8")
    files = probe.family_files(repo)
    assert sorted(files) == sorted(f"{m}/SKILL.md" for m in probe.MEMBERS)
    (repo / "cover-letter" / "SKILL.md").unlink()
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    with pytest.raises(SystemExit, match="cover-letter"):
        probe.family_files(repo)


def test_out_dir_from_a_different_env_is_refused(tmp_path, monkeypatch):
    _fake_claude(monkeypatch, [_lines("direct-answer.jsonl")])
    _run(tmp_path, "--ids", "1", "--samples", "1")
    with pytest.raises(SystemExit, match="different run"):
        _run(tmp_path, "--ids", "1", "--samples", "1", "--family-only")


# --- dry run ---------------------------------------------------------------------

def test_dry_run_interview_prep_cases_2_to_4_family_only(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(probe.subprocess, "Popen", lambda cmd, **k: _REAL_POPEN(cmd, **k)
                        if cmd[0] == "git" else pytest.fail("no claude call"))
    out = tmp_path / "out"
    assert probe.main(["--scenarios", str(IP_SCENARIOS), "--out-dir", str(out), "--ids", "2-4",
                       "--samples", "3", "--family-only", "--dry-run"]) == 0
    printed = capsys.readouterr().out
    assert not out.exists(), "a dry run writes nothing"
    assert "env: family; expected skill: interview-prep; samples per case: 3" in printed
    assert "--setting-sources project" in printed
    for m in probe.MEMBERS:
        assert f"{m} (" in printed
    turn1 = {c["id"]: c["turns"][0] for c in probe.roe.load_cases(IP_SCENARIOS)}
    assert [ln.split()[1] for ln in printed.splitlines() if ln.startswith("case ")] == ["2", "3", "4"]
    for cid in (2, 3, 4):
        assert f"  turn 1: {turn1[cid]}" in printed
    assert f"turn 1: {turn1[1]}" not in printed
