#!/usr/bin/env python3
"""Generate the Claude-written side of the prose-check benchmark with a stripped-down `claude -p`.

usage: bench/prose-check/generate-ai.py GO_BLOG_DIR OUT_DIR [N_TOPICS]

Titles are a seeded sample of the Go blog titles that fetch-open.py writes, so the human and AI sides
cover the same topics. Each title goes to Sonnet 5.5 and Opus 5.5 with no tools, MCP servers, hooks,
plugins, auto-memory, or CLAUDE.md, under a neutral system prompt, so the text shows the model's own
habits. Writes OUT_DIR/<model>/<slug>.md and OUT_DIR/costs.json; existing posts are kept. The committed
corpus in ai-claude/ came from this script on 2026-11-13 and cost $3.93 on a Claude subscription.
"""
import concurrent.futures as cf
import json
import os
import random
import re
import subprocess
import sys
import tempfile
from pathlib import Path

MODELS = {"sonnet": "claude-sonnet-5-5", "opus": "claude-opus-5-5"}
PROMPT = ("Write an engineering blog post titled \"{title}\" for a software company's engineering blog. "
          "About 700 words, in Markdown, starting with the title as a heading.")


def clean_settings():
    config = Path(os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude"))
    installed = config / "plugins" / "installed_plugins.json"
    plugins = json.loads(installed.read_text()).get("plugins", {}) if installed.exists() else {}
    return {
        "disableAllHooks": True, "autoMemoryEnabled": False,
        "syncClaudeAiPlugins": False, "syncClaudeAiSkills": False,
        "claudeMdExcludes": [str(config / "CLAUDE.md"), "**/CLAUDE.md"],
        "enabledPlugins": {name: False for name in plugins},
    }


def topics(go_blog, count):
    titles = []
    for path in sorted(Path(go_blog).glob("*.md")):
        match = re.search(r"^title:\s*(.+)$", path.read_text(errors="replace"), re.M)
        if match:
            titles.append(match.group(1).strip().strip("\"'"))
    random.seed(5)
    return random.sample(titles, count)


def generate(job, out, settings, workdir):
    model, title = job
    target = out / model / (re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:60] + ".md")
    if target.exists():
        return model, title, 0.0, "kept"

    result = subprocess.run(
        ["claude", "-p", PROMPT.format(title=title), "--model", MODELS[model], "--settings", settings,
         "--strict-mcp-config", "--tools", "", "--system-prompt", "You are a helpful assistant.",
         "--no-session-persistence", "--output-format", "json"],
        capture_output=True, text=True, stdin=subprocess.DEVNULL, cwd=workdir, timeout=600,
    )
    data = json.loads(result.stdout or "{}")
    if not data.get("result"):
        return model, title, 0.0, result.stderr[-200:]
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(data["result"] + "\n", encoding="utf-8")
    return model, title, data.get("total_cost_usd") or 0.0, "ok"


def main():
    go_blog, out = sys.argv[1], Path(sys.argv[2])
    count = int(sys.argv[3]) if len(sys.argv) > 3 else 40

    with tempfile.TemporaryDirectory() as workdir:
        settings = Path(workdir) / "settings.json"
        settings.write_text(json.dumps(clean_settings()))
        jobs = [(model, title) for model in MODELS for title in topics(go_blog, count)]

        # the first request runs alone so the rest can read its prompt cache
        results = [generate(jobs[0], out, str(settings), workdir)]
        with cf.ThreadPoolExecutor(4) as pool:
            results += pool.map(lambda job: generate(job, out, str(settings), workdir), jobs[1:])

    cost = sum(r[2] for r in results)
    (out / "costs.json").write_text(json.dumps({"total_usd": round(cost, 4), "runs": results}, indent=1) + "\n")
    print(f"{len(results)} posts, ${cost:.2f}, failed: {[r[:2] for r in results if r[3] not in ('ok', 'kept')]}")


if __name__ == "__main__":
    main()
