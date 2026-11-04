#!/usr/bin/env python3
"""UserPromptSubmit hook: lat.md sync + lat check reminder, no lat search.

Replaces `lat hook claude UserPromptSubmit`, whose injected text mandates
`lat search` (unused here). Keeps the lat check / lat.md sync reminder only.
Emits nothing when no lat.md/ dir exists in cwd, so non-lat repos stay clean.
"""
import json
import os
import sys

if not os.path.isdir(os.path.join(os.getcwd(), "lat.md")):
    sys.exit(0)

context = (
    "`lat.md/` is the project knowledge graph. Use `lat locate` / `lat expand` "
    "to find relevant sections before writing code. "
    "If you change code, update the relevant `lat.md/` sections and run "
    "`lat check` before finishing. All wiki links and code refs must pass."
)

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit",
        "additionalContext": context,
    }
}))
