FROM rust:1.82-slim AS build
WORKDIR /src
COPY Cargo.toml ./
RUN mkdir -p src && echo "fn main(){}" > src/main.rs && cargo fetch
COPY . .
RUN cargo build --release --locked || cargo build --release

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system app && useradd --system --gid app --no-create-home app
WORKDIR /app
COPY --from=build /src/target/release/ozzb2b-matcher /usr/local/bin/ozzb2b-matcher
USER app
EXPOSE 8090
ENTRYPOINT ["/usr/local/bin/ozzb2b-matcher"]
