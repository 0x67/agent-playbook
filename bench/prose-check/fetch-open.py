#!/usr/bin/env python3
"""Rebuild the openly licensed corpora of the prose-check benchmark from pinned sources.

usage: bench/prose-check/fetch-open.py OUT_DIR

Writes, one Markdown file per document:
  OUT_DIR/human/rust-book   The Rust Programming Language, last commit of 2021 (MIT or Apache-2.0)
  OUT_DIR/human/go-blog     The Go blog, last commit of 2021 (CC BY 4.0)
  OUT_DIR/hc3/human         HC3 human answers (CC BY-SA 4.0)
  OUT_DIR/hc3/chatgpt       HC3 ChatGPT answers to the same 1,500 questions
  OUT_DIR/fixtures/{positive,negative}  vale-ai-tells v1.37.0 test documents (MIT)
HC3 answers are detokenized ("n't", spaces before punctuation) so word-level rules see normal text.
"""
import hashlib
import io
import json
import random
import re
import sys
import tarfile
import urllib.request
from pathlib import Path

USER_AGENT = "prose-bench/0.1 (local text statistics; no redistribution)"
TARBALLS = {
    "human/rust-book": ("rust-lang/book", "15aef431579a3d2f2bac8cc25445ece1c8e9808c", r"^[^/]+/src/[^/]+\.md$"),
    "human/go-blog": ("golang/website", "f07bd53eacd2d2fce298fb0ea31be6c21f477159", r"^[^/]+/_content/blog/[^/]+\.md$"),
}
HC3 = {
    "url": "https://huggingface.co/datasets/Hello-SimpleAI/HC3/resolve/4d0ff18143b5a7e1b1e79beb540c04549d1e59d3/all.jsonl",
    "sha256": "ee231f82283d754050a4dc58ecf9331afaf5daea7283c6da0b096ed0fb2774cf",
    "pairs": 1500, "seed": 13, "min_words": 60,
}
FIXTURES = {
    "fixtures/positive/ai-tells-positive.md": "https://raw.githubusercontent.com/tbhb/vale-ai-tells/v1.37.0/test-document.md",
    "fixtures/negative/ai-tells-negative.md": "https://raw.githubusercontent.com/tbhb/vale-ai-tells/v1.37.0/test-false-positives.md",
}


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=300) as response:
        return response.read()


def unpack(repo, sha, pattern, dest):
    dest.mkdir(parents=True, exist_ok=True)
    count = 0
    with tarfile.open(fileobj=io.BytesIO(fetch(f"https://codeload.github.com/{repo}/tar.gz/{sha}"))) as tar:
        for member in tar.getmembers():
            if member.isfile() and re.match(pattern, member.name):
                (dest / Path(member.name).name).write_bytes(tar.extractfile(member).read())
                count += 1
    return count


def detokenize(text):
    text = re.sub(r"\s+(n't|'s|'re|'ve|'ll|'d|'m)\b", r"\1", text)
    text = re.sub(r"\s+([.,;:!?%)\]])", r"\1", text)
    text = re.sub(r"([(\[$])\s+", r"\1", text)
    text = re.sub(r'"\s+([^"]*?)\s+"', r'"\1"', text)
    return re.sub(r"[ \t]+", " ", text).strip()


def build_hc3(out):
    raw = fetch(HC3["url"])
    if hashlib.sha256(raw).hexdigest() != HC3["sha256"]:
        sys.exit("HC3 all.jsonl does not match the pinned checksum")

    pairs = []
    for line in raw.decode("utf-8").splitlines():
        row = json.loads(line)
        human = [t for t in (detokenize(a) for a in row.get("human_answers") or [] if a) if len(t.split()) >= HC3["min_words"]]
        machine = [t for t in (detokenize(a) for a in row.get("chatgpt_answers") or [] if a) if len(t.split()) >= HC3["min_words"]]
        if human and machine:
            pairs.append((row.get("source", "unknown"), human[0], machine[0]))

    random.seed(HC3["seed"])
    random.shuffle(pairs)
    for side in ("human", "chatgpt"):
        (out / "hc3" / side).mkdir(parents=True, exist_ok=True)
    for i, (source, human, machine) in enumerate(pairs[:HC3["pairs"]]):
        (out / f"hc3/human/{source}-{i:04d}.md").write_text(human + "\n", encoding="utf-8")
        (out / f"hc3/chatgpt/{source}-{i:04d}.md").write_text(machine + "\n", encoding="utf-8")
    return min(len(pairs), HC3["pairs"])


def main():
    out = Path(sys.argv[1])
    for name, (repo, sha, pattern) in TARBALLS.items():
        print(f"{name}: {unpack(repo, sha, pattern, out / name)} files from {repo}@{sha[:7]}")
    print(f"hc3: {build_hc3(out)} answer pairs")
    for name, url in FIXTURES.items():
        (out / name).parent.mkdir(parents=True, exist_ok=True)
        (out / name).write_bytes(fetch(url))
    print(f"fixtures: {len(FIXTURES)} files")


if __name__ == "__main__":
    main()
