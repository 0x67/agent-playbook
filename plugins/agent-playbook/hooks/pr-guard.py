#!/usr/bin/env python3
"""PreToolUse (Bash) hook: ask before a PR or a stack layer goes out too large or breaks the naming rules.

`gh pr create`:
1. Size: lines changed against the PR base, with lockfiles left out and renames counted by their edits.
   Over AGENT_PLAYBOOK_PR_MAX_LINES (default 400, 0 turns it off), asks to split the work into stacked PRs.
2. Title: a `--title` that is not a Conventional Commits header, runs past 72 characters, ends with a
   period, or carries a stack position such as `[2/3]` or `Part 2`.
3. Branch: a head branch outside `<type>/<slug>`, unless most remote branches use another pattern,
   or a branch name with a stack position such as `part-2`.

GitHub's `gh stack` extension (github/gh-stack):
4. `init` and `add`: each new branch name gets the branch check. A missing name asks too: `add -m`
   then generates an `MM-DD-slug` name, and a bare `init` or `add` prompts for one.
5. `submit`: each layer from `gh stack view --json` gets the size check against the layer below it and
   the branch check. A layer with no PR asks, since submit would open it with a generated title and a
   footer. A missing `--auto` asks, since the bare command opens a full-screen editor.
6. `link`: a branch argument with no open PR asks, since link would open one with a generated title.

Findings become a permission prompt (permissionDecision "ask"). A git or gh error, or an unparsable command,
skips that check. Stacking rules: skills/conventional-commits/references/stacked-prs.md.
"""
import glob
import json
import os
import re
import shlex
import subprocess
import sys

DEFAULT_MAX_LINES = 400
MAX_TITLE = 72
TYPES = "feat|fix|perf|refactor|test|docs|build|ci|chore|revert|style"
HEADER = re.compile(r"^[a-z]+(\([a-z0-9][a-z0-9._/,-]*\))?!?: \S")
KNOWN_TYPE = re.compile(rf"^({TYPES})[(!:]")
TITLE_STACK_MARK = re.compile(r"[\[(]\s*\d+\s*/\s*\d+\s*[\])]|\bpart\s*\d+\b", re.I)
TYPE_BRANCH = re.compile(rf"^({TYPES})/[a-z0-9][a-z0-9._/-]*$")
BRANCH_STACK_MARK = re.compile(r"(^|[/_-])(part|stack)[-_]?\d+($|[/_-])", re.I)
TRUNKS = {"main", "master", "develop", "trunk", "HEAD"}
LOCKFILES = {
    "package-lock.json", "npm-shrinkwrap.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock", "bun.lockb",
    "Cargo.lock", "go.sum", "uv.lock", "poetry.lock", "Pipfile.lock", "Gemfile.lock", "composer.lock",
    "gradle.lockfile", "flake.lock",
}
FLAGS = {"--title": "title", "-t": "title", "--base": "base", "-B": "base", "--head": "head", "-H": "head"}
SEPARATORS = set("();<>|&")
ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
PR_REF = re.compile(r"^(\d+|https?://\S+/pull/\d+\S*)$")
# gh stack flags that take a value, per subcommand (cmd/*.go in github/gh-stack v0.3.0)
STACK_VALUE_FLAGS = {
    "init": {"-b", "--base"},
    "add": {"-m", "--message"},
    "submit": {"--remote"},
    "link": {"--base", "--remote"},
}


def emit(reasons):
    if reasons:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": " | ".join(reasons),
        }}))


def run(cwd, argv):
    try:
        r = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=10, stdin=subprocess.DEVNULL)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def git(cwd, *args):
    return run(cwd, ["git", *args])


def gh(cwd, *args):
    return run(cwd, ["gh", *args])


def remote_of(cwd, branch):
    return git(cwd, "config", f"branch.{branch}.remote") or "origin"


# ---------------------------------------------------------------- command parsing

def tokens(cmd):
    """Shell words with operators as separate tokens; a heredoc after the flags is cut off when it breaks quoting."""
    for text in (cmd, cmd.split("<<", 1)[0]):
        try:
            lexer = shlex.shlex(text, posix=True, punctuation_chars=True)
            lexer.whitespace_split = True
            return list(lexer)
        except ValueError:
            continue
    return None


def commands(cmd):
    """Words of each simple command in a shell line, without leading VAR=value assignments."""
    words = tokens(cmd)
    if not words:
        return []

    found, current = [], []
    for word in words + [";"]:
        if word and set(word) <= SEPARATORS:
            while current and ASSIGNMENT.match(current[0]):
                current.pop(0)
            if current:
                found.append(current)
            current = []
        else:
            current.append(word)
    return found


def parse_flags(args):
    """The `gh pr create` flags this hook reads; other flags and their values are skipped."""
    values, i = {}, 0
    while i < len(args):
        arg = args[i]
        name, eq, inline = arg.partition("=")
        if eq and name in FLAGS:
            values[FLAGS[name]] = inline
        elif arg in FLAGS and i + 1 < len(args):
            values[FLAGS[arg]] = args[i + 1]
            i += 1
        i += 1
    return values


def split_args(args, takes_value):
    """Flags and positional arguments. Short flags may be combined, as in `-Am "msg"`."""
    flags, positional, i = {}, [], 0
    while i < len(args):
        arg = args[i]
        if arg == "--":
            positional += args[i + 1:]
            break
        if arg.startswith("--"):
            name, eq, inline = arg.partition("=")
            if eq:
                flags[name] = inline
            elif name in takes_value and i + 1 < len(args):
                flags[name] = args[i + 1]
                i += 1
            else:
                flags[name] = True
        elif arg.startswith("-") and len(arg) > 1:
            for j, ch in enumerate(arg[1:], 2):
                if "-" + ch not in takes_value:
                    flags["-" + ch] = True
                    continue
                if arg[j:]:
                    flags["-" + ch] = arg[j:]
                elif i + 1 < len(args):
                    flags["-" + ch] = args[i + 1]
                    i += 1
                break
        else:
            positional.append(arg)
        i += 1
    return flags, positional


# ---------------------------------------------------------------- size

def max_lines():
    try:
        return int(os.environ.get("AGENT_PLAYBOOK_PR_MAX_LINES", DEFAULT_MAX_LINES))
    except ValueError:
        return DEFAULT_MAX_LINES


def resolve(cwd, remote, branch):
    for ref in (f"{remote}/{branch}", branch):
        if git(cwd, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"):
            return ref
    return None


def base_ref(cwd, remote, base):
    if base:
        return resolve(cwd, remote, base)

    default = git(cwd, "symbolic-ref", "--short", f"refs/remotes/{remote}/HEAD")
    if default:
        return default
    return resolve(cwd, remote, "main") or resolve(cwd, remote, "master")


def changed_lines(cwd, base, head):
    out = git(cwd, "diff", "--numstat", "-M", f"{base}...{head}")
    if out is None:
        return None

    total = 0
    for line in out.splitlines():
        added, deleted, path = line.split("\t", 2)
        new_path = path.replace("}", "").split(" => ")[-1]
        if added == "-" or os.path.basename(new_path) in LOCKFILES:
            continue
        total += int(added) + int(deleted)
    return total


def size_reason(cwd, remote, base, head):
    limit = max_lines()
    if limit <= 0:
        return None

    base_name = base_ref(cwd, remote, base)
    if not base_name or not git(cwd, "rev-parse", "--verify", "--quiet", f"{head}^{{commit}}"):
        return None

    n = changed_lines(cwd, base_name, head)
    if n is None or n <= limit:
        return None
    return (f"`{head}` changes {n} lines against `{base_name}` (limit {limit}, lockfiles not counted). "
            "Split it into stacked PRs, one concern each, as in the conventional-commits skill's references/stacked-prs.md.")


# ---------------------------------------------------------------- naming

def has_commitlint(cwd):
    root = git(cwd, "rev-parse", "--show-toplevel") or cwd
    if glob.glob(os.path.join(root, "commitlint.config.*")) or glob.glob(os.path.join(root, ".commitlintrc*")):
        return True
    try:
        with open(os.path.join(root, "package.json"), encoding="utf-8") as fh:
            return "commitlint" in json.load(fh)
    except (OSError, ValueError):
        return False


def title_reasons(cwd, title):
    reasons = []
    # a commitlint config defines its own types, so only the header shape is checked there
    known = has_commitlint(cwd) or KNOWN_TYPE.match(title)
    if not HEADER.match(title) or not known:
        reasons.append(f"PR title `{title}` is not a Conventional Commits header (`type(scope): subject`).")
    if len(title) > MAX_TITLE:
        reasons.append(f"PR title is {len(title)} characters; keep it under {MAX_TITLE}.")
    if title.rstrip().endswith("."):
        reasons.append("PR title ends with a period.")
    if TITLE_STACK_MARK.search(title):
        reasons.append("PR title carries a stack position; list it in the PR body's Stack section instead.")
    return reasons


def branch_reasons(cwd, remote, head):
    if head in TRUNKS:
        return []

    reasons = []
    if BRANCH_STACK_MARK.search(head):
        reasons.append(f"Branch `{head}` carries a stack position; list it in the PR body's Stack section instead.")

    refs = git(cwd, "for-each-ref", "--format=%(refname:lstrip=3)", f"refs/remotes/{remote}") or ""
    others = [name for name in refs.splitlines() if name and name not in TRUNKS and name != head]
    typed = sum(1 for name in others if TYPE_BRANCH.match(name))
    # with fewer than 3 remote branches the repo has no pattern yet, so the default applies
    repo_uses_types = len(others) < 3 or typed * 2 >= len(others)
    if repo_uses_types and not TYPE_BRANCH.match(head):
        reasons.append(f"Branch `{head}` does not follow `<type>/<slug>` (lowercase, kebab-case slug).")
    return reasons


# ---------------------------------------------------------------- commands

def pr_create_reasons(cwd, args):
    flags = parse_flags(args)
    head = flags.get("head", "").split(":")[-1] or git(cwd, "rev-parse", "--abbrev-ref", "HEAD")
    if not head or head == "HEAD":
        return []
    remote = remote_of(cwd, head)

    reasons = []
    size = size_reason(cwd, remote, flags.get("base"), head)
    if size:
        reasons.append(size)
    if "title" in flags:
        reasons += title_reasons(cwd, flags["title"])
    return reasons + branch_reasons(cwd, remote, head)


def stack_branch_reasons(cwd, sub, args):
    """`gh stack init` and `gh stack add`: the names of the branches they create."""
    flags, names = split_args(args, STACK_VALUE_FLAGS[sub])
    if names:
        return [r for name in names for r in branch_reasons(cwd, remote_of(cwd, name), name)]
    if sub == "add" and ("-m" in flags or "--message" in flags):
        return ["`gh stack add -m` without a branch name generates an `MM-DD-slug` name. "
                "Pass the name: `gh stack add <type>/<slug>`."]
    return [f"A bare `gh stack {sub}` prompts for a branch name. Pass it: `gh stack {sub} <type>/<slug>`."]


def stack_layers(cwd):
    """(branch, base, has_pr) for each unmerged layer of the current stack, bottom first."""
    out = gh(cwd, "stack", "view", "--json")
    try:
        view = json.loads(out) if out else None
    except ValueError:
        return []
    if not isinstance(view, dict):
        return []

    base, layers = view.get("trunk") or None, []
    for branch in view.get("branches") or []:
        name = branch.get("name")
        if not name or branch.get("isMerged"):
            continue
        layers.append((name, base, bool(branch.get("pr"))))
        base = name
    return layers


def stack_submit_reasons(cwd, args):
    flags, _ = split_args(args, STACK_VALUE_FLAGS["submit"])
    reasons = []
    if "--auto" not in flags:
        reasons.append("Pass `--auto`: a bare `gh stack submit` opens a full-screen editor.")

    remote_flag = flags.get("--remote")
    unopened = []
    for name, base, has_pr in stack_layers(cwd):
        remote = remote_flag if isinstance(remote_flag, str) else remote_of(cwd, name)
        size = size_reason(cwd, remote, base, name)
        if size:
            reasons.append(size)
        reasons += branch_reasons(cwd, remote, name)
        if not has_pr:
            unopened.append(f"`{name}`")
    if unopened:
        reasons.append(f"`gh stack submit` would open PRs for {', '.join(unopened)} with a title taken from the commit "
                       "subject or the branch name and a \"Stack created with GitHub Stacks CLI\" footer. Open each one "
                       "with `gh pr create --base <layer below>`, then run `gh stack link <PR numbers>`.")
    return reasons


def stack_link_reasons(cwd, args):
    _, refs = split_args(args, STACK_VALUE_FLAGS["link"])
    reasons, unopened = [], []
    for ref in refs:
        if PR_REF.match(ref):
            continue
        reasons += branch_reasons(cwd, remote_of(cwd, ref), ref)
        if gh(cwd, "pr", "list", "--head", ref, "--state", "open", "--json", "number", "--jq", "length") == "0":
            unopened.append(f"`{ref}`")
    if unopened:
        reasons.append(f"`gh stack link` would open PRs for {', '.join(unopened)} with generated titles. Open each one "
                       "with `gh pr create --base <layer below>`, then pass the PR numbers to `gh stack link`.")
    return reasons


def main():
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return
    if data.get("tool_name") != "Bash":
        return

    cwd = data.get("cwd") or os.getcwd()
    reasons = []
    for words in commands((data.get("tool_input") or {}).get("command", "")):
        if words[:3] == ["gh", "pr", "create"]:
            reasons += pr_create_reasons(cwd, words[3:])
        elif words[:2] == ["gh", "stack"] and len(words) > 2:
            sub, args = words[2], words[3:]
            if sub in ("init", "add"):
                reasons += stack_branch_reasons(cwd, sub, args)
            elif sub == "submit":
                reasons += stack_submit_reasons(cwd, args)
            elif sub == "link":
                reasons += stack_link_reasons(cwd, args)
    emit(list(dict.fromkeys(reasons)))


if __name__ == "__main__":
    main()
