#!/usr/bin/env python3
"""Benchmark prose-check on whole corpora: finding rates, per-rule rates, Vale parity, speed, and separation.

usage: scripts/prose-bench.py [--json OUT] [--top N] LABEL=DIR ...

Each DIR holds Markdown files, one document per file. For every corpus it reports words (code and front
matter masked, as the port sees them), findings per 1,000 words from Vale and from the Python port, the
cross-sentence checks, the share of Vale's non-sequence rule findings the port also reports, and seconds per 100,000
words for each engine. Labels that start with "human" or "ai" are paired: the script then reports the
AUC of a per-document score (findings per 100 words), the chance that a random AI document scores above
a random human one. Run it through skills/prose-check/scripts/run.sh's interpreter to include `regex`.
"""
import argparse
import collections
import json
import re
import subprocess
import sys
import time
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "plugins" / "agent-playbook" / "skills" / "prose-check" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import vale_lite  # noqa: E402
import xstring  # noqa: E402

CONFIG = SCRIPTS.parent / "vale.ini"
SEQUENCE = {n for n, r in json.loads((SCRIPTS / "ai-tells.rules.json").read_text())["rules"].items() if r.get("extends") == "sequence"}
WORD = re.compile(r"[A-Za-z0-9']+")


def vale_run(directory):
    start = time.perf_counter()
    out = subprocess.run(["vale", "--config", str(CONFIG), "--output=JSON", str(directory)], capture_output=True, text=True)
    elapsed = time.perf_counter() - start
    found = collections.defaultdict(set)
    for path, alerts in json.loads(out.stdout or "{}").items():
        for alert in alerts:
            found[Path(path).name].add((alert["Line"], alert["Check"].split(".")[-1]))
    return found, elapsed


def port_run(files, rules, ignores):
    start = time.perf_counter()
    found = {f.name: {(line, rule) for line, rule, _, _ in vale_lite.lint(f.read_text(encoding="utf-8", errors="replace"), rules, ignores)} for f in files}
    return found, time.perf_counter() - start


def structure_run(files):
    found = {}
    for f in files:
        report = xstring.check_markdown(f.read_text(encoding="utf-8", errors="replace"))
        found[f.name] = collections.Counter({k: len(v) for k, v in report.items() if v})
    return found


def auc(ai_scores, human_scores):
    """Mann-Whitney AUC: chance a random AI score beats a random human one, ties counted half."""
    ranked = sorted([(s, 1) for s in ai_scores] + [(s, 0) for s in human_scores])
    rank_sum, i = 0.0, 0
    while i < len(ranked):
        j = i
        while j < len(ranked) and ranked[j][0] == ranked[i][0]:
            j += 1
        mean_rank = (i + j + 1) / 2
        rank_sum += mean_rank * sum(1 for k in range(i, j) if ranked[k][1])
        i = j
    n_ai, n_h = len(ai_scores), len(human_scores)
    return (rank_sum - n_ai * (n_ai + 1) / 2) / (n_ai * n_h) if n_ai and n_h else float("nan")


def bench(label, directory, rules, ignores):
    files = sorted(p for p in Path(directory).iterdir() if p.suffix == ".md")
    words = {f.name: len(WORD.findall(vale_lite.prepare(f.read_text(encoding="utf-8", errors="replace"), ignores))) for f in files}
    total_words = sum(words.values()) or 1

    vale, vale_s = vale_run(directory)
    port, port_s = port_run(files, rules, ignores)
    structure = structure_run(files)

    vale_n = sum(len(v) for v in vale.values())
    port_n = sum(len(v) for v in port.values())
    comparable = {n: {f for f in v if f[1] not in SEQUENCE} for n, v in vale.items()}
    both = sum(len(comparable.get(n, set()) & port.get(n, set())) for n in words)
    struct_n = sum(sum(c.values()) for c in structure.values())
    per_rule = collections.Counter(rule for v in vale.values() for _, rule in v)
    per_rule.update({k: n for c in structure.values() for k, n in c.items()})
    scores = {n: 100 * (len(vale.get(n, ())) + sum(structure[n].values())) / max(words[n], 1) for n in words}

    return {
        "label": label, "files": len(files), "words": total_words,
        "vale_per_1k": round(1000 * vale_n / total_words, 2),
        "port_per_1k": round(1000 * port_n / total_words, 2),
        "structure_per_1k": round(1000 * struct_n / total_words, 2),
        "port_parity": round(both / sum(len(v) for v in comparable.values()), 3) if vale_n else 1.0,
        "vale_s_per_100k": round(100_000 * vale_s / total_words, 2),
        "port_s_per_100k": round(100_000 * port_s / total_words, 2),
        "rules_per_1k": {r: round(1000 * n / total_words, 3) for r, n in per_rule.most_common()},
        "scores": scores,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("corpora", nargs="+", metavar="LABEL=DIR")
    parser.add_argument("--json", help="write the full results here")
    parser.add_argument("--top", type=int, default=12, help="rules to list per corpus")
    args = parser.parse_args()

    rules, ignores = vale_lite.load_rules()
    print(f"regex module: {'yes' if vale_lite.fallback_re else 'no'}; port rules loaded: {len(rules)}")
    results = [bench(*item.split("=", 1), rules, ignores) for item in args.corpora]

    print(f"{'corpus':16} {'files':>5} {'words':>8} {'vale/1k':>8} {'port/1k':>8} {'struct/1k':>9} {'parity':>7} {'vale s':>7} {'port s':>7}")
    for r in results:
        print(f"{r['label']:16} {r['files']:5} {r['words']:8} {r['vale_per_1k']:8} {r['port_per_1k']:8} {r['structure_per_1k']:9} "
              f"{r['port_parity']:7.1%} {r['vale_s_per_100k']:7} {r['port_s_per_100k']:7}")
    for r in results:
        top = ", ".join(f"{k} {v}" for k, v in list(r["rules_per_1k"].items())[:args.top])
        print(f"  {r['label']}: {top}")

    human = [s for r in results if r["label"].startswith("human") for s in r["scores"].values()]
    ai = [s for r in results if r["label"].startswith("ai") for s in r["scores"].values()]
    if human and ai:
        print(f"AUC, AI above human (findings per 100 words): {auc(ai, human):.3f}")

    if args.json:
        Path(args.json).write_text(json.dumps([{k: v for k, v in r.items() if k != "scores"} for r in results], indent=1))


if __name__ == "__main__":
    main()
