#!/usr/bin/env python3
"""Copy pinned third-party skills into plugins/vetted-skills after a SkillSpector scan.

usage: scripts/vendor-skills.py [--bump] [--only NAME ...]

Each entry in scripts/vendor-skills.json names a GitHub repo, the skill folder inside it, and the
commit to take it from. The script downloads that commit, scans the folder with
`skillspector scan --no-llm`, and replaces plugins/vetted-skills/skills/<name> only when the scan
recommends SAFE, or when the entry's `accepted` block records a review of the same commit at the
same or a higher severity. --bump moves each pin to the head of the repo's default branch first,
so a bumped entry that relies on `accepted` fails until someone reviews the new commit.
Downloaded files are only extracted and scanned, never run.
"""
import argparse
import io
import json
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PINS = ROOT / "scripts" / "vendor-skills.json"
DEST = ROOT / "plugins" / "vetted-skills" / "skills"
SEVERITY = ["NONE", "INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
# claude.ai drops other frontmatter keys and strips angle brackets from descriptions
CLAUDE_AI_KEYS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "vendor-skills"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def head_sha(repo):
    branch = json.loads(fetch(f"https://api.github.com/repos/{repo}"))["default_branch"]
    return json.loads(fetch(f"https://api.github.com/repos/{repo}/commits/{branch}"))["sha"]


def download(repo, sha, path, into):
    archive = fetch(f"https://codeload.github.com/{repo}/tar.gz/{sha}")
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(into, filter="data")

    top = next(into.iterdir())
    skill = top / path
    if not (skill / "SKILL.md").is_file():
        raise RuntimeError(f"{repo}@{sha[:7]} has no {path}/SKILL.md")

    return top, skill


def add_license(top, stage):
    if any(stage.glob("LICENSE*")):
        return True

    for candidate in sorted(top.glob("LICENSE*")):
        shutil.copy(candidate, stage / candidate.name)
        return True

    return False


def scan(folder, workdir):
    report = workdir / "report.json"
    # skillspector exits non-zero for risky skills, so the report decides, not the exit code
    subprocess.run(
        ["skillspector", "scan", str(folder), "--no-llm", "--format", "json", "--output", str(report)],
        capture_output=True, text=True, timeout=600, stdin=subprocess.DEVNULL,
    )
    assessment = json.loads(report.read_text()).get("risk_assessment") or {}
    return assessment.get("severity", "UNKNOWN"), assessment.get("recommendation", "UNKNOWN")


def verdict(entry, sha, severity, recommendation):
    if recommendation == "SAFE":
        return True, f"{severity}/SAFE"

    accepted = entry.get("accepted") or {}
    ceiling = accepted.get("severity", "NONE")
    if accepted.get("sha") == sha and severity in SEVERITY and SEVERITY.index(severity) <= SEVERITY.index(ceiling):
        return True, f"{severity}/{recommendation}, accepted on {accepted.get('reviewed')}"

    return False, f"{severity}/{recommendation}, needs a human review"


def frontmatter(skill):
    text = (skill / "SKILL.md").read_text()
    match = re.match(r"---\n(.*?)\n---\n", text, re.S)
    return match.group(1) if match else ""


def lint(skill, name):
    header = frontmatter(skill)
    keys = re.findall(r"^([A-Za-z_-]+):", header, re.M)
    block = re.search(r"^description:[ \t]*[>|]?-?[ \t]*\n?((?:.*\n?)*?)(?=^\S|\Z)", header, re.M)
    description = " ".join(block.group(1).split()) if block else ""
    named = re.search(r"^name:\s*(\S+)", header, re.M)

    warnings = []
    if extra := sorted(set(keys) - CLAUDE_AI_KEYS):
        warnings.append(f"frontmatter keys claude.ai ignores: {', '.join(extra)}")
    if len(description) > 1024:
        warnings.append(f"description is {len(description)} characters, over 1024")
    if re.search(r"[<>]", description):
        warnings.append("description has angle brackets")
    if not named or named.group(1) != name:
        warnings.append(f"name does not match the folder name {name}")

    return warnings


def vendor(entry, bump):
    sha = head_sha(entry["repo"]) if bump else entry["sha"]

    with tempfile.TemporaryDirectory() as tmp:
        workdir = Path(tmp)
        (workdir / "src").mkdir()
        top, skill = download(entry["repo"], sha, entry["path"], workdir / "src")

        stage = workdir / entry["name"]
        shutil.copytree(skill, stage)
        licensed = add_license(top, stage)

        severity, recommendation = scan(stage, workdir)
        passed, reason = verdict(entry, sha, severity, recommendation)
        print(f"{entry['name']:20} {sha[:7]}  {reason}")
        if not licensed:
            print("  no LICENSE file in the skill folder or at the repo root")
        for warning in lint(stage, entry["name"]):
            print(f"  claude.ai: {warning}")

        if not passed:
            return False

        target = DEST / entry["name"]
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(stage, target)
        entry["sha"] = sha

    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--bump", action="store_true", help="move each pin to the default branch head first")
    parser.add_argument("--only", nargs="+", metavar="NAME", help="vendor only these skills")
    args = parser.parse_args()

    if not shutil.which("skillspector"):
        sys.exit("skillspector is not on PATH")

    pins = json.loads(PINS.read_text())
    failed = []
    for entry in pins:
        if args.only and entry["name"] not in args.only:
            continue
        try:
            passed = vendor(entry, args.bump)
        except Exception as error:
            print(f"{entry['name']:20} error: {error}")
            passed = False
        if not passed:
            failed.append(entry["name"])

    PINS.write_text(json.dumps(pins, indent=2) + "\n")
    if failed:
        sys.exit(f"not vendored: {', '.join(failed)}")


if __name__ == "__main__":
    main()
