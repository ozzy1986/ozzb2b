#!/usr/bin/env bash
# Phase 5 local CI: tidy+test events and chat Go modules, fmt/clippy/test Rust matcher.
set -euo pipefail
cd /var/www/ozzb2b.com/app

echo "=== go events ==="
docker run --rm \
  -v /var/www/ozzb2b.com/app/apps/events:/src \
  -w /src \
  golang:1.23-alpine sh -c '
    go mod tidy
    go vet ./...
    go build ./...
    go test ./...
  '

echo "=== go chat ==="
docker run --rm \
  -v /var/www/ozzb2b.com/app/apps/chat:/src \
  -w /src \
  golang:1.23-alpine sh -c '
    go mod tidy
    go vet ./...
    go build ./...
    go test ./...
  '

echo "=== rust matcher ==="
docker run --rm \
  -v /var/www/ozzb2b.com/app:/src \
  -w /src/apps/matcher \
  rust:1.85-slim bash -c '
    apt-get update -qq
    apt-get install -y -qq protobuf-compiler >/dev/null
    rustup component add rustfmt clippy >/dev/null
    cargo fmt --check
    cargo clippy --all-targets -- -D warnings
    cargo test --all-targets
  '
