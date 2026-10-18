"""Unit tests for the routing-eval parser and scorer (no live calls)."""
import importlib.util
import json
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "run_routing_evals", Path(__file__).with_name("run_routing_evals.py"))
rre = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rre)


def _assistant(*tool_uses):
    return {"type": "assistant", "message": {"content": [
        {"type": "tool_use", "name": n, "input": i} for n, i in tool_uses]}}


def test_skill_tool_call_is_the_routing_signal():
    events = [_assistant(("Skill", {"skill": "job-search", "args": "x"}))]
    assert rre.routed_skill(events) == ("job-search", ["job-search"])


def test_read_of_skill_md_counts_and_first_wins():
    events = [_assistant(("Read", {"file_path": "C:/Users/x/.agents/skills/job-search/SKILL.md"})),
              _assistant(("Skill", {"skill": "resume-tailor"}))]
    assert rre.routed_skill(events) == ("job-search", ["job-search", "resume-tailor"])


def test_namespaced_skill_name_is_normalized():
    events = [_assistant(("Skill", {"skill": "job-hunter:cover-letter"}))]
    assert rre.routed_skill(events)[0] == "cover-letter"


def test_non_skill_reads_and_text_are_ignored():
    events = [_assistant(("Read", {"file_path": "C:/notes/README.md"})),
              {"type": "assistant", "message": {"content": [{"type": "text", "text": "SKILL_USED: job-search"}]}}]
    assert rre.routed_skill(events) == (None, [])


def test_scoring_positive_strict_and_lenient():
    case = {"expected": ["job-search"], "allow_none": False}
    assert rre.score(case, "job-search") == {"strict": True, "lenient": True}
    assert rre.score(case, "job-hunter") == {"strict": False, "lenient": True}
    assert rre.score(case, "resume-tailor") == {"strict": False, "lenient": False}
    assert rre.score(case, None) == {"strict": False, "lenient": False}


def test_scoring_off_domain_allows_non_family_skills_only():
    case = {"expected": [], "allow_none": True}
    assert rre.score(case, None)["strict"]
    assert rre.score(case, "code-review")["strict"]
    assert not rre.score(case, "job-hunter")["lenient"]


def test_scoring_member_or_none():
    case = {"expected": ["resume-tailor"], "allow_none": True}
    assert rre.score(case, "resume-tailor")["strict"]
    assert rre.score(case, None)["strict"]
    assert not rre.score(case, "career-profile")["lenient"]


def test_cases_dedupe_and_labels_apply():
    cases = rre.load_cases()
    queries = [c["query"] for c in cases]
    assert len(queries) == len(set(queries))
    by_q = {c["query"]: c for c in cases}
    # a negative in other members is NOT "no family skill": labelled owner wins
    assert by_q["Tailor my resume for this product manager role at Stripe"]["expected"] == ["resume-tailor"]
    assert by_q["Find me senior backend engineer roles in Seattle, $180k+"]["expected"] == ["job-search"]
    # stale resume-tailor#7 claim is overridden: cover letters belong to cover-letter
    assert by_q["Write me a cover letter for the Anthropic research engineer position"]["expected"] == ["cover-letter"]


def test_parse_ids_ranges():
    assert rre.parse_ids("7,8,13-15") == {7, 8, 13, 14, 15}
    assert rre.parse_ids(" 3 ,") == {3}


def test_unclaimed_query_without_label_is_rejected(tmp_path):
    import json, shutil
    for m in rre.MEMBERS:
        (tmp_path / m / "evals").mkdir(parents=True)
        shutil.copy(rre.REPO / m / "evals" / "trigger-evals.json", tmp_path / m / "evals")
    p = tmp_path / "job-search" / "evals" / "trigger-evals.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    data.append({"id": 99, "query": "Brand new unlabeled negative", "should_trigger": False})
    p.write_text(json.dumps(data), encoding="utf-8")
    try:
        rre.load_cases(tmp_path)
    except ValueError as exc:
        assert "Brand new unlabeled negative" in str(exc)
    else:
        raise AssertionError("unlabeled unclaimed query was accepted")


# Real tail of a `claude -p` stream when the CLI is not logged in (2026-10-18).
# Note subtype "success" with is_error true: the subtype alone does not flag it.
_NOT_LOGGED_IN = "Not logged in \u00b7 Please run /login"
_NOT_LOGGED_IN_STREAM = [
    {"type": "system", "subtype": "init", "model": "claude-opus-5-5"},
    {"type": "assistant", "error": "authentication_failed", "message": {
        "model": "<synthetic>", "content": [{"type": "text", "text": _NOT_LOGGED_IN}]}},
    {"type": "result", "subtype": "success", "is_error": True, "num_turns": 1,
     "result": _NOT_LOGGED_IN, "total_cost_usd": 0},
]


class _FakeProc:
    """Stands in for the claude CLI process: replays a fixed stream."""
    pid = 0

    def __init__(self, events):
        import io
        self.stdin = io.StringIO()
        self.stdout = iter(json.dumps(e) + "\n" for e in events)

    def poll(self):
        return 0


def _fake_claude(monkeypatch, events):
    calls = []
    monkeypatch.setattr(rre.shutil, "which", lambda name: "claude")

    def popen(cmd, **kw):
        calls.append(cmd)
        return _FakeProc(events)
    monkeypatch.setattr(rre.subprocess, "Popen", popen)
    return calls


def test_not_logged_in_result_is_errored_not_scored(tmp_path, monkeypatch, capsys):
    _fake_claude(monkeypatch, _NOT_LOGGED_IN_STREAM)
    # case 1 is a positive (expected non-empty); old code scored it "routed (none)"
    rc = rre.main(["--out-dir", str(tmp_path), "--ids", "1", "--workers", "1"])
    assert rc != 0, "an errored CLI call must fail the run"
    row = json.loads((tmp_path / "results.json").read_text(encoding="utf-8"))[0]
    assert row["errored"] is True
    assert row["error"] == _NOT_LOGGED_IN
    report = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert "Positive strict: 0/0" in report
    assert "Negative (no family skill): 0/0" in report
    assert "## Errored" in report and "Not logged in" in report
    misses = report.split("## Misses", 1)[1].split("##", 1)[0]
    assert "| 1 |" not in misses, "errored case must not be listed as a routing miss"


def test_errored_raw_is_retried_on_resume(tmp_path, monkeypatch):
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "001.jsonl").write_text(
        "".join(json.dumps(e) + "\n" for e in _NOT_LOGGED_IN_STREAM), encoding="utf-8")
    ok = [{"type": "system", "subtype": "init", "model": "m"},
          _assistant(("Skill", {"skill": "job-search"}))]
    calls = _fake_claude(monkeypatch, ok)
    rc = rre.main(["--out-dir", str(tmp_path), "--ids", "1", "--workers", "1"])
    assert len(calls) == 1, "an errored raw result must be re-run, not reused"
    row = json.loads((tmp_path / "results.json").read_text(encoding="utf-8"))[0]
    assert row["errored"] is False and row["routed"] == "job-search"
    assert rc == 0
