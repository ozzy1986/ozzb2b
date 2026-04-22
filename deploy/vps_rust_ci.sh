#!/usr/bin/env bash
# Run the same Rust gates CI does, using the toolchain image directly so we
# can catch fmt/clippy regressions before pushing.
set -euo pipefail

cd /var/www/ozzb2b.com/app

docker run --rm \
  -v "$(pwd)":/src \
  -w /src/apps/matcher \
  rust:1.85-slim \
  bash -c '
    set -euo pipefail
    apt-get update -qq
    apt-get install -y -qq protobuf-compiler >/dev/null
    rustup component add rustfmt clippy >/dev/null
    echo "--- cargo fmt --check"
    cargo fmt --check
    echo "--- cargo clippy"
    cargo clippy --all-targets -- -D warnings
    echo "--- cargo test"
    cargo test --all-targets
  '
