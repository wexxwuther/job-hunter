"""Unit tests for the routing-eval parser and scorer (no live calls)."""
import importlib.util
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
