"""UserPromptSubmit hook: short memory and search-order reminder for the model.

additionalContext reaches the model; systemMessage would only show the user a
banner. The full rules arrive with AGENTS.md at session start.
"""
import json
import sys

CONTEXT = (
    "Before planning, coding, reviewing, or investigating: check the MEMORY.md "
    "index, then search in the AGENTS.md order (lat, Semble, fff, codebase-memory, "
    "language server). Missing tool: use built-in tools and say why."
)


def main() -> None:
    try:
        event = json.load(sys.stdin).get("hook_event_name", "UserPromptSubmit")
    except (json.JSONDecodeError, AttributeError):
        event = "UserPromptSubmit"
    print(json.dumps({"hookSpecificOutput": {"hookEventName": event, "additionalContext": CONTEXT}}))


if __name__ == "__main__":
    main()
