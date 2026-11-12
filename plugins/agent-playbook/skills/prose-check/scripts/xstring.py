#!/usr/bin/env python3
"""Flag AI-like structure that per-sentence linters miss: patterns repeated across strings or sentences.

usage: xstring.py [--strings FILE] [--markdown FILE] [--min N] [--json]

--strings takes one UI string per line; a leading "L123 UI| " prefix is stripped.
--markdown takes a Markdown document; code blocks, headings and table rows are skipped.
Exit 1 when anything is flagged, 0 when clean.
"""
import argparse
import collections
import json
import re
import statistics
import sys

PREFIX = re.compile(r"^L\d+\s+\w+\|\s?")
SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'`(])")
WORD = re.compile(r"[A-Za-z0-9']+")
CONTRAST = [
    re.compile(r"\bnot\b[^.;]{1,60}\bbut\b", re.I),
    re.compile(r",\s+not\s+[a-z][^.]{0,40}\.$"),
    re.compile(r"\b(it|this|that)\s+(is|was)\s*n[o']t\b[^.]*\.\s+(it|this|that)\b", re.I),
]
COLON_LABEL = re.compile(r"^([A-Z][\w-]*(?:\s[\w-]+){0,2}):\s+(\S+(?:\s+\S+){3,})")
DATA_LABELS = {
    "column", "columns", "default", "defaults", "example", "examples", "field", "fields", "file", "files",
    "input", "note", "notes", "output", "prototype", "see", "source", "sources", "table", "tables", "usage",
}


def sentences(text):
    return [s.strip() for s in SENTENCE_END.split(text.strip()) if s.strip()]


def words(sentence):
    return [w.lower() for w in WORD.findall(sentence)]


def colon_reveal(sentence):
    """A short label, a colon, then a full sentence ("Draft: these bars are set aside"). Data labels and lists pass."""
    match = COLON_LABEL.match(sentence)
    if not match:
        return False

    label, rest = match.group(1), match.group(2)
    head = rest.split(". ")[0]
    is_list = head.count(",") >= 2 and len(head.split()) <= 3 * head.count(",")
    return label.lower() not in DATA_LABELS and "http" not in rest and not is_list


def contrast(sentence):
    return any(p.search(sentence) for p in CONTRAST)


def clusters(keyed, minimum):
    groups = collections.defaultdict(list)
    for key, source in keyed:
        if key:
            groups[key].append(source)
    return {k: v for k, v in groups.items() if len(v) >= minimum}


def check_strings(lines, minimum=3):
    strings = [PREFIX.sub("", line).strip() for line in lines]
    strings = [s for s in strings if len(words(s)) >= 3]
    sents = [(s, sn) for s in strings for sn in sentences(s)]
    long_sents = [(s, sn) for s, sn in sents if len(words(sn)) >= 4]

    shapes = collections.Counter(
        tuple(min(len(words(sn)) // 4, 3) for sn in sentences(s)) for s in strings if len(sentences(s)) >= 2
    )
    return {
        "repeated_openings": clusters(((" ".join(words(sn)[:2]), sn) for _, sn in long_sents), minimum),
        "repeated_endings": clusters(((" ".join(words(sn)[-3:]), sn) for _, sn in long_sents), minimum),
        "repeated_sentences": clusters(((" ".join(words(sn)), s) for s, sn in sents if len(words(sn)) >= 3), minimum),
        "same_sentence_shape": {str(k): n for k, n in shapes.items() if n >= minimum * 2},
        "colon_reveals": [s for s in strings if colon_reveal(s)],
        "contrasts": [sn for _, sn in sents if contrast(sn)],
    }


def paragraphs(markdown):
    text = re.sub(r"```.*?```", "", markdown, flags=re.S)
    blocks = []
    for block in re.split(r"\n\s*\n", text):
        lines = [ln for ln in block.splitlines() if ln.strip() and not ln.lstrip().startswith(("|", "#"))]
        if lines:
            blocks.append(" ".join(re.sub(r"^\s*(?:[-*]|\d+\.)\s+", "", ln) for ln in lines))
    return [re.sub(r"[*_`]", "", b) for b in blocks]


def check_markdown(markdown, minimum=3):
    found = collections.defaultdict(list)
    all_sents = []
    for para in paragraphs(markdown):
        sents = sentences(para)
        all_sents += sents
        lengths = [len(words(s)) for s in sents]

        if len(lengths) >= 4 and statistics.mean(lengths) > 0:
            spread = statistics.pstdev(lengths) / statistics.mean(lengths)
            if spread < 0.25:
                found["flat_rhythm"].append(sents[0])

        firsts = [words(s)[0] if words(s) else "" for s in sents]
        for i in range(len(firsts) - 2):
            if firsts[i] and firsts[i] == firsts[i + 1] == firsts[i + 2]:
                found["anaphora_runs"].append(sents[i])
                break

        if len(lengths) >= 3 and lengths[-1] <= 6 and lengths[-1] < statistics.mean(lengths[:-1]) / 2:
            found["short_closers"].append(sents[-1])

        found["contrasts"] += [s for s in sents if contrast(s)]
        found["colon_reveals"] += [s for s in sents if colon_reveal(s)]

    openings = clusters(((" ".join(words(s)[:2]), s) for s in all_sents if len(words(s)) >= 4), minimum + 1)
    found["repeated_openings"] = openings
    return dict(found)


def total(report):
    return sum(len(v) for findings in report.values() for v in findings.values())


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--strings")
    parser.add_argument("--markdown")
    parser.add_argument("--min", type=int, default=3, help="smallest cluster to report (default 3)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = {}
    if args.strings:
        with open(args.strings, encoding="utf-8") as fh:
            report["strings"] = check_strings(fh.read().splitlines(), args.min)
    if args.markdown:
        with open(args.markdown, encoding="utf-8") as fh:
            report["markdown"] = check_markdown(fh.read(), args.min)

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        for source, findings in report.items():
            print(f"== {source}")
            for name, value in findings.items():
                if not value:
                    continue
                print(f"-- {name} ({len(value)})")
                items = value.items() if isinstance(value, dict) else enumerate(value)
                for key, item in list(items)[:8]:
                    if isinstance(item, list):
                        print(f"   {key!r} x{len(item)}: {item[0][:90]!r}")
                    elif isinstance(item, int):
                        print(f"   sentence-length shape {key} x{item}")
                    else:
                        print(f"   {str(item)[:140]}")

    sys.exit(1 if total(report) else 0)


if __name__ == "__main__":
    main()
