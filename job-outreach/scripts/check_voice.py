#!/usr/bin/env python3
"""
check_voice.py

Deterministic voice check for anything written in a job seeker's name: recruiter and
hiring-manager emails, LinkedIn connection notes and messages, follow-ups, cover letters,
and resume text. Every agent that runs it on the same draft with the same rules file gets
the same result, which is the point: the voice stays consistent no matter which agent drafts.

The engine holds no opinions about any person. All rules come from a JSON rules file that the
USER owns and keeps in their own workspace (for example `voice/rules.json`). Nothing personal
ships with this skill.

Usage:
  python check_voice.py --rules voice/rules.json --channel email draft.md
  python check_voice.py --rules voice/rules.json --channel linkedin-note --text "Hi ..."
  cat draft.md | python check_voice.py --rules voice/rules.json --channel linkedin-dm -
  add --subject "..." to check an email subject line, --json for machine output,
  --strict to fail on warnings too.

Exit codes: 0 pass (warnings allowed unless --strict), 1 at least one failing finding,
2 usage or rules-file error.

Rules file (version 1):
{
  "version": 1,
  "channels": ["email", "linkedin-note", "linkedin-dm", "cover-letter", "resume"],
  "allow": ["exact approved sentence that must never be flagged", ...],
  "limits": {"linkedin-note": {"max_chars": 300, "level": "fail"},
             "email-subject": {"max_chars": 70, "level": "warn"}},
  "rules": [
    {"id": "no-em-dash", "level": "fail", "type": "chars", "chars": ["\\u2014"],
     "message": "...", "source": "where the rule came from", "channels": ["email", ...]},
    {"id": "...", "level": "warn", "type": "phrases", "phrases": ["..."]},
    {"id": "...", "level": "fail", "type": "regex", "pattern": "...", "flags": "i"},
    {"id": "...", "level": "warn", "type": "opening", "pattern": "...", "flags": "i",
     "within_chars": 300},
    {"id": "...", "level": "warn", "type": "max_count", "pattern": "\\*\\*", "max": 4}
  ]
}
"channels" on a rule is optional; without it the rule applies to every channel.
"level" is "fail" or "warn". A rule may give "levels_by_channel" to override its level for
specific channels, e.g. {"cover-letter": "fail"}.

The checker NEVER edits the draft. It reports findings with the matched text and the rule's
message so the drafter can revise and run it again.
"""
import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

LEVELS = ("fail", "warn")
TYPES = ("chars", "phrases", "regex", "opening", "max_count")
FLAG_MAP = {"i": re.IGNORECASE, "m": re.MULTILINE, "s": re.DOTALL}


class RulesError(Exception):
    pass


def _flags(text):
    value = 0
    for ch in text or "":
        if ch not in FLAG_MAP:
            raise RulesError(f"unknown regex flag {ch!r}; use i, m or s")
        value |= FLAG_MAP[ch]
    return value


def load_rules(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise RulesError(f"rules file not found: {path}")
    except json.JSONDecodeError as exc:
        raise RulesError(f"rules file is not valid JSON: {exc}")
    if not isinstance(data, dict) or data.get("version") != 1:
        raise RulesError("rules file must be a JSON object with \"version\": 1")
    channels = data.get("channels") or []
    if not channels or not all(isinstance(c, str) for c in channels):
        raise RulesError("rules file must list its \"channels\"")
    seen = set()
    compiled = []
    for i, rule in enumerate(data.get("rules") or []):
        where = f"rule #{i + 1} ({rule.get('id', 'no id')})"
        rid = rule.get("id")
        if not rid or rid in seen:
            raise RulesError(f"{where}: every rule needs a unique \"id\"")
        seen.add(rid)
        if rule.get("level") not in LEVELS:
            raise RulesError(f"{where}: \"level\" must be one of {LEVELS}")
        if rule.get("type") not in TYPES:
            raise RulesError(f"{where}: \"type\" must be one of {TYPES}")
        if not rule.get("message"):
            raise RulesError(f"{where}: needs a \"message\" telling the drafter what to do instead")
        for ch in rule.get("channels") or []:
            if ch not in channels:
                raise RulesError(f"{where}: channel {ch!r} is not in the file's channel list")
        for ch, lvl in (rule.get("levels_by_channel") or {}).items():
            if ch not in channels or lvl not in LEVELS:
                raise RulesError(f"{where}: bad levels_by_channel entry {ch!r}: {lvl!r}")
        r = dict(rule)
        t = rule["type"]
        try:
            if t == "chars":
                if not rule.get("chars"):
                    raise RulesError(f"{where}: \"chars\" rule needs a non-empty \"chars\" list")
            elif t == "phrases":
                phrases = rule.get("phrases") or []
                if not phrases:
                    raise RulesError(f"{where}: \"phrases\" rule needs a non-empty \"phrases\" list")
                alts = "|".join(re.escape(p) for p in sorted(phrases, key=len, reverse=True))
                r["_re"] = re.compile(rf"(?<![\w]){alts}(?![\w])", re.IGNORECASE)
            else:
                if not rule.get("pattern"):
                    raise RulesError(f"{where}: \"{t}\" rule needs a \"pattern\"")
                if any(ord(c) < 32 and c not in "\t\n" for c in rule["pattern"]):
                    # "\b" in JSON is a backspace character, not a regex word boundary. A pattern
                    # holding one compiles fine and silently never matches.
                    raise RulesError(f"{where}: pattern contains a control character; in JSON write "
                                     "\\\\b (two backslashes) for a regex word boundary")
                r["_re"] = re.compile(rule["pattern"], _flags(rule.get("flags", "")))
                if t == "max_count" and not isinstance(rule.get("max"), int):
                    raise RulesError(f"{where}: \"max_count\" rule needs an integer \"max\"")
        except re.error as exc:
            raise RulesError(f"{where}: bad pattern: {exc}")
        compiled.append(r)
    limits = data.get("limits") or {}
    for key, lim in limits.items():
        if not isinstance(lim, dict) or not isinstance(lim.get("max_chars"), int) or lim.get("level") not in LEVELS:
            raise RulesError(f"limit {key!r} needs integer \"max_chars\" and a \"level\"")
    return {"channels": channels, "allow": list(data.get("allow") or []), "limits": limits, "rules": compiled}


def _mask(text, allowed):
    """Blank out approved sentences so no rule can flag them; offsets are preserved."""
    for sentence in allowed:
        if not sentence:
            continue
        start = 0
        while True:
            k = text.find(sentence, start)
            if k < 0:
                break
            text = text[:k] + (" " * len(sentence)) + text[k + len(sentence):]
            start = k + len(sentence)
    return text


def _line_of(text, offset):
    return text.count("\n", 0, offset) + 1


def _snippet(text, start, end):
    a, b = max(0, start - 30), min(len(text), end + 30)
    return ("..." if a else "") + text[a:b].replace("\n", " ") + ("..." if b < len(text) else "")


def check(text, rules, channel, subject=None):
    if channel not in rules["channels"]:
        raise RulesError(f"channel {channel!r} is not one of {rules['channels']}")
    findings = []
    masked = _mask(text, rules["allow"])

    def add(rule_id, level, message, start=None, end=None, matched=None, source=None):
        f = {"rule": rule_id, "level": level, "message": message}
        if start is not None:
            f.update({"line": _line_of(text, start), "match": matched if matched is not None else text[start:end],
                      "context": _snippet(text, start, end)})
        if source:
            f["source"] = source
        findings.append(f)

    for r in rules["rules"]:
        if r.get("channels") and channel not in r["channels"]:
            continue
        level = (r.get("levels_by_channel") or {}).get(channel, r["level"])
        t = r["type"]
        if t == "chars":
            for ch in r["chars"]:
                k = masked.find(ch)
                if k >= 0:
                    name = unicodedata.name(ch, hex(ord(ch)))
                    add(r["id"], level, r["message"], k, k + 1, matched=f"{ch} ({name}, x{masked.count(ch)})",
                        source=r.get("source"))
        elif t in ("phrases", "regex"):
            for m in r["_re"].finditer(masked):
                add(r["id"], level, r["message"], m.start(), m.end(), source=r.get("source"))
        elif t == "opening":
            window = masked[: int(r.get("within_chars", 300))]
            m = r["_re"].search(window)
            if m:
                add(r["id"], level, r["message"], m.start(), m.end(), source=r.get("source"))
        elif t == "max_count":
            n = len(r["_re"].findall(masked))
            if n > r["max"]:
                add(r["id"], level, f"{r['message']} (found {n}, max {r['max']})", source=r.get("source"))

    lim = rules["limits"].get(channel)
    if lim and len(text) > lim["max_chars"]:
        add(f"limit-{channel}", lim["level"],
            f"{channel} is {len(text)} characters; the limit is {lim['max_chars']}. Cut it down.")
    if subject is not None:
        sl = rules["limits"].get("email-subject")
        if sl and len(subject) > sl["max_chars"]:
            add("limit-email-subject", sl["level"],
                f"subject is {len(subject)} characters; keep it under {sl['max_chars']}.")
        sub_findings = check_subject(subject, rules, channel)
        findings.extend(sub_findings)
    findings.sort(key=lambda f: (f["level"] != "fail", f.get("line", 0), f["rule"]))
    return findings


def check_subject(subject, rules, channel):
    """Subject lines get the same rules as the body (minus length limits and opening rules)."""
    stripped = {**rules, "limits": {}, "rules": [r for r in rules["rules"] if r["type"] != "opening"]}
    out = check(subject, stripped, channel)
    for f in out:
        f["where"] = "subject"
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check a draft against a voice rules file.")
    ap.add_argument("draft", nargs="?", help="draft file, or - for stdin")
    ap.add_argument("--text", help="check this text instead of a file")
    ap.add_argument("--rules", required=True)
    ap.add_argument("--channel", required=True)
    ap.add_argument("--subject")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true", help="warnings also fail")
    a = ap.parse_args(argv)
    try:
        rules = load_rules(a.rules)
        if a.text is not None:
            text = a.text
        elif a.draft == "-":
            text = sys.stdin.read()
        elif a.draft:
            text = Path(a.draft).read_text(encoding="utf-8")
        else:
            ap.error("give a draft file, - for stdin, or --text")
        findings = check(text, rules, a.channel, a.subject)
    except (RulesError, FileNotFoundError, UnicodeDecodeError) as exc:
        print(f"check_voice: {exc}", file=sys.stderr)
        return 2
    fails = sum(f["level"] == "fail" for f in findings)
    warns = len(findings) - fails
    passed = fails == 0 and not (a.strict and warns)
    if a.json:
        print(json.dumps({"pass": passed, "fails": fails, "warnings": warns, "findings": findings}, indent=2))
    else:
        for f in findings:
            loc = f"line {f['line']}: " if "line" in f else ""
            where = "subject " if f.get("where") == "subject" else ""
            print(f"{f['level'].upper():4} {where}{loc}[{f['rule']}] {f['message']}")
            if "match" in f:
                print(f"     matched: {f['match']!r}   in: {f['context']}")
        print(f"{'PASS' if passed else 'FAIL'}: {fails} failing, {warns} warnings ({a.channel})")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
