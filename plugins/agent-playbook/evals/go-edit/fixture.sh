#!/bin/sh
set -e
cat > go.mod <<'X'
module example.com/mathx

go 1.25
X
cat > mathx.go <<'X'
// Package mathx holds small numeric helpers.
package mathx
X
