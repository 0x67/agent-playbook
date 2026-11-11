"""SessionStart/SubagentStart hook: inject a markdown file (path relative to the plugin root) as context."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    try:
        event = json.load(sys.stdin).get("hook_event_name", "SessionStart")
    except Exception:
        event = "SessionStart"
    try:
        text = (ROOT / sys.argv[1]).read_text(encoding="utf-8")
    except (IndexError, OSError):
        print("{}")
        return
    print(json.dumps({"hookSpecificOutput": {"hookEventName": event, "additionalContext": text}}))


if __name__ == "__main__":
    main()
