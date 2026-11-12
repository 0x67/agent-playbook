#!/usr/bin/env python3
"""PreToolUse hook for message tools (Slack, Jira, Confluence, Gmail, Notion): check the text before it goes out.

When the prose check flags the message, the first send is denied with the findings so the agent can revise
it. Resending the identical text goes through, which covers text the user wrote or asked to send as is,
and a third flagged attempt on the same tool within 10 minutes also goes through, so a revise loop cannot
stall the task. State lives in the temp directory per session. Short messages (under 12 words) pass.
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


def state_file(session):
    folder = Path(tempfile.gettempdir()) / "prose-check"
    folder.mkdir(exist_ok=True)
    return folder / f"send-guard-{re.sub(r'[^A-Za-z0-9_-]', '', session or 'none')}.json"


def load(path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return {"flagged": [], "denials": []}


def deny(reason):
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": reason}}


def main():
    try:
        payload = json.load(sys.stdin)
        tool = payload.get("tool_name", "")
        text = "\n\n".join(dict.fromkeys(collect(payload.get("tool_input") or {})))
        if len(text.split()) < MIN_WORDS:
            print("{}")
            return

        path = state_file(payload.get("session_id"))
        state = load(path)
        now = time.time()
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

        shown = "\n".join(f"- {rule}: {message[:150]}" for _, rule, message in found[:MAX_REPORTED])
        more = f"\n(+{len(found) - MAX_REPORTED} more)" if len(found) > MAX_REPORTED else ""
        print(json.dumps(deny(
            f"Prose check flagged {len(found)} AI-like pattern(s) in this message, so it was not sent. Revise the "
            f"text under the humanizer rules, keeping every fact and adding none, then send again. If the user "
            f"wrote this text or asked to send it as is, send the identical text again and it will go through.\n"
            f"{shown}{more}"
        )))
    except Exception:
        print("{}")


if __name__ == "__main__":
    main()
