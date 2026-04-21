//! ozzb2b matcher service (Phase 3 target).
//!
//! Phase 0 exposes a minimal HTTP `/health` endpoint; the gRPC interface
//! defined in `proto/ozzb2b/matcher/v1` will be added when the matching
//! engine is implemented.

use axum::{routing::get, Json, Router};
use serde::Serialize;
use std::net::SocketAddr;
use tracing_subscriber::EnvFilter;

const VERSION: &str = env!("CARGO_PKG_VERSION");

#[derive(Serialize)]
struct Health {
    status: &'static str,
    service: &'static str,
    version: &'static str,
}

async fn health() -> Json<Health> {
    Json(Health {
        status: "ok",
        service: "ozzb2b-matcher",
        version: VERSION,
    })
}

fn app() -> Router {
    Router::new()
        .route("/health", get(health))
        .route("/ready", get(health))
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    tracing_subscriber::fmt()
        .json()
        .with_env_filter(EnvFilter::try_from_default_env().unwrap_or_else(|_| EnvFilter::new("info")))
        .init();

    let addr: SocketAddr = std::env::var("OZZB2B_MATCHER_HTTP_ADDR")
        .unwrap_or_else(|_| "0.0.0.0:8090".to_string())
        .parse()?;

    let listener = tokio::net::TcpListener::bind(addr).await?;
    tracing::info!(addr = %addr, version = VERSION, "matcher.start");

    axum::serve(listener, app())
        .with_graceful_shutdown(shutdown_signal())
        .await?;

    tracing::info!("matcher.stop");
    Ok(())
}

async fn shutdown_signal() {
    let ctrl_c = async {
        tokio::signal::ctrl_c()
            .await
            .expect("failed to install Ctrl+C handler");
    };
    #[cfg(unix)]
    let terminate = async {
        tokio::signal::unix::signal(tokio::signal::unix::SignalKind::terminate())
            .expect("failed to install signal handler")
            .recv()
            .await;
    };
    #[cfg(not(unix))]
    let terminate = std::future::pending::<()>();
    tokio::select! { _ = ctrl_c => {}, _ = terminate => {} }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn health_returns_ok_payload() {
        let Json(body) = health().await;
        assert_eq!(body.status, "ok");
        assert_eq!(body.service, "ozzb2b-matcher");
        assert_eq!(body.version, VERSION);
    }
}
