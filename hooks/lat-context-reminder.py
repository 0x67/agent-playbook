#!/usr/bin/env python3
"""UserPromptSubmit hook: inject the lat.md sections that match the prompt.

Agents rarely run `lat search` on their own, so this runs it for them and
injects up to 3 sections, each with its location, leading paragraph, and up to
4 code links, then the lat.md sync reminder. A section is injected only when its
semantic similarity reaches MIN_SIMILARITY and it links to code that exists.
Search is read-only and only runs when the index already exists. Any failure
falls back to the reminder alone.
Emits nothing when no lat.md/ dir exists in cwd, so non-lat repos stay clean.
"""
import json
import os
import re
import shutil
import subprocess
import sys

LAT_DIR = os.path.join(os.getcwd(), "lat.md")
if not os.path.isdir(LAT_DIR):
    sys.exit(0)

REMINDER = (
    "If you change code, update the relevant `lat.md/` sections and run "
    "`lat check` before finishing. All wiki links and code refs must pass."
)
MAX_SECTIONS = 3
SEARCH_LIMIT = 6
MAX_CODE_LINKS = 4
# keyword matches bypass `lat search --min-similarity`, so the cutoff is applied here.
# Tuned on 48 questions across 3 repos: 0.50 plus the code-link filter below gave the
# best balance of helpful (31) to misleading (5) injections.
MIN_SIMILARITY = 0.50
MIN_PROMPT_WORDS = 4
SEARCH_TIMEOUT_S = 3

SECTION_RE = re.compile(r"^\* Section: \[\[(.+?)\]\]")
SIMILARITY_RE = re.compile(r'"semanticSimilarity":([0-9.]+)')
DEFINED_RE = re.compile(r"^\s*Defined in (\S+?):(\d+)-(\d+)")
INTRO_RE = re.compile(r"^\s*> (.*)")
CODE_LINK_RE = re.compile(r"\[\[([^\]|#]+/[^\]|#]+\.[a-z]+(?:#[^\]|]+)?)(?:\|[^\]]*)?\]\]")
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def prompt_text():
    try:
        return json.load(sys.stdin).get("prompt", "") or ""
    except Exception:
        return ""


def search(prompt):
    """Return [(section id, file, start, end, intro)] from `lat search`, or []."""
    if len(prompt.split()) < MIN_PROMPT_WORDS or prompt.lstrip().startswith("/"):
        return []
    if not shutil.which("lat") or not os.path.exists(os.path.join(LAT_DIR, ".cache", "search.db")):
        return []
    try:
        out = subprocess.run(
            ["lat", "search", prompt[:500], "--limit", str(SEARCH_LIMIT), "--preview", "intro", "--debug"],
            capture_output=True, text=True, timeout=SEARCH_TIMEOUT_S, cwd=os.getcwd(),
        ).stdout
    except Exception:
        return []
    hits, cur = [], None
    for line in ANSI_RE.sub("", out).splitlines():
        if m := SECTION_RE.match(line):
            sim = SIMILARITY_RE.search(line)
            if not sim or float(sim.group(1)) < MIN_SIMILARITY:
                cur = None
                continue
            cur = [m.group(1), None, 0, 0, ""]
            hits.append(cur)
        elif cur and (m := DEFINED_RE.match(line)):
            cur[1], cur[2], cur[3] = m.group(1), int(m.group(2)), int(m.group(3))
        elif cur and not cur[4] and (m := INTRO_RE.match(line)):
            cur[4] = m.group(1).strip()
    return [h for h in hits if h[1]]


def code_links(path, start, end):
    try:
        with open(os.path.join(os.getcwd(), path), encoding="utf-8") as fh:
            body = "".join(fh.readlines()[start - 1:end])
    except Exception:
        return []
    links = []
    for link in CODE_LINK_RE.findall(body):
        if link.startswith("lat.md/") or link in links:
            continue
        if os.path.exists(os.path.join(os.getcwd(), link.split("#", 1)[0])):
            links.append(link)
    return links[:MAX_CODE_LINKS]


def main():
    lines = []
    # sections that link to no existing code (docs of another system, prose-only notes)
    # were the main source of misleading injections, so they are skipped
    picked = []
    for sid, path, start, end, intro in search(prompt_text()):
        links = code_links(path, start, end)
        if links:
            picked.append((sid, path, start, end, intro, links))
        if len(picked) == MAX_SECTIONS:
            break
    if picked:
        lines.append(
            "lat.md sections matching this prompt (from `lat search`). Open the code links "
            "directly, or `lat section \"<id>\"` for the full section:"
        )
        for sid, path, start, end, intro, links in picked:
            lines.append(f"- {sid} ({path}:{start}-{end}): {intro}")
            lines.append("  code: " + ", ".join(links))
        lines.append("")
    lines.append(REMINDER)
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": "\n".join(lines),
        }
    }))


main()
