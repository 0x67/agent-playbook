#!/bin/sh
# Run the agent-playbook eval suite with a no-plugin baseline arm.
#
# `claude plugin eval` loads only the plugin under test, so the humanizer dependency
# declared in plugin.json is missing and Claude Code refuses to load agent-playbook. This script evals a
# temporary copy with the dependencies removed and copies the results back to evals/results/.
#
# usage: evals/run.sh [extra `claude plugin eval` flags], e.g. --case rust-read --runs 1 --model sonnet
set -eu
repo=$(cd "$(dirname "$0")/.." && pwd)
work=$(mktemp -d "${TMPDIR:-/tmp}/agent-playbook-eval.XXXXXX")
trap 'rm -rf "$work"' EXIT

mkdir -p "$work/agent-playbook"
(cd "$repo" && tar cf - --exclude .git --exclude evals/results .) | (cd "$work/agent-playbook" && tar xf -)
python3 - "$work/agent-playbook/.claude-plugin/plugin.json" <<'EOF'
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
(cd "$work/agent-playbook" && claude plugin eval . --scaffold --trust-plugin --no-publish \
    --allow-tools Edit Write --judge-model sonnet \
    --output-dir "$out" --report "$out/report.html" --json "$out/result.json" "$@" < /dev/null) || status=$?
echo "results: $out"
exit "$status"
