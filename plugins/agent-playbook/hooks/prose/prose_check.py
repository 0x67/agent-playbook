#!/usr/bin/env python3
"""PostToolUse (Write|Edit) hook and CLI: lint prose with Vale and the cross-sentence checks in xstring.py.

Hook: for a .md, .mdx, .txt or .html file, returns the findings inside the written or edited text as
additionalContext so the agent revises them. Prints {} and stays silent when vale is not installed.
CLI: prose_check.py FILE... prints every finding in each file and exits 1 when there are any.
Everything runs locally; the Vale rules are vendored in styles/.
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import xstring

HERE = Path(__file__).resolve().parent
CONFIG = HERE / ".vale.ini"
EXTENSIONS = {".md", ".mdx", ".txt", ".html"}
SKIP_DIRS = {".git", "node_modules", "vendor", "dist", "build"}
MAX_REPORTED = 12


def skipped(path):
    parts = set(path.parts)
    return path.suffix.lower() not in EXTENSIONS or bool(parts & SKIP_DIRS) or "vetted-skills" in parts


def vale_findings(path):
    result = subprocess.run(
        ["vale", "--config", str(CONFIG), "--output=JSON", str(path)],
        capture_output=True, text=True, timeout=25, stdin=subprocess.DEVNULL,
    )
    try:
        report = json.loads(result.stdout or "{}")
    except ValueError:
        return []

    return [
        (alert["Line"], alert["Check"].split(".")[-1], alert["Message"])
        for alerts in report.values()
        for alert in alerts
    ]


def line_of(text_lines, snippet):
    probe = snippet[:40]
    for number, line in enumerate(text_lines, 1):
        if probe and probe in re.sub(r"[*_`]", "", line):
            return number
    return 0


def structure_findings(path, text):
    if path.suffix.lower() not in {".md", ".mdx", ".txt"}:
        return []

    lines = text.splitlines()
    findings = []
    for kind, sentences in xstring.check_markdown(text).items():
        for sentence in sentences:
            findings.append((line_of(lines, sentence), kind, sentence[:110]))
    return findings


def edited_lines(text, tool_input):
    """Line numbers covered by an Edit's new text; None for a Write, which covers the whole file."""
    pieces = [tool_input.get("new_string")] + [e.get("new_string") for e in tool_input.get("edits") or []]
    pieces = [p for p in pieces if p]
    if not pieces:
        return None

    covered = set()
    for piece in pieces:
        start = text.find(piece)
        if start < 0:
            continue
        first = text.count("\n", 0, start) + 1
        covered.update(range(first, first + piece.count("\n") + 1))
    return covered


def findings_for(path, tool_input=None):
    text = path.read_text(encoding="utf-8", errors="replace")
    found = vale_findings(path) + structure_findings(path, text)

    covered = edited_lines(text, tool_input) if tool_input else None
    if covered is not None:
        found = [f for f in found if f[0] in covered]
    return sorted(set(found))


def describe(path, found):
    shown = "\n".join(f"- L{line} {rule}: {message[:160]}" for line, rule, message in found[:MAX_REPORTED])
    more = f"\n(+{len(found) - MAX_REPORTED} more)" if len(found) > MAX_REPORTED else ""
    return (
        f"Prose check flagged {len(found)} AI-like pattern(s) in {path.name}. Revise these lines before "
        f"reporting, keep every fact, and add none. If you keep one, say why.\n{shown}{more}"
    )


def run_hook():
    try:
        payload = json.load(sys.stdin)
        tool_input = payload.get("tool_input") or {}
        path = Path(tool_input.get("file_path") or "")
        if not shutil.which("vale") or not path.is_file() or skipped(path):
            print("{}")
            return

        found = findings_for(path, tool_input)
        if not found:
            print("{}")
            return

        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": describe(path, found)}}))
    except Exception:
        print("{}")


def run_cli(paths):
    if not shutil.which("vale"):
        sys.exit("vale is not on PATH")

    flagged = 0
    for name in paths:
        path = Path(name)
        found = findings_for(path)
        flagged += len(found)
        print(f"== {path} ({len(found)})")
        for line, rule, message in found:
            print(f"  L{line} {rule}: {message[:160]}")
    sys.exit(1 if flagged else 0)


if __name__ == "__main__":
    if sys.argv[1:]:
        run_cli(sys.argv[1:])
    else:
        run_hook()
