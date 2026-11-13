#!/usr/bin/env python3
"""PreToolUse (Bash|Edit|Write) hook: check new dependencies before they are installed.

1. Install commands and manifest edits: OSV is checked for malicious-package advisories (MAL-*), and for
   known vulnerabilities when a version is pinned.
2. Release age: a version published less than AGENT_PLAYBOOK_MIN_AGE_DAYS ago (default 7, 0 turns it off)
   asks, using publish times from deps.dev (npm, PyPI, crates.io, Go, RubyGems).
3. Lockfiles: before `npm ci`, `npm install`, `pnpm install`, `yarn install`, or `bun install`, every lockfile
   entry that is not in HEAD gets the OSV and age checks, and npm entries with install scripts are named.
4. Adding a package with `npm install <pkg>` or `pnpm add <pkg>` is resolved first in a temp copy of
   package.json and the lockfile (no scripts, project files untouched), so the packages it pulls in get
   the same checks before anything is installed. npm workspaces, `yarn add`, and `bun add` keep check 1 only.

Every finding becomes a permission prompt for the user (permissionDecision "ask"). A network error or a
timeout never blocks work: that check is skipped.
"""
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

OSV_URL = "https://api.osv.dev/v1/querybatch"
OSV_TIMEOUT_S = 4
DEPS_DEV_URL = "https://api.deps.dev/v3"
DEPS_DEV_SYSTEMS = {"npm": "npm", "PyPI": "pypi", "crates.io": "cargo", "Go": "go", "RubyGems": "rubygems"}
DEFAULT_MIN_AGE_DAYS = 7
MAX_AGE_LOOKUPS = 60
MAX_LOCK_ENTRIES = 300
RESOLVE_TIMEOUT_S = 60
LOCKFILE_OF = {"npm": "package-lock.json", "pnpm": "pnpm-lock.yaml", "yarn": "yarn.lock", "bun": "bun.lock"}
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


# ---------------------------------------------------------------- release age

def min_age_days():
    try:
        return float(os.environ.get("AGENT_PLAYBOOK_MIN_AGE_DAYS", DEFAULT_MIN_AGE_DAYS))
    except ValueError:
        return DEFAULT_MIN_AGE_DAYS


def fetch_json(url):
    try:
        with urllib.request.urlopen(url, timeout=OSV_TIMEOUT_S) as resp:
            return json.load(resp)
    except Exception:
        return None


def published(target):
    """(version, publish time) from deps.dev; the package's default version when none is pinned."""
    eco, name, version = target
    system = DEPS_DEV_SYSTEMS.get(eco)
    if not system:
        return None
    base = f"{DEPS_DEV_URL}/systems/{system}/packages/{urllib.parse.quote(name, safe='')}"
    if version:
        data = fetch_json(f"{base}/versions/{urllib.parse.quote(version, safe='')}")
        return (version, data.get("publishedAt")) if data else None
    for v in (fetch_json(base) or {}).get("versions", []):
        if v.get("isDefault"):
            return v["versionKey"]["version"], v.get("publishedAt")
    return None


def age_text(seconds):
    hours = int(seconds // 3600)
    return f"{hours} hour{'s' * (hours != 1)}" if hours < 48 else f"{hours // 24} days"


def age_findings(targets):
    """Targets whose version is younger than AGENT_PLAYBOOK_MIN_AGE_DAYS."""
    limit = min_age_days()
    todo = list(dict.fromkeys(targets))[:MAX_AGE_LOOKUPS]
    if limit <= 0 or not todo:
        return []

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(zip(todo, pool.map(published, todo)))
    now, young = datetime.now(timezone.utc), []
    for (eco, name, _), found in results:
        if not found or not found[1]:
            continue
        version, when = found
        age = (now - datetime.fromisoformat(when.replace("Z", "+00:00"))).total_seconds()
        if age < limit * 86400:
            young.append((eco, f"{name} {version} ({eco}, {age_text(age)} old)"))
    if not young:
        return []

    more = f" and {len(young) - 5} more" if len(young) > 5 else ""
    hint = "; `npm config set min-release-age 7` sets the same limit for every npm install" if any(e == "npm" for e, _ in young) else ""
    return [f"{len(young)} version(s) published less than {limit:g} days ago: {', '.join(t for _, t in young[:5])}{more}. "
            f"Pin an older version or wait{hint}"]


# ---------------------------------------------------------------- lockfiles

def lock_entries(lockfile, text):
    """{(name, version): runs install scripts} for each package a lockfile pins."""
    out = {}
    if not text:
        return out
    if lockfile == "package-lock.json":
        try:
            packages = json.loads(text).get("packages") or {}
        except ValueError:
            return out
        for key, e in packages.items():
            if key and not e.get("link") and e.get("version"):
                out[(e.get("name") or key.rsplit("node_modules/", 1)[-1], e["version"])] = bool(e.get("hasInstallScript"))
    elif lockfile == "pnpm-lock.yaml":
        section, key = "", None
        for line in text.splitlines():
            if line and not line[0].isspace():
                section, key = line.strip().rstrip(":"), None
            elif section == "packages" and (m := re.match(r"^  '?/?((?:@[^/@\s']+/)?[^@/\s']+)[@/]([^(\s':]+)", line)):
                key = (m.group(1), m.group(2))
                out[key] = False
            elif key and line.strip() == "requiresBuild: true":
                out[key] = True
    elif lockfile == "yarn.lock":
        for block in re.split(r"\n\s*\n", text):
            header = next((l for l in block.splitlines() if l and not l.startswith(("#", " "))), "")
            version = re.search(r"^\s+version:?\s+\"?([^\"\s]+)", block, re.M)
            spec = header.split(",")[0].strip().strip('"').rstrip(":")
            if version and "@" in spec[1:] and "workspace:" not in header and not spec.startswith("__metadata"):
                out[(spec[:spec.rindex("@")], version.group(1))] = False
    elif lockfile == "bun.lock":
        for m in re.finditer(r'^\s*"[^"]+":\s*\[\s*"((?:@[^/"@]+/)?[^"@]+)@([^"]+)"', text, re.M):
            if not m.group(2).startswith("workspace:"):
                out[(m.group(1), m.group(2))] = False
    return out


def scripts_disabled():
    try:
        r = subprocess.run(["npm", "config", "get", "ignore-scripts"], capture_output=True, text=True, timeout=5,
                           stdin=subprocess.DEVNULL)
        return r.stdout.strip() == "true"
    except (OSError, subprocess.TimeoutExpired):
        return False


def entry_findings(new):
    """OSV, release age, and install scripts for new npm lockfile entries."""
    items = list(new.items())
    skipped, items = max(0, len(items) - MAX_LOCK_ENTRIES), items[:MAX_LOCK_ENTRIES]
    targets = [("npm", name, version) for (name, version), _ in items]
    findings = osv_findings(targets) + age_findings(targets)

    scripts = [f"{name}@{version}" for (name, version), runs in items if runs]
    if scripts and (findings or not scripts_disabled()):
        more = f" and {len(scripts) - 5} more" if len(scripts) > 5 else ""
        findings.append(f"{len(scripts)} new package(s) run install scripts: {', '.join(scripts[:5])}{more}")
    if findings and skipped:
        findings.append(f"{skipped} more new lockfile entries were not checked")
    return findings


def git_show_head(cwd, path):
    try:
        r = subprocess.run(["git", "show", f"HEAD:./{path}"], cwd=cwd, capture_output=True, text=True, timeout=10,
                           stdin=subprocess.DEVNULL)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return r.stdout if r.returncode == 0 else ""


def command_words(seg):
    w = [x for x in words(seg) if x]
    while w and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", w[0]):
        w = w[1:]
    return w


def lock_install(cmd):
    """The package manager of an install that reads the lockfile and adds no package, or None."""
    for seg in segments(cmd):
        w = command_words(seg)
        if not w or w[0] not in LOCKFILE_OF:
            continue
        tool, sub = w[0], (w[1] if len(w) > 1 else "")
        named = [a for a in w[2:] if not a.startswith("-")]
        if tool == "npm" and (sub == "ci" or sub in ("install", "i") and not named):
            return tool
        if tool in ("pnpm", "bun") and sub in ("install", "i") and not named:
            return tool
        if tool == "yarn" and (not sub or sub.startswith("-") or sub == "install"):
            return tool
    return None


def read_text(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return ""


def lockfile_findings(cwd, manager):
    lockfile = LOCKFILE_OF[manager]
    after = lock_entries(lockfile, read_text(os.path.join(cwd, lockfile)))
    before = lock_entries(lockfile, git_show_head(cwd, lockfile))
    return entry_findings({k: v for k, v in after.items() if k not in before})


def add_command(cmd):
    """(manager, package specs) for `npm install <pkg>` or `pnpm add <pkg>`, else None."""
    for seg in segments(cmd):
        w = command_words(seg)
        if len(w) < 3:
            continue
        specs = [a for a in w[2:] if not a.startswith("-")]
        local = any(s.startswith((".", "/", "~", "git+", "http", "file:")) for s in specs)
        if specs and not local and (w[0] == "npm" and w[1] in ("install", "i", "add") or w[0] == "pnpm" and w[1] == "add"):
            return w[0], specs
    return None


def resolved_entries(cwd, manager, specs):
    """New lockfile entries that adding `specs` would bring in, resolved in a temp copy; None if it cannot run."""
    lockfile = LOCKFILE_OF[manager]
    try:
        with open(os.path.join(cwd, "package.json"), encoding="utf-8") as fh:
            manifest = json.load(fh)
    except (OSError, ValueError):
        return None
    if not shutil.which(manager) or (manager == "npm" and manifest.get("workspaces")):
        return None

    if manager == "npm":
        argv = ["npm", "install", *specs, "--package-lock-only", "--ignore-scripts", "--no-audit", "--no-fund"]
    else:
        argv = ["pnpm", "add", *specs, "--lockfile-only", "--ignore-scripts"]
    with tempfile.TemporaryDirectory() as tmp:
        for name in ("package.json", lockfile, ".npmrc", "pnpm-workspace.yaml"):
            if os.path.isfile(os.path.join(cwd, name)):
                shutil.copy(os.path.join(cwd, name), tmp)
        before = lock_entries(lockfile, read_text(os.path.join(tmp, lockfile)))
        try:
            r = subprocess.run(argv, cwd=tmp, capture_output=True, text=True, timeout=RESOLVE_TIMEOUT_S, stdin=subprocess.DEVNULL)
        except (OSError, subprocess.TimeoutExpired):
            return None
        after = lock_entries(lockfile, read_text(os.path.join(tmp, lockfile)))
    return {k: v for k, v in after.items() if k not in before} if r.returncode == 0 else None


def capped(reasons):
    return reasons if len(reasons) <= 6 else reasons[:5] + [f"{len(reasons) - 5} more findings"]


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
        targets = install_targets(cmd)
        add = add_command(cmd)
        resolved = resolved_entries(cwd, *add) if add else None
        if resolved is not None:
            # the resolved lockfile pins every npm target, so check those through it
            targets = [t for t in targets if t[0] != "npm"]
            reasons += entry_findings(resolved)
        reasons += osv_findings(targets) + age_findings(targets)
        if manager := lock_install(cmd):
            reasons += lockfile_findings(cwd, manager)
    elif tool in ("Edit", "Write"):
        targets = manifest_edit_targets(tool, ti)
        reasons += osv_findings(targets) + age_findings(targets)
    emit(capped(reasons))


if __name__ == "__main__":
    main()
