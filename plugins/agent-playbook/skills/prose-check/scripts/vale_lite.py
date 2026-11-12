#!/usr/bin/env python3
"""Run a Vale style's existence, substitution and occurrence rules without Vale.

Reads ai-tells.rules.json (generated from the vendored YAML by scripts/vendor-vale-style.py) and the rule
levels, MinAlertLevel and TokenIgnores from ../vale.ini. Sequence rules need Vale's part-of-speech tagger
and are skipped, as are patterns Python's re cannot compile (variable-width lookbehind).
"""
import json
import re
from pathlib import Path

try:
    import regex as fallback_re
except ImportError:
    fallback_re = None

HERE = Path(__file__).resolve().parent
RULES = HERE / "ai-tells.rules.json"
CONFIG = HERE.parent / "vale.ini"
RANK = {"suggestion": 0, "warning": 1, "error": 2}


def parens_groups(value):
    """Split a TokenIgnores value like "(a), (b)" into its top-level groups."""
    groups, depth, start, escaped = [], 0, None, False
    for i, ch in enumerate(value):
        if escaped:
            escaped = False
        elif ch == "\\":
            escaped = True
        elif ch == "(":
            depth += 1
            start = i if depth == 1 else start
        elif ch == ")":
            depth -= 1
            if depth == 0 and start is not None:
                groups.append(value[start:i + 1])
    return groups


def load_config(path=CONFIG, style="ai-tells"):
    min_level, levels, ignores = "suggestion", {}, []
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith(("#", "[")) or "=" not in line:
            continue
        key, value = (part.strip() for part in line.split("=", 1))
        if key == "MinAlertLevel":
            min_level = value
        elif key == "TokenIgnores":
            ignores = [re.compile(g) for g in parens_groups(value)]
        elif key.startswith(style + "."):
            levels[key.split(".", 1)[1]] = value
    return min_level, levels, ignores


def closing(pattern, start):
    """Index of the parenthesis that closes the group opened at start."""
    depth, i = 0, start
    while i < len(pattern):
        ch = pattern[i]
        if ch == "\\":
            i += 2
            continue
        depth += ch == "("
        depth -= ch == ")"
        if depth == 0:
            return i
        i += 1
    return -1


def top_level_split(body):
    parts, depth, last, i = [], 0, 0, 0
    while i < len(body):
        ch = body[i]
        if ch == "\\":
            i += 2
            continue
        depth += ch == "("
        depth -= ch == ")"
        if ch == "|" and depth == 0:
            parts.append(body[last:i])
            last = i + 1
        i += 1
    return parts + [body[last:]]


def expand_lookbehinds(pattern):
    """Rewrite (?<!a|bb) and (?<=x(?:a|bb)y) into fixed-width lookbehinds Python's re accepts."""
    out, i = [], 0
    while i < len(pattern):
        if pattern.startswith(("(?<=", "(?<!"), i):
            end = closing(pattern, i)
            body, negative = pattern[i + 4:end], pattern[i + 3] == "!"
            alts = top_level_split(body)
            if len(alts) == 1 and "(?:" in body:
                g = body.index("(?:")
                g_end = closing(body, g)
                prefix, suffix = body[:g], body[g_end + 1:]
                if "(" not in prefix and not suffix[:1] in ("?", "*", "+", "{"):
                    alts = [prefix + alt + suffix for alt in top_level_split(body[g + 3:g_end])]
            parts = [f"(?<{'!' if negative else '='}{alt})" for alt in alts]
            out.append("".join(parts) if negative else "(?:" + "|".join(parts) + ")")
            i = end + 1
        else:
            out.append(pattern[i])
            i += 1
    return "".join(out)


def compile_one(pattern, flags):
    for candidate in (pattern, expand_lookbehinds(pattern)):
        try:
            return re.compile(candidate, flags)
        except re.error:
            pass
    if fallback_re:
        try:
            return fallback_re.compile(pattern, flags)
        except Exception:
            pass
    return None


def wrap(pattern, nonword):
    return f"(?:{pattern})" if nonword else rf"\b(?:{pattern})\b"


def compile_tokens(tokens, nonword, flags):
    tokens = [t for t in tokens if isinstance(t, str)]
    joined = compile_one(wrap("|".join(tokens), nonword), flags) if tokens else None
    if joined:
        return [joined]
    compiled = (compile_one(wrap(token, nonword), flags) for token in tokens)
    return [c for c in compiled if c]


class Rule:
    def __init__(self, name, spec, level):
        self.name, self.level, self.kind = name, level, spec["extends"]
        self.message = spec.get("message", name)
        self.scope = spec.get("scope") or ("paragraph" if self.kind == "occurrence" else "text")
        flags = re.I if spec.get("ignorecase") else 0
        nonword = bool(spec.get("nonword"))

        self.patterns, self.swaps, self.maximum = [], [], spec.get("max", 0)
        if self.kind == "existence":
            self.patterns = compile_tokens(spec.get("tokens") or [], nonword, flags)
        elif self.kind == "substitution":
            for key, replacement in (spec.get("swap") or {}).items():
                for pattern in compile_tokens([key], nonword, flags):
                    self.swaps.append((pattern, replacement if isinstance(replacement, str) else str(replacement)))
        elif self.kind == "occurrence":
            self.patterns = compile_tokens([spec["token"]], True, flags)

        exceptions = spec.get("exceptions") or []
        self.exceptions = compile_tokens(exceptions, True, flags) if exceptions else []

    def usable(self):
        return bool(self.patterns or self.swaps)

    def excepted(self, text):
        # Vale drops a match when any exception pattern occurs inside it, not only when it covers it all
        return any(p.search(text) for p in self.exceptions)

    def run(self, block):
        """Yield (offset, message) for one block of text."""
        if self.kind == "occurrence":
            count = sum(len(p.findall(block)) for p in self.patterns)
            if count > self.maximum:
                yield 0, self.message.replace("%d", str(count))
            return

        if self.kind == "substitution":
            for pattern, replacement in self.swaps:
                for match in pattern.finditer(block):
                    if not self.excepted(match.group(0)):
                        yield match.start(), self.message.replace("%s", replacement, 1).replace("%s", match.group(0), 1)
            return

        for pattern in self.patterns:
            for match in pattern.finditer(block):
                if match.group(0).strip() and not self.excepted(match.group(0)):
                    yield match.start(), self.message.replace("%s", match.group(0), 1)


def load_rules():
    min_level, levels, ignores = load_config()
    floor = RANK.get(min_level, 0)
    rules = []
    for name, spec in json.loads(RULES.read_text(encoding="utf-8"))["rules"].items():
        level = levels.get(name, spec.get("level", "warning"))
        if level.upper() == "NO" or spec.get("extends") not in ("existence", "substitution", "occurrence"):
            continue
        if RANK.get(level, 0) >= floor:
            rule = Rule(name, spec, level)
            if rule.usable():
                rules.append(rule)
    return rules, ignores


def blank(match):
    return re.sub(r"[^\n]", " ", match.group(0))


def prepare(text, ignores):
    """Mask what Vale skips (front matter, code, URLs, tags, ignored tokens) while keeping every offset and line."""
    text = re.sub(r"\A---\n.*?\n---[ \t]*\n", blank, text, flags=re.S)
    text = re.sub(r"(?s)<!--.*?-->", blank, text)
    text = re.sub(r"(?ms)^(```|~~~).*?^\1[^\n]*$", blank, text)
    text = re.sub(r"(?m)(?<=\n\n)(?:(?:\t| {4})[^\n]*(?:\n|$))+", blank, text)
    text = re.sub(r"`[^`\n]+`", blank, text)
    text = re.sub(r"\]\([^)\s]+\)", blank, text)
    text = re.sub(r"https?://\S+", blank, text)
    text = re.sub(r"<[^>\n]+>", blank, text)
    text = re.sub(r"(?m)^[ \t]*\|?(?:[ \t]*:?-{2,}:?[ \t]*\|)+[ \t]*:?-*:?[ \t]*$", blank, text)
    text = re.sub(r"(?m)^[ \t]*(?:-{3,}|\*{3,}|_{3,})[ \t]*$", blank, text)
    for pattern in ignores:
        text = pattern.sub(blank, text)
    return text


def blocks(text, scope):
    """Yield (start offset, block text) for the scope: paragraphs, headings, or the whole raw text."""
    if scope == "raw":
        yield 0, text
        return
    for match in re.finditer(r"(?:[^\n]+\n?)+", text):
        block = match.group(0)
        is_heading = block.lstrip().startswith("#")
        if scope == "heading" and not is_heading:
            continue
        flat = re.sub(r"(?m)^[ \t]*(?:#{1,6}|[-*+]|\d+[.)]|>)[ \t]+", lambda m: " " * len(m.group(0)), block)
        yield match.start(), flat.replace("\n", " ").replace("|", " ")


def lint(text, rules=None, ignores=None):
    """Return sorted (line, rule, message, level) findings for Markdown or plain text."""
    if rules is None:
        rules, ignores = load_rules()
    masked = prepare(text, ignores or [])
    line_starts = [0] + [m.end() for m in re.finditer("\n", masked)]

    def line_of(offset):
        low, high = 0, len(line_starts) - 1
        while low < high:
            mid = (low + high + 1) // 2
            low, high = (mid, high) if line_starts[mid] <= offset else (low, mid - 1)
        return low + 1

    findings = set()
    for rule in rules:
        for start, block in blocks(masked, rule.scope):
            for offset, message in rule.run(block):
                findings.add((line_of(start + offset), rule.name, message, rule.level))
    return sorted(findings)


if __name__ == "__main__":
    import sys

    for path in sys.argv[1:]:
        for line, rule, message, level in lint(Path(path).read_text(encoding="utf-8")):
            print(f"{path}:{line} {rule} [{level}] {message[:140]}")
