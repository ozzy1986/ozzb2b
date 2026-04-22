//! tonic service implementation for `MatcherService`.

use std::time::Instant;

use tonic::{Request, Response, Status};

use crate::metrics;
use crate::proto::matcher_v1::{matcher_service_server::MatcherService, RankRequest, RankResponse};
use crate::scoring::{rank, Weights};

/// Request guardrails so a pathological caller cannot OOM the service. The
/// values are permissive for our small catalog — adjust once the matcher
/// starts fronting larger shortlists.
pub const MAX_CANDIDATES: usize = 1_000;
pub const MAX_QUERY_CHARS: usize = 500;

#[derive(Debug, Default)]
pub struct MatcherServer {
    weights: Weights,
}

impl MatcherServer {
    pub fn with_weights(weights: Weights) -> Self {
        Self { weights }
    }
}

#[tonic::async_trait]
impl MatcherService for MatcherServer {
    async fn rank(&self, request: Request<RankRequest>) -> Result<Response<RankResponse>, Status> {
        let started = Instant::now();
        let m = metrics::global();
        let req = request.into_inner();

        if req.query.chars().count() > MAX_QUERY_CHARS {
            m.rank_calls.with_label_values(&["invalid"]).inc();
            m.rank_latency
                .with_label_values(&["invalid"])
                .observe(started.elapsed().as_secs_f64());
            return Err(Status::invalid_argument("query too long"));
        }
        if req.candidates.len() > MAX_CANDIDATES {
            m.rank_calls.with_label_values(&["invalid"]).inc();
            m.rank_latency
                .with_label_values(&["invalid"])
                .observe(started.elapsed().as_secs_f64());
            return Err(Status::invalid_argument("too many candidates"));
        }

        let total = req.candidates.len() as i32;
        let candidate_count = req.candidates.len() as u64;
        let ranked = rank(&req, &self.weights);

        m.rank_calls.with_label_values(&["ok"]).inc();
        m.rank_candidates
            .with_label_values(&["ok"])
            .inc_by(candidate_count);
        m.rank_latency
            .with_label_values(&["ok"])
            .observe(started.elapsed().as_secs_f64());

        Ok(Response::new(RankResponse {
            providers: ranked,
            total_estimate: total,
        }))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::proto::matcher_v1::Candidate;

    fn sample_request(n: usize) -> RankRequest {
        let mut candidates = Vec::with_capacity(n);
        for i in 0..n {
            candidates.push(Candidate {
                provider_id: format!("p{i}"),
                display_name: format!("Name {i}"),
                description: String::new(),
                category_slugs: vec![],
                country_code: "RU".into(),
                city_slug: String::new(),
                legal_form_code: String::new(),
                retrieval_score: 1.0 / ((i as f32) + 1.0),
            });
        }
        RankRequest {
            query: "name".into(),
            category_slugs: vec![],
            country_codes: vec![],
            city_slugs: vec![],
            legal_form_codes: vec![],
            limit: 10,
            offset: 0,
            candidates,
        }
    }

    #[tokio::test]
    async fn rank_returns_providers_sorted_by_score() {
        let svc = MatcherServer::default();
        let resp = svc
            .rank(Request::new(sample_request(3)))
            .await
            .expect("rank succeeds");
        let body = resp.into_inner();
        assert_eq!(body.providers.len(), 3);
        assert_eq!(body.total_estimate, 3);
        for w in body.providers.windows(2) {
            assert!(w[0].score >= w[1].score);
        }
    }

    #[tokio::test]
    async fn rank_rejects_oversize_input() {
        let svc = MatcherServer::default();
        let mut req = sample_request(1);
        req.query = "x".repeat(MAX_QUERY_CHARS + 1);
        let err = svc.rank(Request::new(req)).await.unwrap_err();
        assert_eq!(err.code(), tonic::Code::InvalidArgument);

        let mut req = sample_request(1);
        req.candidates = (0..MAX_CANDIDATES + 1)
            .map(|i| Candidate {
                provider_id: format!("p{i}"),
                display_name: "n".into(),
                description: String::new(),
                category_slugs: vec![],
                country_code: "RU".into(),
                city_slug: String::new(),
                legal_form_code: String::new(),
                retrieval_score: 0.0,
            })
            .collect();
        let err = svc.rank(Request::new(req)).await.unwrap_err();
        assert_eq!(err.code(), tonic::Code::InvalidArgument);
    }
}
