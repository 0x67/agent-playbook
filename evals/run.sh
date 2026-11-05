#!/bin/sh
# Run the ai-setup eval suite with a no-plugin baseline arm.
#
# `claude plugin eval` loads only the plugin under test, so the humanizer and fable dependencies
# declared in plugin.json are missing and Claude Code refuses to load ai-setup. This script evals a
# temporary copy with the dependencies removed and copies the results back to evals/results/.
#
# usage: evals/run.sh [extra `claude plugin eval` flags], e.g. --case rust-read --runs 1 --model sonnet
set -eu
repo=$(cd "$(dirname "$0")/.." && pwd)
work=$(mktemp -d "${TMPDIR:-/tmp}/ai-setup-eval.XXXXXX")
trap 'rm -rf "$work"' EXIT

mkdir -p "$work/ai-setup"
(cd "$repo" && tar cf - --exclude .git --exclude evals/results .) | (cd "$work/ai-setup" && tar xf -)
python3 - "$work/ai-setup/.claude-plugin/plugin.json" <<'EOF'
import json, sys
path = sys.argv[1]
manifest = json.load(open(path))
manifest.pop("dependencies", None)
json.dump(manifest, open(path, "w"), indent=2)
EOF

stamp=$(date -u +%Y-%m-%dT%H-%M-%SZ)
out="$repo/evals/results/$stamp"
mkdir -p "$out"
status=0
# Edit and Write are gated in eval runs; they only touch the per-run sandbox workspace.
# Sonnet judges the llm graders, since Haiku failed correct answers on wording.
(cd "$work/ai-setup" && claude plugin eval . --scaffold --trust-plugin --no-publish \
    --allow-tools Edit Write --judge-model sonnet \
    --output-dir "$out" --report "$out/report.html" --json "$out/result.json" "$@") || status=$?
echo "results: $out"
exit "$status"
