#!/usr/bin/env python3
"""Rebuild the engineering-blog corpora of the prose-check benchmark from their URL manifests.

usage: bench/prose-check/fetch-blogs.py OUT_DIR [PLATFORM ...]

Each blogs/<platform>.json lists posts published before 2022-11-30 (url, date, title, file) and the
HTML elements that hold the article body. The script downloads each page at one request per second,
keeps the article body as Markdown (headings, paragraphs, list items, quotes, fenced code) and writes
OUT_DIR/<platform>/<file> with YAML front matter. Pages are cached in OUT_DIR/.cache, so a rerun only
fetches what is missing. A page that fails to load is reported and skipped. The posts are copyrighted
by their publishers, so the repo holds only these URL lists.
"""
import argparse
import hashlib
import html.parser
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
USER_AGENT = "prose-bench/0.1 (local text statistics; no redistribution)"
SKIP = {"script", "style", "noscript", "svg", "figure", "figcaption", "button", "nav", "aside", "form", "iframe"}
HEADINGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
BLOCKS = HEADINGS | {"p", "li", "pre", "blockquote", "div", "section", "tr", "ul", "ol", "table"}
VOID = {"br", "img", "hr", "meta", "link", "input", "source", "wbr", "col", "area"}


class ArticleBody(html.parser.HTMLParser):
    """Markdown from the elements that match one of `containers`, given as (tag, class substring) pairs."""

    def __init__(self, containers):
        super().__init__(convert_charrefs=True)
        self.containers = containers
        self.stack, self.buf, self.lines, self.prefix = [], [], [], ""

    def matches(self, tag, attrs):
        cls = dict(attrs).get("class") or ""
        return any(tag == want_tag and want_class in cls for want_tag, want_class in self.containers)

    def skipping(self):
        return any(tag in SKIP for tag in self.stack)

    def flush(self):
        text = "".join(self.buf)
        if "pre" in self.stack:
            if text.strip():
                self.lines.append(f"```\n{text.strip(chr(10))}\n```")
        elif " ".join(text.split()):
            self.lines.append(self.prefix + " ".join(text.split()))
        self.buf, self.prefix = [], ""

    def handle_starttag(self, tag, attrs):
        if tag in VOID:
            if self.stack and tag == "br" and not self.skipping():
                self.buf.append("\n" if "pre" in self.stack else " ")
            return
        if not self.stack:
            if self.matches(tag, attrs):
                self.stack.append(tag)
            return

        self.stack.append(tag)
        if self.skipping():
            return
        if tag in BLOCKS and "pre" not in self.stack[:-1]:
            self.flush()
        if tag in HEADINGS:
            self.prefix = "#" * int(tag[1]) + " "
        elif tag == "li":
            self.prefix = "- "
        elif tag == "blockquote":
            self.prefix = "> "
        elif tag == "code" and "pre" not in self.stack:
            self.buf.append("`")

    def handle_endtag(self, tag):
        if tag in VOID or tag not in self.stack:
            return
        if not self.skipping():
            if tag == "code" and "pre" not in self.stack:
                self.buf.append("`")
            if tag in BLOCKS:
                self.flush()
        while self.stack and self.stack.pop() != tag:
            pass

    def handle_data(self, data):
        if self.stack and not self.skipping():
            self.buf.append(data)

    def markdown(self):
        self.flush()
        return "\n\n".join(self.lines)


def fetch(url, cache):
    path = cache / (hashlib.sha1(url.encode()).hexdigest() + ".html")
    if path.exists():
        return path.read_text(encoding="utf-8", errors="replace"), False

    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        page = response.read().decode("utf-8", "replace")
    path.write_text(page, encoding="utf-8")
    return page, True


def build(platform, out_dir):
    spec = json.loads((HERE / "blogs" / f"{platform}.json").read_text())
    cache = out_dir / ".cache" / platform
    cache.mkdir(parents=True, exist_ok=True)
    target = out_dir / platform
    target.mkdir(parents=True, exist_ok=True)
    containers = [tuple(c) for c in spec["containers"]]

    written = failed = 0
    for post in spec["posts"]:
        try:
            page, fetched = fetch(post["url"], cache)
        except (urllib.error.URLError, TimeoutError) as error:
            print(f"{platform}: skipped {post['url']}: {error}", file=sys.stderr)
            failed += 1
            continue
        if fetched:
            time.sleep(1)

        parser = ArticleBody(containers)
        parser.feed(page)
        body = parser.markdown()
        if not body:
            print(f"{platform}: no article body in {post['url']}", file=sys.stderr)
            failed += 1
            continue

        front = "\n".join(f"{key}: {json.dumps(post[key], ensure_ascii=False)}" for key in ("url", "date", "title"))
        (target / post["file"]).write_text(f"---\n{front}\n---\n\n# {post['title']}\n\n{body}\n", encoding="utf-8")
        written += 1

    print(f"{platform}: {written} written, {failed} skipped")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("out_dir", type=Path)
    parser.add_argument("platforms", nargs="*", help="default: every blogs/*.json")
    args = parser.parse_args()

    platforms = args.platforms or sorted(p.stem for p in (HERE / "blogs").glob("*.json"))
    for platform in platforms:
        build(platform, args.out_dir)


if __name__ == "__main__":
    main()
