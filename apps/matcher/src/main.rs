//! ozzb2b matcher service entrypoint.
//!
//! Two surfaces are exposed:
//!
//! * HTTP `/health` and `/ready` on `OZZB2B_MATCHER_HTTP_ADDR` (default
//!   `0.0.0.0:8090`) — used by Docker / Nginx / humans.
//! * gRPC `MatcherService` on `OZZB2B_MATCHER_GRPC_ADDR` (default
//!   `0.0.0.0:9090`) — the only business interface. The Python API is the
//!   only client today.

use std::net::SocketAddr;

use axum::{http::header, response::IntoResponse, routing::get, Json, Router};
use ozzb2b_matcher::metrics;
use ozzb2b_matcher::proto::matcher_v1::matcher_service_server::MatcherServiceServer;
use ozzb2b_matcher::service::MatcherServer;
use serde::Serialize;
use tonic::transport::Server as GrpcServer;
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

async fn metrics_handler() -> impl IntoResponse {
    match metrics::global().encode_text() {
        Ok(body) => (
            axum::http::StatusCode::OK,
            [(header::CONTENT_TYPE, "text/plain; version=0.0.4")],
            body,
        )
            .into_response(),
        Err(err) => (
            axum::http::StatusCode::INTERNAL_SERVER_ERROR,
            [(header::CONTENT_TYPE, "text/plain; charset=utf-8")],
            format!("encode error: {err}"),
        )
            .into_response(),
    }
}

fn http_app() -> Router {
    Router::new()
        .route("/health", get(health))
        .route("/ready", get(health))
        .route("/metrics", get(metrics_handler))
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    tracing_subscriber::fmt()
        .json()
        .with_env_filter(
            EnvFilter::try_from_default_env().unwrap_or_else(|_| EnvFilter::new("info")),
        )
        .init();

    let http_addr: SocketAddr = std::env::var("OZZB2B_MATCHER_HTTP_ADDR")
        .unwrap_or_else(|_| "0.0.0.0:8090".to_string())
        .parse()?;
    let grpc_addr: SocketAddr = std::env::var("OZZB2B_MATCHER_GRPC_ADDR")
        .unwrap_or_else(|_| "0.0.0.0:9090".to_string())
        .parse()?;

    tracing::info!(
        http = %http_addr,
        grpc = %grpc_addr,
        version = VERSION,
        "matcher.start"
    );

    let http_listener = tokio::net::TcpListener::bind(http_addr).await?;
    let http_future =
        axum::serve(http_listener, http_app()).with_graceful_shutdown(shutdown_signal());

    let grpc_future = GrpcServer::builder()
        .add_service(MatcherServiceServer::new(MatcherServer::default()))
        .serve_with_shutdown(grpc_addr, shutdown_signal());

    tokio::select! {
        res = http_future => res?,
        res = grpc_future => res?,
    }

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
