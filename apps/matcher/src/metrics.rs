//! Prometheus metrics for the matcher service.
//!
//! We keep a single custom `Registry` (no `default_registry()`) so a future
//! embedding of this crate into another process cannot accidentally pick up
//! our counters. The exporter is a trivial text response mounted at
//! `GET /metrics` in `main.rs`.

use std::sync::OnceLock;

use prometheus::{
    Encoder, HistogramOpts, HistogramVec, IntCounterVec, Opts, Registry, TextEncoder,
};

pub struct Metrics {
    pub registry: Registry,
    pub rank_calls: IntCounterVec,
    pub rank_candidates: IntCounterVec,
    pub rank_latency: HistogramVec,
}

impl Default for Metrics {
    fn default() -> Self {
        Self::new()
    }
}

impl Metrics {
    pub fn new() -> Self {
        let registry = Registry::new();

        let rank_calls = IntCounterVec::new(
            Opts::new(
                "ozzb2b_matcher_rank_calls_total",
                "Total Rank RPCs received, labelled by outcome.",
            ),
            &["outcome"],
        )
        .expect("rank_calls metric registers");

        let rank_candidates = IntCounterVec::new(
            Opts::new(
                "ozzb2b_matcher_rank_candidates_total",
                "Total candidates seen across all Rank calls.",
            ),
            &["outcome"],
        )
        .expect("rank_candidates metric registers");

        let rank_latency = HistogramVec::new(
            HistogramOpts::new(
                "ozzb2b_matcher_rank_duration_seconds",
                "Latency of a Rank RPC, seconds.",
            )
            .buckets(vec![
                0.0005, 0.001, 0.0025, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0,
            ]),
            &["outcome"],
        )
        .expect("rank_latency metric registers");

        registry
            .register(Box::new(rank_calls.clone()))
            .expect("register rank_calls");
        registry
            .register(Box::new(rank_candidates.clone()))
            .expect("register rank_candidates");
        registry
            .register(Box::new(rank_latency.clone()))
            .expect("register rank_latency");

        Self {
            registry,
            rank_calls,
            rank_candidates,
            rank_latency,
        }
    }

    pub fn encode_text(&self) -> Result<String, std::io::Error> {
        let mut buf = Vec::new();
        let encoder = TextEncoder::new();
        encoder
            .encode(&self.registry.gather(), &mut buf)
            .map_err(std::io::Error::other)?;
        String::from_utf8(buf).map_err(std::io::Error::other)
    }
}

static INSTANCE: OnceLock<Metrics> = OnceLock::new();

pub fn global() -> &'static Metrics {
    INSTANCE.get_or_init(Metrics::new)
}
