#!/usr/bin/env python3
"""Compare the prose-check Python port (vale_lite.py) with Vale on the same files.

usage: scripts/prose-parity.py FILE...

Prints the findings each engine reports that the other does not, by (line, rule), and the share of Vale's
findings the port also reports. Sequence rules are left out, since the port does not run them. Exit 1 when
that share is below 90%.
"""
import json
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "plugins" / "agent-playbook" / "skills" / "prose-check" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import vale_lite  # noqa: E402

CONFIG = SCRIPTS.parent / "vale.ini"


def vale(path, skip):
    out = subprocess.run(["vale", "--config", str(CONFIG), "--output=JSON", str(path)], capture_output=True, text=True)
    found = set()
    for alerts in json.loads(out.stdout or "{}").values():
        for alert in alerts:
            rule = alert["Check"].split(".")[-1]
            if rule not in skip:
                found.add((alert["Line"], rule))
    return found


def main():
    spec = json.loads((SCRIPTS / "ai-tells.rules.json").read_text())["rules"]
    skip = {name for name, rule in spec.items() if rule.get("extends") == "sequence"}
    rules, ignores = vale_lite.load_rules()

    shared = vale_total = 0
    for name in sys.argv[1:]:
        path = Path(name)
        expected = vale(path, skip)
        got = {(line, rule) for line, rule, _, _ in vale_lite.lint(path.read_text(encoding="utf-8"), rules, ignores)}
        shared += len(expected & got)
        vale_total += len(expected)
        print(f"== {path.name}: vale {len(expected)}, port {len(got)}, both {len(expected & got)}")
        for line, rule in sorted(expected - got):
            print(f"   only vale  L{line} {rule}")
        for line, rule in sorted(got - expected):
            print(f"   only port  L{line} {rule}")

    share = shared / vale_total if vale_total else 1.0
    print(f"port reports {share:.0%} of Vale's findings")
    sys.exit(0 if share >= 0.9 else 1)


if __name__ == "__main__":
    main()
