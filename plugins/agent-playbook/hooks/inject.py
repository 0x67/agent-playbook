"""SessionStart/SubagentStart hook: inject a markdown file (path relative to the plugin root) as context.

Claude Code keeps each hook's output inline only up to 10,000 characters; a longer one is saved to a file and the
model sees a 2,000-character preview. With `PART COUNT` arguments the file is split at top-level `# ` headings into
chunks under LIMIT characters and this run prints chunk PART, so COUNT hook entries deliver the whole file. A part
past the last chunk prints nothing; if the file needs more chunks than COUNT, the last part says where the rest is.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIMIT = 9000


def chunks(text, limit=LIMIT):
    """Consecutive pieces of `text` under `limit` characters, cut at `# ` headings, or at blank lines inside a long section."""
    pieces = []
    for section in re.split(r"(?m)^(?=# )", text):
        while len(section) > limit:
            cut = section.rfind("\n\n", 0, limit)
            cut = cut if cut > 0 else limit
            pieces.append(section[:cut])
            section = section[cut:]
        pieces.append(section)

    out, current = [], ""
    for piece in pieces:
        if current and len(current) + len(piece) > limit:
            out.append(current)
            current = ""
        current += piece
    return out + [current] if current else out


def main() -> None:
    try:
        event = json.load(sys.stdin).get("hook_event_name", "SessionStart")
    except Exception:
        event = "SessionStart"
    try:
        name = sys.argv[1]
        text = (ROOT / name).read_text(encoding="utf-8")
    except (IndexError, OSError):
        print("{}")
        return

    if len(sys.argv) >= 4:
        part, count = int(sys.argv[2]), int(sys.argv[3])
        parts = chunks(text)
        if part > len(parts):
            print("{}")
            return
        text = f"({name}, part {part} of {min(count, len(parts))})\n\n{parts[part - 1]}"
        if part == count and len(parts) > count:
            text += f"\n\n({name} continues past this part; read the rest from {ROOT / name}.)"
    print(json.dumps({"hookSpecificOutput": {"hookEventName": event, "additionalContext": text}}))


if __name__ == "__main__":
    main()
