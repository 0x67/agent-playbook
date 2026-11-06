#!/bin/sh
set -e
cat > go.mod <<'X'
module example.com/path

go 1.27
X
cat > path.go <<'X'
package path

import "strings"

// splitAtLast splits s around the last occurrence of sep.
func splitAtLast(s, sep string) (before, after string, found bool) {
	i := strings.LastIndex(s, sep)
	if i < 0 {
		return s, "", false
	}
	return s[:i], s[i+len(sep):], true
}
X
