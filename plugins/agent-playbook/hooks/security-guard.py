#!/usr/bin/env python3
"""PreToolUse (Bash|Edit|Write) hook: stop and ask before risky moments in daily work.

1. Skills, plugins, MCP servers, and remote scripts: SkillSpector scans a skill repo or marketplace
   before it is added; MCP servers, `curl | sh`, and git-URL tool installs always ask.
2. Secrets: gitleaks scans the staged diff before `git commit`.
3. Deploy and publish commands always ask; GitHub workflow edits get a zizmor check.

New dependencies are checked by dep-guard.py.

Every finding becomes a permission prompt for the user (permissionDecision "ask"). A missing scanner,
a network error, or a timeout never blocks work: that check is skipped.
"""
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile

SCAN_TIMEOUT_S = 90

DEPLOY = [
    (r"\bgit\s+push\b", "git push"),
    (r"\b(npm|pnpm|bun)\s+publish\b|\byarn\s+(npm\s+)?publish\b", "package publish"),
    (r"\bcargo\s+publish\b", "crate publish"),
    (r"\b(twine\s+upload|uv\s+publish|poetry\s+publish|gem\s+push)\b", "package publish"),
    (r"\b(docker|podman)\s+(image\s+)?push\b", "image push"),
    (r"\bkubectl\s+(apply|create|delete|replace|patch|rollout|scale)\b", "Kubernetes change"),
    (r"\bhelm\s+(install|upgrade|uninstall|rollback)\b", "Helm release change"),
    (r"\b(terraform|tofu)\s+(apply|destroy|import)\b|\bpulumi\s+(up|destroy)\b", "infrastructure change"),
    (r"\bgh\s+release\s+(create|upload|delete)\b|\bgh\s+pr\s+merge\b", "GitHub release or merge"),
    (r"\bgh\s+stack\s+(push|submit|sync|link|merge|unstack|delete)\b", "gh stack push, PR, or merge"),
    (r"\b(vercel\s+(--prod|deploy)|netlify\s+deploy|fly\s+deploy|wrangler\s+(deploy|publish)|firebase\s+deploy)\b", "deploy"),
]
REMOTE_EXEC = re.compile(r"\b(curl|wget)\b[^|;&]*\|\s*(sudo\s+)?(sh|bash|zsh|python3?|node)\b|\b(sh|bash)\s+<\(\s*(curl|wget)\b|\biwr\b[^|]*\|\s*iex\b")
GIT_URL_INSTALL = re.compile(r"\b(uv\s+tool\s+install|uvx|pipx\s+install|pip3?\s+install|npm\s+(i|install)\s+-g|cargo\s+install)\b[^;&|]*\b(git\+|https?://github\.com/|--git\b)")


def emit(reasons):
    if reasons:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": " | ".join(reasons),
        }}))


def segments(cmd):
    """Split a shell line into simple commands on ; && || | and newlines."""
    return [s.strip() for s in re.split(r"&&|\|\||[;|\n]", cmd) if s.strip()]


def words(seg):
    try:
        return shlex.split(seg)
    except ValueError:
        return seg.split()


# ---------------------------------------------------------------- shared

def new_text_for(tool, ti):
    path = ti.get("file_path", "")
    if tool == "Write":
        return ti.get("content", "")
    try:
        old = open(path, encoding="utf-8").read()
    except OSError:
        return None
    a, b = ti.get("old_string", ""), ti.get("new_string", "")
    if not a:
        return None
    return old.replace(a, b) if ti.get("replace_all") else old.replace(a, b, 1)



# ---------------------------------------------------------------- skills, plugins, MCP

def skillspector(target, label=None):
    """One-line summary when SkillSpector rates the target anything but SAFE, else None."""
    if not shutil.which("skillspector"):
        return None
    with tempfile.TemporaryDirectory() as tmp:
        report = os.path.join(tmp, "report.json")
        try:
            subprocess.run(["skillspector", "scan", target, "--no-llm", "--format", "json", "--output", report],
                           capture_output=True, text=True, timeout=SCAN_TIMEOUT_S, stdin=subprocess.DEVNULL)
            data = json.load(open(report))
        except subprocess.TimeoutExpired:
            return f"SkillSpector did not finish scanning {target} within {SCAN_TIMEOUT_S}s; review it before installing"
        except (OSError, ValueError):
            return None
    ra = data.get("risk_assessment") or {}
    rec = data.get("risk_recommendation") or ra.get("recommendation") or ""
    sev = data.get("risk_severity") or ra.get("severity") or "?"
    if str(rec).upper() == "SAFE":
        return None
    skills = data.get("skills") or [data]
    cats = {}
    for s in skills:
        for i in s.get("issues", []):
            cats[i.get("category", "?")] = cats.get(i.get("category", "?"), 0) + 1
    top = ", ".join(f"{k} x{v}" for k, v in sorted(cats.items(), key=lambda kv: -kv[1])[:4])
    return f"SkillSpector rates {label or target} {sev} ({rec}): {top or 'see a full scan'}"


def config_dir():
    return os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")


def repo_url(spec):
    if spec.startswith(("http://", "https://", "git@")):
        return spec
    if re.match(r"^[\w.\-]+/[\w.\-]+$", spec):
        return f"https://github.com/{spec}"
    return None


def extension_reasons(cmd):
    reasons = []
    for seg in segments(cmd):
        w = words(seg)
        joined = " ".join(w)
        if re.match(r"^npx\s+(-y\s+)?skills\s+add\s+\S+", joined):
            url = repo_url(w[w.index("add") + 1])
            if url and (r := skillspector(url)):
                reasons.append(r)
        elif re.match(r"^claude\s+plugin\s+marketplace\s+add\s+\S+", joined):
            url = repo_url(w[4])
            if url and (r := skillspector(url)):
                reasons.append(r)
        elif re.match(r"^claude\s+plugin\s+install\s+\S+@\S+", joined):
            market = w[3].split("@", 1)[1]
            d = os.path.join(config_dir(), "plugins", "marketplaces", market)
            if os.path.isdir(d) and (r := skillspector(d)):
                reasons.append(r)
        elif re.match(r"^claude\s+mcp\s+(add|add-json|add-from-claude-desktop)\b", joined):
            reasons.append(f"Adds an MCP server, which runs code with tool access: {seg[:160]}")
    if REMOTE_EXEC.search(cmd):
        reasons.append("Pipes a downloaded script straight into an interpreter; read the script first")
    if GIT_URL_INSTALL.search(cmd):
        reasons.append("Installs code straight from a git repository; check the source and pin a commit or tag")
    return reasons


def new_skill_file_reason(tool, ti):
    path = ti.get("file_path", "")
    installed = re.search(r"(^|/)\.claude(-[\w-]+)?/(skills/[^/]+/SKILL\.md|agents/[^/]+\.md|commands/[^/]+\.md)$", path)
    if tool != "Write" or not installed or os.path.exists(path):
        return None
    with tempfile.TemporaryDirectory() as tmp:
        d = os.path.join(tmp, "skill")
        os.makedirs(d)
        with open(os.path.join(d, "SKILL.md"), "w", encoding="utf-8") as fh:
            fh.write(ti.get("content", ""))
        return skillspector(d, label=path)


# ---------------------------------------------------------------- secrets, deploy, workflows

def gitleaks_reason(cmd, cwd):
    if not re.search(r"\bgit\s+commit\b", cmd) or not shutil.which("gitleaks"):
        return None
    # `git commit -a` also commits unstaged changes to tracked files, so scan those too
    with_unstaged = bool(re.search(r"\bgit\s+commit\b[^;&|]*\s-[A-Za-z]*a[A-Za-z]*\b|\bgit\s+commit\b[^;&|]*--all\b", cmd))
    leaks = []
    with tempfile.TemporaryDirectory() as tmp:
        for staged in ([True, False] if with_unstaged else [True]):
            report = os.path.join(tmp, f"leaks-{staged}.json")
            args = ["gitleaks", "git", "--pre-commit", *(["--staged"] if staged else []), "--redact", "--no-banner",
                    "--exit-code", "0", "--report-format", "json", "--report-path", report]
            try:
                subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=30, stdin=subprocess.DEVNULL)
                leaks += json.load(open(report)) or []
            except (subprocess.TimeoutExpired, OSError, ValueError):
                continue
    if not leaks:
        return None
    where = ", ".join(f"{l.get('File')}:{l.get('StartLine')} ({l.get('RuleID')})" for l in leaks[:3])
    return f"gitleaks found {len(leaks)} possible secret(s) in what this commit adds: {where}"


def deploy_reason(cmd):
    hits = [label for pat, label in DEPLOY if re.search(pat, cmd)]
    if hits:
        return f"Outward-facing action ({', '.join(dict.fromkeys(hits))}): {cmd.strip()[:160]}"
    return None


def workflow_reason(tool, ti):
    path = ti.get("file_path", "")
    if not re.search(r"(^|/)\.github/workflows/[^/]+\.ya?ml$", path) or not shutil.which("zizmor"):
        return None
    new = new_text_for(tool, ti)
    if not new:
        return None
    with tempfile.TemporaryDirectory() as tmp:
        f = os.path.join(tmp, os.path.basename(path))
        with open(f, "w", encoding="utf-8") as fh:
            fh.write(new)
        try:
            out = subprocess.run(["zizmor", "--offline", "--format", "json", f], capture_output=True, text=True, timeout=30, stdin=subprocess.DEVNULL).stdout
            findings = json.loads(out or "[]")
        except (subprocess.TimeoutExpired, OSError, ValueError):
            return None
    serious = [x for x in findings if str((x.get("determinations") or {}).get("severity", "")).lower() in ("medium", "high")]
    if not serious:
        return None
    ids = ", ".join(dict.fromkeys(x.get("ident", "?") for x in serious))
    return f"zizmor flags this workflow change: {ids}"


def main():
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return
    tool = data.get("tool_name", "")
    ti = data.get("tool_input") or {}
    cwd = data.get("cwd") or os.getcwd()
    reasons = []
    if tool == "Bash":
        cmd = ti.get("command", "")
        reasons += extension_reasons(cmd)
        reasons += [r for r in (gitleaks_reason(cmd, cwd), deploy_reason(cmd)) if r]
    elif tool in ("Edit", "Write"):
        reasons += [r for r in (new_skill_file_reason(tool, ti), workflow_reason(tool, ti)) if r]
    emit(reasons)


if __name__ == "__main__":
    main()
