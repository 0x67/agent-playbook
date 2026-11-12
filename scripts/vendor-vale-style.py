#!/usr/bin/env python3
"""Vendor the pinned vale-ai-tells release into the prose-check skill and regenerate its rule JSON.

usage: scripts/vendor-vale-style.py [--from-dir DIR]

Downloads the release zip named in PIN, replaces skills/prose-check/styles/ai-tells with it, fetches the
repo LICENSE at the same tag, and writes scripts/ai-tells.rules.json, which the Python port (vale_lite.py)
reads so it needs no YAML parser at runtime. --from-dir converts an already extracted style instead of
downloading. Needs PyYAML. After a bump, run scripts/prose-parity.py to compare the port with Vale.
"""
import argparse
import io
import json
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

import yaml

PIN = {"repo": "tbhb/vale-ai-tells", "tag": "v1.37.0", "asset": "ai-tells.zip"}
ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "plugins" / "agent-playbook" / "skills" / "prose-check"
STYLE = SKILL / "styles" / "ai-tells"
RULES_JSON = SKILL / "scripts" / "ai-tells.rules.json"


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "vendor-vale-style"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def download_style():
    base = f"https://github.com/{PIN['repo']}"
    archive = zipfile.ZipFile(io.BytesIO(fetch(f"{base}/releases/download/{PIN['tag']}/{PIN['asset']}")))
    if STYLE.exists():
        shutil.rmtree(STYLE)
    STYLE.mkdir(parents=True)

    for member in archive.namelist():
        name = Path(member).name
        if member.startswith("ai-tells/") and name.endswith(".yml") and "/" not in member[len("ai-tells/"):]:
            (STYLE / name).write_bytes(archive.read(member))

    (STYLE / "LICENSE").write_bytes(fetch(f"https://raw.githubusercontent.com/{PIN['repo']}/{PIN['tag']}/LICENSE"))


def write_rules(style_dir):
    rules = {}
    for path in sorted(Path(style_dir).glob("*.yml")):
        docs = [d for d in yaml.safe_load_all(path.read_text(encoding="utf-8")) if d]
        rules[path.stem] = docs[0]

    payload = {"style": "ai-tells", "source": f"{PIN['repo']}@{PIN['tag']}", "rules": rules}
    RULES_JSON.write_text(json.dumps(payload, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return len(rules)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--from-dir", help="convert this extracted style folder instead of downloading")
    args = parser.parse_args()

    if not args.from_dir:
        download_style()
    count = write_rules(args.from_dir or STYLE)
    print(f"{count} rules from {PIN['repo']}@{PIN['tag']} -> {RULES_JSON.relative_to(ROOT)}")


if __name__ == "__main__":
    sys.exit(main())
