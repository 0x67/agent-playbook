#!/usr/bin/env python3
"""PreToolUse (Bash|Edit|Write) hook: check new dependencies before they are installed.

1. Install commands and manifest edits: OSV is checked for malicious-package advisories (MAL-*), and for
   known vulnerabilities when a version is pinned.

Every finding becomes a permission prompt for the user (permissionDecision "ask"). A network error or a
timeout never blocks work: that check is skipped.
"""
import json
import os
import re
import shlex
import sys
import urllib.request

OSV_URL = "https://api.osv.dev/v1/querybatch"
OSV_TIMEOUT_S = 4
# a summary that only mentions malicious input ("malicious URLs") is an ordinary vulnerability
MALWARE_SUMMARY = re.compile(r"\bmalware\b|\bmalicious\s+(code|package|version|release|payload)s?\b|\bbackdoor", re.I)


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
        _malware_checked[vuln_id] = "CWE-506" in cwes or bool(MALWARE_SUMMARY.search(d.get("summary", "")))
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


def main():
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return
    tool = data.get("tool_name", "")
    ti = data.get("tool_input") or {}
    reasons = []
    if tool == "Bash":
        reasons += osv_findings(install_targets(ti.get("command", "")))
    elif tool in ("Edit", "Write"):
        reasons += osv_findings(manifest_edit_targets(tool, ti))
    emit(reasons)


if __name__ == "__main__":
    main()
