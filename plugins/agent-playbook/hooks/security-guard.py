#!/usr/bin/env python3
"""PreToolUse (Bash|Edit|Write) hook: stop and ask before risky moments in daily work.

1. New dependencies (install commands and manifest edits): OSV is checked for malicious-package
   advisories (MAL-*), and for known vulnerabilities when a version is pinned.
2. Skills, plugins, MCP servers, and remote scripts: SkillSpector scans a skill repo or marketplace
   before it is added; MCP servers, `curl | sh`, and git-URL tool installs always ask.
3. Secrets: gitleaks scans the staged diff before `git commit`.
4. Deploy and publish commands always ask; GitHub workflow edits get a zizmor check.

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
import urllib.request

OSV_URL = "https://api.osv.dev/v1/querybatch"
OSV_TIMEOUT_S = 4
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


# ---------------------------------------------------------------- dependencies

def install_targets(cmd):
    """(ecosystem, name, version or None) for each package an install command adds."""
    out = []
    for seg in segments(cmd):
        w = [x for x in words(seg) if x]
        while w and re.match(r"^[A-Z_]+=", w[0]):
            w = w[1:]
        if len(w) < 3:
            continue
        tool, sub, args = w[0], w[1], w[2:]
        pkgs = [a for a in args if not a.startswith("-")]
        if tool in ("npm", "pnpm", "yarn", "bun") and sub in ("install", "i", "add"):
            for p in pkgs:
                if p.startswith((".", "/", "git+", "http", "file:")):
                    continue
                m = re.match(r"^(@?[^@]+)(?:@(.+))?$", p)
                if m:
                    out.append(("npm", m.group(1), m.group(2) if m.group(2) and re.match(r"^\d", m.group(2)) else None))
        elif (tool in ("pip", "pip3") and sub == "install") or (tool == "uv" and sub in ("add", "pip")) or (tool == "poetry" and sub == "add"):
            if tool == "uv" and sub == "pip":
                pkgs = pkgs[1:] if pkgs and pkgs[0] == "install" else []
            for p in pkgs:
                if p.startswith((".", "/", "git+", "http")) or p.endswith((".txt", ".toml")):
                    continue
                m = re.match(r"^([A-Za-z0-9_.\-]+)(?:\[[^\]]*\])?(?:==([\w.]+))?", p)
                if m:
                    out.append(("PyPI", m.group(1), m.group(2)))
        elif tool == "cargo" and sub == "add":
            for p in pkgs:
                m = re.match(r"^([A-Za-z0-9_\-]+)(?:@([\w.]+))?$", p)
                if m:
                    out.append(("crates.io", m.group(1), m.group(2)))
        elif tool == "go" and sub in ("get", "install"):
            for p in pkgs:
                m = re.match(r"^([\w.\-]+\.[a-z]+/[\w.\-/]+?)(?:/\.\.\.)?(?:@(v[\w.\-]+))?$", p)
                if m:
                    out.append(("Go", m.group(1), m.group(2)))
        elif tool == "gem" and sub == "install":
            for p in pkgs:
                out.append(("RubyGems", p, None))
    return out


def manifest_names(path, text):
    """{(ecosystem, name): version or None} declared in a manifest."""
    base = os.path.basename(path)
    found = {}
    try:
        if base == "package.json":
            data = json.loads(text or "{}")
            for key in ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies"):
                for name, spec in (data.get(key) or {}).items():
                    v = re.match(r"^\d[\w.\-]*$", str(spec))
                    found[("npm", name)] = v.group(0) if v else None
        elif base == "Cargo.toml":
            section = ""
            for line in text.splitlines():
                if line.strip().startswith("["):
                    section = line.strip()
                    continue
                if "dependencies" in section:
                    m = re.match(r'^\s*([A-Za-z0-9_\-]+)\s*=\s*(?:"([\d][\w.\-]*)"|\{)', line)
                    if m and "path" not in line and "git" not in line:
                        found[("crates.io", m.group(1))] = m.group(2)
        elif base == "go.mod":
            for m in re.finditer(r"^\s*(?:require\s+)?([\w.\-]+\.[a-z]+/[\w.\-/]+)\s+(v[\w.\-+]+)", text, re.M):
                found[("Go", m.group(1))] = m.group(2)
        elif re.match(r"^requirements.*\.txt$", base):
            for line in text.splitlines():
                m = re.match(r"^\s*([A-Za-z0-9_.\-]+)(?:\[[^\]]*\])?\s*(?:==\s*([\w.]+))?", line)
                if m and not line.strip().startswith(("#", "-")):
                    found[("PyPI", m.group(1))] = m.group(2)
        elif base == "pyproject.toml":
            for block in re.findall(r"dependencies\s*=\s*\[(.*?)\]", text, re.S):
                for spec in re.findall(r'"([^"]+)"', block):
                    m = re.match(r"^([A-Za-z0-9_.\-]+)(?:\[[^\]]*\])?\s*(?:==\s*([\w.]+))?", spec)
                    if m:
                        found[("PyPI", m.group(1))] = m.group(2)
    except ValueError:
        return {}
    return found


_malware_checked = {}


def is_malware(vuln_id):
    """GHSA and other databases file malware under their own ids: CWE-506 or a 'malware' summary."""
    if vuln_id.startswith("MAL-"):
        return True
    if len(_malware_checked) >= 6 and vuln_id not in _malware_checked:
        return False
    if not re.fullmatch(r"[A-Za-z0-9._:-]{1,80}", vuln_id):
        return False
    if vuln_id not in _malware_checked:
        try:
            d = json.load(urllib.request.urlopen(f"https://api.osv.dev/v1/vulns/{vuln_id}", timeout=OSV_TIMEOUT_S))
        except Exception:
            d = {}
        cwes = (d.get("database_specific") or {}).get("cwe_ids") or []
        _malware_checked[vuln_id] = "CWE-506" in cwes or bool(re.search(r"\bmalware\b|\bmalicious\b", d.get("summary", ""), re.I))
    return _malware_checked[vuln_id]


def osv_findings(targets):
    """Advisory ids per target: MAL-* always; other ids only when a version is pinned."""
    if not targets:
        return []
    # one version-less query per package for malware (advisories may not list the pinned version),
    # plus a versioned query for known vulnerabilities when a version is pinned
    queries = [{"package": {"name": name, "ecosystem": eco}} for eco, name, _ in targets]
    pinned = [(i, ver) for i, (_, _, ver) in enumerate(targets) if ver]
    queries += [{"package": queries[i]["package"], "version": ver} for i, ver in pinned]
    try:
        req = urllib.request.Request(OSV_URL, data=json.dumps({"queries": queries}).encode(), headers={"Content-Type": "application/json"})
        results = json.load(urllib.request.urlopen(req, timeout=OSV_TIMEOUT_S)).get("results", [])
    except Exception:
        return []
    ids_of = lambda res: [v.get("id", "") for v in (res or {}).get("vulns", [])]
    versioned = {i: ids_of(results[len(targets) + k]) for k, (i, _) in enumerate(pinned) if len(targets) + k < len(results)}
    out = []
    for i, (eco, name, ver) in enumerate(targets):
        mal = [x for x in ids_of(results[i] if i < len(results) else {}) if is_malware(x)]
        vulns = versioned.get(i, [])
        if mal:
            out.append(f"{name} ({eco}) is reported as a malicious package: {', '.join(mal[:3])}")
        elif vulns:
            out.append(f"{name} {ver} ({eco}) has known vulnerabilities: {', '.join(vulns[:3])}{' and more' if len(vulns) > 3 else ''}")
    return out


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


def manifest_edit_targets(tool, ti):
    path = ti.get("file_path", "")
    if not re.search(r"(^|/)(package\.json|Cargo\.toml|go\.mod|pyproject\.toml|requirements[^/]*\.txt)$", path):
        return []
    new = new_text_for(tool, ti)
    if new is None:
        return []
    try:
        old = open(path, encoding="utf-8").read()
    except OSError:
        old = ""
    before, after = manifest_names(path, old), manifest_names(path, new)
    return [(eco, name, ver) for (eco, name), ver in after.items() if (eco, name) not in before or before[(eco, name)] != ver]


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
        reasons += osv_findings(install_targets(cmd))
        reasons += extension_reasons(cmd)
        reasons += [r for r in (gitleaks_reason(cmd, cwd), deploy_reason(cmd)) if r]
    elif tool in ("Edit", "Write"):
        reasons += osv_findings(manifest_edit_targets(tool, ti))
        reasons += [r for r in (new_skill_file_reason(tool, ti), workflow_reason(tool, ti)) if r]
    emit(reasons)


if __name__ == "__main__":
    main()
