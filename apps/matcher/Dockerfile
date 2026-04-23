# Matcher gRPC service. Build context MUST be the repo root so the shared
# `proto/` directory is visible to the crate's `build.rs`.
#
# Example: docker build -f apps/matcher/Dockerfile .

FROM rust:1.95-slim AS build
WORKDIR /src

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        protobuf-compiler \
    && rm -rf /var/lib/apt/lists/*

# Copy only manifests + protos first to maximize Docker layer caching.
COPY apps/matcher/Cargo.toml ./apps/matcher/
COPY proto/ ./proto/

# Warm the dependency cache with a stubbed crate. The `build.rs` stub avoids
# invoking tonic-build at fetch time.
RUN mkdir -p apps/matcher/src \
    && echo "fn main(){}" > apps/matcher/src/main.rs \
    && echo "fn main() -> Result<(), Box<dyn std::error::Error>> { Ok(()) }" \
        > apps/matcher/build.rs \
    && cd apps/matcher && cargo fetch

COPY apps/matcher/ ./apps/matcher/

RUN cd apps/matcher && cargo build --release

FROM debian:bookworm-slim
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates wget \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system app \
    && useradd --system --gid app --no-create-home app

WORKDIR /app
COPY --from=build /src/apps/matcher/target/release/ozzb2b-matcher /usr/local/bin/ozzb2b-matcher
USER app
EXPOSE 8090 9090
ENTRYPOINT ["/usr/local/bin/ozzb2b-matcher"]
