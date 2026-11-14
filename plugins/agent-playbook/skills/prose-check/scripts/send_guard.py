#!/usr/bin/env python3
"""PreToolUse hook: check prose before it leaves through a message, publishing, or commit command.

Messages (Slack, Jira, Confluence, Gmail, Notion, Claude Docs, Google Docs and Slides): the text in the tool
input is checked. A flagged message is denied once with its findings; resending the identical text goes
through, which covers text the user wrote, and a third flagged attempt on the same tool within 10 minutes
also goes through, so a revise loop cannot stall the task. Messages under 12 words pass.

Bash: the message of `git commit -m/-F` (heredoc form included) and the body of `gh pr|issue create, edit,
comment` (`--body`, `--body-file`) go through the same check as messages. A header-only commit is too
short to be checked.

Artifact publishes: the local files being published (HTML, Markdown, text, JSON data, PowerPoint) are
checked. A publish is denied only for findings not seen before for that file, so findings the agent kept
on purpose do not block every later publish. Before that, a publish from an agent whose transcript shows no
load of the humanizer skill since its last compaction is denied once with a request to load it. The next
publish goes through either way, so a lane without the skill is not blocked. A subagent is judged by its
own transcript.

State lives in the temp directory per session.
"""
import hashlib
import json
import re
import shlex
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
HUMANIZER_SKILLS = {"humanizer", "humanizer:humanizer"}


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


OPERATORS = {"&&", "||", ";", "|", "&"}
HEREDOC = re.compile(r"<<-?\s*['\"]?(\w+)['\"]?\n(.*?)\n\s*\1\b", re.S)


def unwrap(value):
    """The text of a "$(cat <<'EOF' ... EOF)" argument, or the argument itself."""
    match = HEREDOC.search(value)
    return match.group(2) if match else value


def read_file(path, cwd):
    target = Path(path) if Path(path).is_absolute() else Path(cwd or ".") / path
    try:
        return target.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def bash_text(command, cwd):
    """Message text from git commit and gh pr/issue commands in a shell command line."""
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        return ""

    texts, i = [], 0
    while i < len(tokens):
        is_commit = tokens[i] == "git" and "commit" in tokens[i + 1:i + 4]
        is_gh = tokens[i] == "gh" and tokens[i + 1:i + 2] and tokens[i + 1] in ("pr", "issue")
        if not (is_commit or is_gh):
            i += 1
            continue

        j = i + 1
        while j < len(tokens) and tokens[j] not in OPERATORS:
            flag, value = tokens[j], tokens[j + 1] if j + 1 < len(tokens) else ""
            if flag.startswith("--") and "=" in flag:
                flag, value = flag.split("=", 1)
            if (is_commit and flag in ("-m", "--message")) or (is_gh and flag in ("-b", "--body")):
                texts.append(unwrap(value))
            elif (is_commit and flag in ("-F", "--file")) or (is_gh and flag in ("-F", "--body-file")):
                texts.append(read_file(value, cwd))
            j += 1
        i = j
    return "\n\n".join(t.strip() for t in texts if t.strip())


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


def agent_transcript(payload):
    """The transcript of the agent making the call; a subagent (`agent_id`) has its own file under the session."""
    path = payload.get("transcript_path")
    if not path:
        return None
    agent = payload.get("agent_id")
    return Path(path).with_suffix("") / "subagents" / f"agent-{agent}.jsonl" if agent else Path(path)


def loads_humanizer(entry):
    """Whether a transcript entry is a humanizer load: the agent's Skill call, or the skill text Claude Code adds
    as a meta user message (a slash command included)."""
    content = (entry.get("message") or {}).get("content")
    if entry.get("type") == "assistant" and isinstance(content, list):
        return any(part.get("type") == "tool_use" and part.get("name") == "Skill"
                   and (part.get("input") or {}).get("skill") in HUMANIZER_SKILLS for part in content)
    if entry.get("type") == "user" and entry.get("isMeta"):
        parts = content if isinstance(content, list) else [{"type": "text", "text": content or ""}]
        for part in parts:
            text = (part.get("text") or "") if part.get("type") == "text" else ""
            if text.startswith("Base directory for this skill:") and "/humanizer" in text.split("\n", 1)[0]:
                return True
    return False


def humanizer_loaded(transcript):
    """Whether the transcript shows a humanizer load after its last compaction, which cuts loaded skill text
    short. An unreadable transcript counts as loaded."""
    loaded = False
    try:
        with open(transcript, encoding="utf-8", errors="replace") as lines:
            for line in lines:
                if "compact_boundary" not in line and "humanizer" not in line:
                    continue
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                if entry.get("subtype") == "compact_boundary":
                    loaded = False
                elif loads_humanizer(entry):
                    loaded = True
    except (OSError, TypeError):
        return True
    return loaded


def state_file(session):
    folder = Path(tempfile.gettempdir()) / "prose-check"
    folder.mkdir(exist_ok=True)
    return folder / f"send-guard-{re.sub(r'[^A-Za-z0-9_-]', '', session or 'none')}.json"


def load(path):
    try:
        state = json.loads(path.read_text())
    except (OSError, ValueError):
        state = {}
    return {"flagged": [], "denials": [], "seen": {}, "humanizer_asked": [], **state}


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
            agent = payload.get("agent_id") or "main"
            if files and agent not in state["humanizer_asked"] and not humanizer_loaded(agent_transcript(payload)):
                state["humanizer_asked"].append(agent)
                path.write_text(json.dumps(state))
                print(json.dumps(deny(
                    "The humanizer skill has not been loaded in this conversation, so the publish was stopped. Load "
                    "it with the Skill tool (`humanizer:humanizer`, embedded mode) and revise the prose in the files "
                    "under its rules. Keep every fact and add none, then publish again. If the skill is not "
                    "installed, publish again and this check will not stop it."
                )))
                return
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

        if tool == "Bash":
            text = bash_text(tool_input.get("command", ""), payload.get("cwd"))
        else:
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
            f"Prose check flagged {len(found)} AI-like pattern(s) in this message, so it was stopped. Revise the "
            f"text under the humanizer rules, keeping every fact and adding none, then send again. If the user "
            f"wrote this text or asked to send it as is, send the identical text again and it will go through.\n"
            f"{listing([('', rule, message) for _, rule, message in found])}"
        )))
    except Exception:
        print("{}")


if __name__ == "__main__":
    main()
