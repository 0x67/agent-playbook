#!/bin/sh
# Run a prose-check script with the regex module when possible, so vale_lite.py can compile the
# variable-width lookbehinds that Python's re rejects. Order: a python3 that already has regex, then uv
# with the pinned regex (downloaded once into uv's cache), then plain python3 without it.
# usage: run.sh SCRIPT.py [ARGS...]
dir=$(cd "$(dirname "$0")" && pwd)
script="$dir/$1"
shift

if python3 -c 'import regex' 2>/dev/null; then
  exec python3 "$script" "$@"
fi
if command -v uv >/dev/null 2>&1; then
  exec uv run --quiet --no-project --with 'regex==2026.11.9' python "$script" "$@"
fi
exec python3 "$script" "$@"
