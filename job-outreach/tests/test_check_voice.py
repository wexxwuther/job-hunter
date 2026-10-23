"""Tests for job-outreach/scripts/check_voice.py.

The engine is person-neutral: every rule comes from a rules file the user owns. These tests use a
small sample rules file written to a temp dir, never a real person's rules."""
import importlib.util
import json
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("check_voice", HERE.parent / "scripts" / "check_voice.py")
cv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cv)

CHANNELS = ["email", "linkedin-note", "cover-letter"]


def rules_file(tmp_path, rules=None, **extra):
    data = {"version": 1, "channels": CHANNELS, "rules": rules or [], **extra}
    p = tmp_path / "rules.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


def rule(**kw):
    base = {"id": "r1", "level": "fail", "type": "phrases", "phrases": ["synergy"], "message": "say it plainly"}
    base.update(kw)
    return base


# ---- unhappy paths first: a broken rules file must never silently pass a draft ----

def test_missing_rules_file_is_an_error(tmp_path):
    with pytest.raises(cv.RulesError, match="not found"):
        cv.load_rules(tmp_path / "nope.json")


def test_invalid_json_is_an_error(tmp_path):
    p = tmp_path / "rules.json"
    p.write_text("{not json", encoding="utf-8")
    with pytest.raises(cv.RulesError, match="not valid JSON"):
        cv.load_rules(p)


def test_wrong_version_is_an_error(tmp_path):
    p = tmp_path / "rules.json"
    p.write_text(json.dumps({"version": 2, "channels": CHANNELS, "rules": []}), encoding="utf-8")
    with pytest.raises(cv.RulesError, match="version"):
        cv.load_rules(p)


@pytest.mark.parametrize("bad, msg", [
    ({"id": ""}, "unique"),
    ({"level": "error"}, "level"),
    ({"type": "magic"}, "type"),
    ({"message": ""}, "message"),
    ({"channels": ["fax"]}, "channel"),
    ({"type": "regex", "phrases": None, "pattern": "("}, "bad pattern"),
    ({"type": "regex", "phrases": None, "pattern": "x", "flags": "q"}, "flag"),
    ({"type": "max_count", "phrases": None, "pattern": "x"}, "integer"),
    ({"levels_by_channel": {"email": "loud"}}, "levels_by_channel"),
])
def test_malformed_rule_is_rejected(tmp_path, bad, msg):
    with pytest.raises(cv.RulesError, match=msg):
        cv.load_rules(rules_file(tmp_path, [rule(**bad)]))


def test_duplicate_rule_ids_are_rejected(tmp_path):
    with pytest.raises(cv.RulesError, match="unique"):
        cv.load_rules(rules_file(tmp_path, [rule(), rule()]))


def test_json_backspace_in_pattern_is_rejected(tmp_path):
    # Writing "\b" (one backslash) in JSON stores a backspace character. The regex compiles but
    # never matches, so the rule would silently do nothing. The loader must refuse it.
    p = tmp_path / "rules.json"
    p.write_text('{"version": 1, "channels": ["email"], "rules": [{"id": "x", "level": "fail", '
                 '"type": "regex", "pattern": "\\bPM\\b", "message": "m"}]}', encoding="utf-8")
    with pytest.raises(cv.RulesError, match="control character"):
        cv.load_rules(p)


def test_unknown_channel_at_check_time_is_an_error(tmp_path):
    rules = cv.load_rules(rules_file(tmp_path, [rule()]))
    with pytest.raises(cv.RulesError, match="channel"):
        cv.check("text", rules, "fax")


def test_bad_limit_is_rejected(tmp_path):
    with pytest.raises(cv.RulesError, match="limit"):
        cv.load_rules(rules_file(tmp_path, [rule()], limits={"linkedin-note": {"max_chars": "300", "level": "fail"}}))


# ---- behavior ----

def test_phrase_matches_whole_words_case_insensitively(tmp_path):
    rules = cv.load_rules(rules_file(tmp_path, [rule()]))
    assert [f["rule"] for f in cv.check("Real SYNERGY here.", rules, "email")] == ["r1"]
    assert cv.check("asynergy is not the word", rules, "email") == []


def test_chars_rule_reports_the_character(tmp_path):
    rules = cv.load_rules(rules_file(tmp_path, [rule(type="chars", chars=["\u2014"], phrases=None)]))
    (f,) = cv.check("thirty years \u2014 and counting", rules, "email")
    assert "EM DASH" in f["match"] and f["line"] == 1


def test_rule_channels_limit_where_it_applies(tmp_path):
    rules = cv.load_rules(rules_file(tmp_path, [rule(channels=["email"])]))
    assert cv.check("synergy", rules, "email")
    assert cv.check("synergy", rules, "cover-letter") == []


def test_levels_by_channel_overrides_level(tmp_path):
    rules = cv.load_rules(rules_file(tmp_path, [rule(level="warn", levels_by_channel={"cover-letter": "fail"})]))
    assert cv.check("synergy", rules, "email")[0]["level"] == "warn"
    assert cv.check("synergy", rules, "cover-letter")[0]["level"] == "fail"


def test_allowlisted_sentence_is_never_flagged(tmp_path):
    approved = "If it looks like a fit, let's have a conversation about synergy."
    rules = cv.load_rules(rules_file(tmp_path, [rule()], allow=[approved]))
    assert cv.check(approved, rules, "email") == []
    assert cv.check(approved + " More synergy.", rules, "email")[0]["match"].lower() == "synergy"


def test_opening_rule_only_looks_at_the_start(tmp_path):
    r = rule(type="opening", phrases=None, pattern=r"\b250\b", within_chars=40)
    rules = cv.load_rules(rules_file(tmp_path, [r]))
    assert cv.check("I ran a crew of 250 for years.", rules, "email")
    assert cv.check("x" * 60 + " a crew of 250", rules, "email") == []


def test_max_count_rule(tmp_path):
    r = rule(type="max_count", phrases=None, pattern=r"\*\*[^*]+\*\*", max=1, level="warn")
    rules = cv.load_rules(rules_file(tmp_path, [r]))
    assert cv.check("**a** and **b**", rules, "email")[0]["message"].endswith("(found 2, max 1)")
    assert cv.check("**a** only", rules, "email") == []


def test_channel_length_limit(tmp_path):
    rules = cv.load_rules(rules_file(tmp_path, [rule()], limits={"linkedin-note": {"max_chars": 10, "level": "fail"}}))
    assert cv.check("x" * 11, rules, "linkedin-note")[0]["rule"] == "limit-linkedin-note"
    assert cv.check("x" * 10, rules, "linkedin-note") == []


def test_subject_is_checked_and_labeled(tmp_path):
    rules = cv.load_rules(rules_file(tmp_path, [rule()], limits={"email-subject": {"max_chars": 5, "level": "warn"}}))
    found = cv.check("clean body", rules, "email", subject="synergy now")
    assert {f["rule"] for f in found} == {"r1", "limit-email-subject"}
    assert any(f.get("where") == "subject" for f in found)


def test_fails_sort_before_warnings(tmp_path):
    rules = cv.load_rules(rules_file(tmp_path, [
        rule(id="w", level="warn", phrases=["alpha"]), rule(id="f", phrases=["beta"])]))
    assert [f["rule"] for f in cv.check("alpha beta", rules, "email")] == ["f", "w"]


# ---- command line ----

def test_cli_exit_codes(tmp_path, capsys):
    p = rules_file(tmp_path, [rule(), rule(id="w", level="warn", phrases=["leverage"])])
    assert cv.main(["--rules", str(p), "--channel", "email", "--text", "plain words"]) == 0
    assert cv.main(["--rules", str(p), "--channel", "email", "--text", "synergy"]) == 1
    assert cv.main(["--rules", str(p), "--channel", "email", "--text", "leverage"]) == 0
    assert cv.main(["--rules", str(p), "--channel", "email", "--text", "leverage", "--strict"]) == 1
    assert cv.main(["--rules", str(tmp_path / "missing.json"), "--channel", "email", "--text", "x"]) == 2
    assert cv.main(["--rules", str(p), "--channel", "fax", "--text", "x"]) == 2


def test_cli_json_output_and_file_input(tmp_path, capsys):
    p = rules_file(tmp_path, [rule()])
    draft = tmp_path / "draft.md"
    draft.write_text("Line one.\nWe have synergy.\n", encoding="utf-8")
    assert cv.main(["--rules", str(p), "--channel", "email", str(draft), "--json"]) == 1
    out = json.loads(capsys.readouterr().out)
    assert out["pass"] is False and out["fails"] == 1 and out["findings"][0]["line"] == 2


def test_checker_never_writes_the_draft(tmp_path):
    p = rules_file(tmp_path, [rule()])
    draft = tmp_path / "draft.md"
    draft.write_text("synergy", encoding="utf-8")
    before = draft.read_bytes()
    cv.main(["--rules", str(p), "--channel", "email", str(draft)])
    assert draft.read_bytes() == before
