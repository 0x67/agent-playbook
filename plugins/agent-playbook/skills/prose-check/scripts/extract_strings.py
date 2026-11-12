#!/usr/bin/env python3
"""Extract user-facing strings from HTML, JSX/TSX, Vue and Svelte files.

usage: extract_strings.py FILE  (prints "L<line> UI| <text>" per string, the format xstring.py reads)

HTML goes through html.parser: text nodes outside script and style, plus placeholder, title, aria-label
and alt. Component files use patterns: text between tags, those same attributes, and string literals
passed to t() or toast(). Template expressions are kept as {x} so sentence shape survives.
"""
import html.parser
import re
import sys
from pathlib import Path

ATTRIBUTES = ("placeholder", "title", "aria-label", "alt", "label")
COMPONENT_TEXT = re.compile(r">([^<>]*[A-Za-z][^<>]*)<")
COMPONENT_ATTR = re.compile(r"\b(?:%s)=[\"']([^\"'{}]*[A-Za-z][^\"'{}]*)[\"']" % "|".join(ATTRIBUTES))
CALL_LITERAL = re.compile(r"\b(?:t|i18n\.t|toast(?:\.\w+)?)\(\s*([\"'`])((?:(?!\1).)*[A-Za-z](?:(?!\1).)*)\1")
CODE_LIKE = re.compile(r"[;=]|=>|\)\s*\{|^\s*[\w.]+\(|^\s*(?:const|let|var|return|import|export)\b")


def tidy(text):
    text = re.sub(r"\{\{?[^{}]*\}?\}", "{x}", text)
    return re.sub(r"\s+", " ", text).strip()


class HtmlStrings(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.found, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
        for name, value in attrs:
            if name in ATTRIBUTES and value and re.search("[A-Za-z]", value):
                self.found.append((self.getpos()[0], tidy(value)))

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        text = tidy(data)
        if not self.skip and re.search("[A-Za-z]{2}", text):
            self.found.append((self.getpos()[0], text))


def line_at(text, offset):
    return text.count("\n", 0, offset) + 1


def from_components(text):
    found = []
    for pattern, group in ((COMPONENT_TEXT, 1), (COMPONENT_ATTR, 1), (CALL_LITERAL, 2)):
        for match in pattern.finditer(text):
            value = tidy(match.group(group))
            if value and not CODE_LIKE.search(value) and re.search("[A-Za-z]{2}", value):
                found.append((line_at(text, match.start(group)), value))
    return found


def extract(path):
    """Return [(line, text)] in file order, without duplicates on the same line."""
    path = Path(path)
    text = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() in (".html", ".htm"):
        parser = HtmlStrings()
        parser.feed(text)
        found = parser.found
    else:
        found = from_components(text)
    return sorted(set(found))


if __name__ == "__main__":
    for line, value in extract(sys.argv[1]):
        print(f"L{line} UI| {value}")
