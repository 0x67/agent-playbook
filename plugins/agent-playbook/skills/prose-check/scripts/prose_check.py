#!/usr/bin/env python3
"""Check prose for AI-like patterns: a PostToolUse (Write|Edit) hook, and a CLI.

CLI:  prose_check.py [--engine auto|vale|lite] [--json] FILE...   ("-" reads Markdown from stdin)
Hook: run with no arguments; reads the Write or Edit payload on stdin and returns the findings inside
      the written or edited lines as additionalContext.

Markdown and text files are checked as prose. HTML, JSX/TSX, Vue, Svelte, PowerPoint and JSON files have
their strings extracted (extract_strings.py) and checked one by one and as a set (xstring.py). The vale-ai-tells rules
run through Vale when it is on PATH, with ../vale.ini, and through vale_lite.py otherwise. Nothing leaves
the machine.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import extract_strings
import vale_lite
import xstring

HERE = Path(__file__).resolve().parent
CONFIG = HERE.parent / "vale.ini"
PROSE = {".md", ".mdx", ".txt"}
UI = {".html", ".htm", ".tsx", ".jsx", ".vue", ".svelte", ".pptx", ".json"}
# config and data JSON is written constantly while coding, so the Write/Edit hook leaves it to the CLI
NOT_HOOKED = {".json", ".pptx"}
SKIP_DIRS = {".git", "node_modules", "vendor", "dist", "build", "vetted-skills"}
MAX_REPORTED = 12


def engine_for(choice):
    if choice == "auto":
        return "vale" if shutil.which("vale") else "lite"
    return choice


def rule_findings(text, engine):
    """(line, rule, message) from the vale-ai-tells rules, for Markdown text."""
    if engine == "lite":
        return [(line, rule, message) for line, rule, message, _ in vale_lite.lint(text)]

    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as tmp:
        tmp.write(text)
    try:
        out = subprocess.run(
            ["vale", "--config", str(CONFIG), "--output=JSON", tmp.name],
            capture_output=True, text=True, timeout=25, stdin=subprocess.DEVNULL,
        )
        report = json.loads(out.stdout or "{}")
    except (ValueError, subprocess.TimeoutExpired):
        report = {}
    finally:
        Path(tmp.name).unlink(missing_ok=True)

    return [(a["Line"], a["Check"].split(".")[-1], a["Message"]) for alerts in report.values() for a in alerts]


def structure_findings(results, where):
    """Flatten xstring results into (line, rule, message); a cluster becomes one finding."""
    for kind, value in results.items():
        if isinstance(value, dict):
            for key, members in value.items():
                if isinstance(members, int):
                    yield 0, kind, f"{members} strings share the sentence-length shape {key}"
                else:
                    yield where(members[0]), kind, f"{len(members)}x '{key}', e.g. {members[0][:90]}"
        else:
            for item in value:
                yield where(item), kind, item[:110]


def check_prose(text, engine):
    lines = [re.sub(r"[*_`]", "", line) for line in text.splitlines()]

    def where(snippet):
        probe = snippet[:40]
        return next((n for n, line in enumerate(lines, 1) if probe and probe in line), 0)

    return rule_findings(text, engine) + list(structure_findings(xstring.check_markdown(text), where))


def check_ui(path, engine):
    strings = extract_strings.extract(path)
    if not strings:
        return []

    # each string sits on its own line with a blank line after it, so document line 2k-1 is string k
    document = "\n\n".join(text for _, text in strings)
    found = [
        (strings[(line - 1) // 2][0] if 0 < line <= 2 * len(strings) else 0, rule, message)
        for line, rule, message in rule_findings(document, engine)
    ]

    def where(snippet):
        return next((line for line, text in strings if snippet[:40] in text), 0)

    return found + list(structure_findings(xstring.check_strings([t for _, t in strings]), where))


def check_path(path, engine):
    if path.suffix.lower() in UI:
        return sorted(set(check_ui(path, engine)))
    return sorted(set(check_prose(path.read_text(encoding="utf-8", errors="replace"), engine)))


def skipped(path):
    suffix = path.suffix.lower()
    return suffix not in PROSE | UI or suffix in NOT_HOOKED or bool(set(path.parts) & SKIP_DIRS)


def edited_lines(path, tool_input):
    """Line numbers covered by an Edit's new text; None for a Write, which covers the whole file."""
    pieces = [tool_input.get("new_string")] + [e.get("new_string") for e in tool_input.get("edits") or []]
    pieces = [p for p in pieces if p]
    if not pieces:
        return None

    text = path.read_text(encoding="utf-8", errors="replace")
    covered = set()
    for piece in pieces:
        start = text.find(piece)
        if start >= 0:
            first = text.count("\n", 0, start) + 1
            covered.update(range(first, first + piece.count("\n") + 1))
    return covered


def describe(path, found):
    shown = "\n".join(f"- L{line} {rule}: {message[:160]}" for line, rule, message in found[:MAX_REPORTED])
    more = f"\n(+{len(found) - MAX_REPORTED} more)" if len(found) > MAX_REPORTED else ""
    return (
        f"Prose check flagged {len(found)} AI-like pattern(s) in {path.name}. Revise these lines before "
        f"reporting, keep every fact, and add none. If you keep one, say why.\n{shown}{more}"
    )


def run_hook():
    try:
        tool_input = json.load(sys.stdin).get("tool_input") or {}
        path = Path(tool_input.get("file_path") or "")
        if not path.is_file() or skipped(path):
            print("{}")
            return

        found = check_path(path, engine_for("auto"))
        covered = edited_lines(path, tool_input)
        if covered is not None:
            found = [f for f in found if f[0] in covered]

        context = describe(path, found) if found else None
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": context}}) if context else "{}")
    except Exception:
        print("{}")


def run_cli(argv):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("paths", nargs="+", help='files to check, or "-" for Markdown on stdin')
    parser.add_argument("--engine", choices=("auto", "vale", "lite"), default="auto")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    engine = engine_for(args.engine)
    if engine == "vale" and not shutil.which("vale"):
        sys.exit("vale is not on PATH; use --engine lite")

    report = {}
    for name in args.paths:
        if name == "-":
            report["stdin"] = sorted(set(check_prose(sys.stdin.read(), engine)))
        else:
            report[name] = check_path(Path(name), engine)

    if args.json:
        print(json.dumps({"engine": engine, "files": {k: [list(f) for f in v] for k, v in report.items()}}, indent=1))
    else:
        for name, found in report.items():
            print(f"== {name} ({len(found)}, engine {engine})")
            for line, rule, message in found:
                print(f"  L{line} {rule}: {message[:160]}")
    sys.exit(1 if any(report.values()) else 0)


if __name__ == "__main__":
    if sys.argv[1:]:
        run_cli(sys.argv[1:])
    else:
        run_hook()
