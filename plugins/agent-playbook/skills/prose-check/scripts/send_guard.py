#!/usr/bin/env python3
"""PreToolUse hook: check prose before it leaves through a message or publishing tool.

Messages (Slack, Jira, Confluence, Gmail, Notion, Claude Docs, Google Docs and Slides): the text in the tool
input is checked. A flagged message is denied once with its findings; resending the identical text goes
through, which covers text the user wrote, and a third flagged attempt on the same tool within 10 minutes
also goes through, so a revise loop cannot stall the task. Messages under 12 words pass.

Artifact publishes: the local files being published (HTML, Markdown, text, JSON data, PowerPoint) are
checked. A publish is denied only for findings not seen before for that file, so findings the agent kept
on purpose do not block every later publish.

State lives in the temp directory per session.
"""
import hashlib
import json
import re
import sys
import tempfile
import time
from pathlib import Path

import prose_check

TEXT_KEYS = {"text", "message", "body", "comment", "content", "description", "markdown", "html_body", "summary"}
CHECKABLE = prose_check.PROSE | prose_check.UI
MIN_WORDS = 12
MAX_DENIALS = 2
WINDOW_S = 600
MAX_REPORTED = 10


def collect(value, key=None, out=None):
    """Prose strings from a tool input: text-like keys at any depth, plus any string of 8 or more words."""
    out = [] if out is None else out
    if isinstance(value, dict):
        for k, v in value.items():
            collect(v, k, out)
    elif isinstance(value, list):
        for item in value:
            collect(item, key, out)
    elif isinstance(value, str):
        words = len(value.split())
        looks_like_prose = not re.match(r"^\s*(?:https?://|[{\[<])", value)
        if looks_like_prose and ((key in TEXT_KEYS and words >= 2) or words >= 8):
            out.append(value.strip())
    return out


def artifact_files(tool_input, cwd):
    """Local files an Artifact publish sends: the page plus `files` sources. Reads and asset uploads send none."""
    if tool_input.get("action") not in (None, "publish") or tool_input.get("asset"):
        return []

    sources = [tool_input.get("file_path")]
    files = tool_input.get("files") or {}
    if isinstance(files, dict):
        sources += [s if isinstance(s, str) else (s or {}).get("from") for s in files.values()]
    elif isinstance(files, list):
        sources += [f.get("path") for f in files if isinstance(f, dict)]

    base = Path(tool_input.get("root") or cwd or ".")
    paths = [Path(s) if Path(s).is_absolute() else base / s for s in sources if isinstance(s, str) and s]
    return [p for p in paths if p.is_file() and p.suffix.lower() in CHECKABLE]


def state_file(session):
    folder = Path(tempfile.gettempdir()) / "prose-check"
    folder.mkdir(exist_ok=True)
    return folder / f"send-guard-{re.sub(r'[^A-Za-z0-9_-]', '', session or 'none')}.json"


def load(path):
    try:
        state = json.loads(path.read_text())
    except (OSError, ValueError):
        state = {}
    return {"flagged": [], "denials": [], "seen": {}, **state}


def deny(reason):
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": reason}}


def listing(found):
    shown = "\n".join(f"- {where}{rule}: {message[:150]}" for where, rule, message in found[:MAX_REPORTED])
    return shown + (f"\n(+{len(found) - MAX_REPORTED} more)" if len(found) > MAX_REPORTED else "")


def check_artifact(paths, state):
    """Findings in the published files that were not reported for the same file before."""
    new = []
    for path in paths:
        seen = set(state["seen"].get(str(path), []))
        found = prose_check.check_path(path, prose_check.engine_for("auto"))
        fresh = [(line, rule, message) for line, rule, message in found if f"{rule}|{message}" not in seen]
        state["seen"][str(path)] = sorted(seen | {f"{rule}|{message}" for _, rule, message in found})
        new += [(f"{path.name} L{line} ", rule, message) for line, rule, message in fresh]
    return new


def main():
    try:
        payload = json.load(sys.stdin)
        tool = payload.get("tool_name", "")
        tool_input = payload.get("tool_input") or {}
        path = state_file(payload.get("session_id"))
        state = load(path)
        now = time.time()

        if tool == "Artifact":
            files = artifact_files(tool_input, payload.get("cwd"))
            found = check_artifact(files, state) if files else []
            path.write_text(json.dumps(state))
            if found:
                print(json.dumps(deny(
                    f"Prose check flagged {len(found)} AI-like pattern(s) in the files being published, so the "
                    f"publish was stopped. Revise them under the humanizer rules, keeping every fact and adding "
                    f"none, then publish again. Findings you keep on purpose will not stop the next publish.\n"
                    f"{listing(found)}"
                )))
            else:
                print("{}")
            return

        text = "\n\n".join(dict.fromkeys(collect(tool_input)))
        if len(text.split()) < MIN_WORDS:
            print("{}")
            return

        digest = hashlib.sha256(" ".join(text.split()).encode()).hexdigest()
        recent = [d for d in state["denials"] if d["tool"] == tool and now - d["at"] < WINDOW_S]
        if digest in state["flagged"] or len(recent) >= MAX_DENIALS:
            print("{}")
            return

        found = sorted(set(prose_check.check_prose(text, prose_check.engine_for("auto"))))
        if not found:
            print("{}")
            return

        state["flagged"].append(digest)
        state["denials"] = [d for d in state["denials"] if now - d["at"] < WINDOW_S] + [{"tool": tool, "at": now}]
        path.write_text(json.dumps(state))
        print(json.dumps(deny(
            f"Prose check flagged {len(found)} AI-like pattern(s) in this message, so it was not sent. Revise the "
            f"text under the humanizer rules, keeping every fact and adding none, then send again. If the user "
            f"wrote this text or asked to send it as is, send the identical text again and it will go through.\n"
            f"{listing([('', rule, message) for _, rule, message in found])}"
        )))
    except Exception:
        print("{}")


if __name__ == "__main__":
    main()
