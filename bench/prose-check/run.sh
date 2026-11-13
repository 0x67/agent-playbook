#!/bin/sh
# Rerun the prose-check benchmark on corpora built by fetch-open.py and fetch-blogs.py.
# usage: bench/prose-check/run.sh CORPUS_DIR   (blog corpora go in CORPUS_DIR/blogs; writes results.json here)
set -eu
here=$(cd "$(dirname "$0")" && pwd)
corpus=$1
shift

blogs=""
for dir in "$corpus"/blogs/*/; do
  blogs="$blogs human-blog-$(basename "$dir")=$dir"
done

# $blogs is split on spaces on purpose: one LABEL=DIR argument per platform
# shellcheck disable=SC2086
exec uv run --quiet --no-project --with 'regex==2026.11.9' python "$here/../../scripts/prose-bench.py" \
  --json "$here/results.json" \
  --auc 'human-blog-*:ai-sonnet,ai-opus' --auc 'human-hc3:ai-hc3' \
  human-rustbook="$corpus/human/rust-book" human-goblog="$corpus/human/go-blog" $blogs \
  human-hc3="$corpus/hc3/human" ai-hc3="$corpus/hc3/chatgpt" \
  ai-sonnet="$here/ai-claude/sonnet" ai-opus="$here/ai-claude/opus" \
  fixture-positive="$corpus/fixtures/positive" fixture-negative="$corpus/fixtures/negative"
