#!/usr/bin/env bash
# Runs `go test -race -cover` in the given module directory and enforces a
# minimum total coverage. Intended for use in CI and the pre-commit hook.
#
# Usage:
#   scripts/check_go_coverage.sh <module_dir> <min_percent>
#
# Example: scripts/check_go_coverage.sh apps/chat 60

set -euo pipefail

DIR="${1:?module dir required}"
MIN="${2:-60}"

cd "$DIR"

PROFILE="coverage.out"
go test -race -coverprofile="$PROFILE" -covermode=atomic ./...

PCT="$(go tool cover -func="$PROFILE" | awk '/^total:/ {gsub("%", "", $3); print $3}')"

if [ -z "${PCT:-}" ]; then
    echo "[$DIR] failed to extract coverage percentage" >&2
    exit 2
fi

awk -v p="$PCT" -v m="$MIN" 'BEGIN {
    if (p+0 < m+0) {
        printf "[%s] coverage %.2f%% is below threshold %.2f%%\n", ENVIRON["PWD"], p, m > "/dev/stderr";
        exit 1;
    }
    printf "[%s] coverage %.2f%% passes threshold %.2f%%\n", ENVIRON["PWD"], p, m;
}'
