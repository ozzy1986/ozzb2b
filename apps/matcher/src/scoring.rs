//! Deterministic scoring for the matcher MVP.
//!
//! The goal is a small, readable function that explains itself. We blend two
//! inputs: the retrieval score the API already has (from Meilisearch / PG FTS)
//! and a local term-overlap score over the candidate's text fields.
//!
//! Design notes (SOLID):
//! - `Weights` is a plain value object with safe defaults; callers can override
//!   them from env without touching the scoring loop.
//! - `matcher_score` and `final_score` are separate pure functions so they can
//!   be replaced independently when a future heuristic arrives.

use crate::proto::matcher_v1::{Candidate, RankRequest, ScoredProvider};

/// Scoring weights. Tuned for a small catalog (few dozens to thousands) where
/// we want the human-readable signals (name/category hits) to dominate over
/// raw term counts in descriptions.
#[derive(Debug, Clone, Copy)]
pub struct Weights {
    pub name_hit: f32,
    pub description_hit: f32,
    pub category_hit: f32,
    pub category_facet_bonus: f32,
    pub retrieval: f32,
    pub matcher: f32,
}

impl Default for Weights {
    fn default() -> Self {
        Self {
            name_hit: 3.0,
            description_hit: 1.0,
            category_hit: 2.0,
            category_facet_bonus: 1.5,
            retrieval: 0.4,
            matcher: 0.6,
        }
    }
}

/// Lowercase then split on any non-alphanumeric character. Keeps Unicode
/// letters (Cyrillic, Latin, etc.) and digits. Callers can feed already-
/// normalized text; this is best-effort on the server side.
pub fn tokenize(s: &str) -> Vec<String> {
    s.to_lowercase()
        .split(|c: char| !c.is_alphanumeric())
        .filter(|tok| !tok.is_empty())
        .map(str::to_owned)
        .collect()
}

fn count_hits(haystack_tokens: &[String], needle_tokens: &[String]) -> usize {
    if needle_tokens.is_empty() || haystack_tokens.is_empty() {
        return 0;
    }
    let mut hits = 0usize;
    for needle in needle_tokens {
        for tok in haystack_tokens {
            if tok == needle {
                hits += 1;
            }
        }
    }
    hits
}

/// Pure function: returns the matcher-local score for a single candidate.
/// Always non-negative; zero means "no signal from this matcher".
pub fn matcher_score(
    query_tokens: &[String],
    request_category_slugs: &[String],
    candidate: &Candidate,
    weights: &Weights,
) -> f32 {
    if query_tokens.is_empty() && request_category_slugs.is_empty() {
        return 0.0;
    }

    let name_tokens = tokenize(&candidate.display_name);
    let description_tokens = tokenize(&candidate.description);
    let category_tokens: Vec<String> = candidate
        .category_slugs
        .iter()
        .flat_map(|s| tokenize(s))
        .collect();

    let name_hits = count_hits(&name_tokens, query_tokens) as f32;
    let description_hits = count_hits(&description_tokens, query_tokens) as f32;
    let category_hits = count_hits(&category_tokens, query_tokens) as f32;

    let facet_matches = candidate
        .category_slugs
        .iter()
        .filter(|slug| request_category_slugs.iter().any(|r| r == *slug))
        .count() as f32;

    weights.name_hit * name_hits
        + weights.description_hit * description_hits
        + weights.category_hit * category_hits
        + weights.category_facet_bonus * facet_matches
}

/// Combine the retrieval score with the matcher score.
pub fn final_score(retrieval_score: f32, matcher_score_val: f32, weights: &Weights) -> f32 {
    weights.retrieval * retrieval_score + weights.matcher * matcher_score_val
}

/// Score and re-rank the full candidate list in `request`. Pagination is
/// applied after sorting so the caller's `limit` / `offset` are honored on the
/// re-ranked order.
pub fn rank(request: &RankRequest, weights: &Weights) -> Vec<ScoredProvider> {
    let query_tokens = tokenize(&request.query);

    let mut scored: Vec<ScoredProvider> = request
        .candidates
        .iter()
        .map(|c| {
            let m = matcher_score(&query_tokens, &request.category_slugs, c, weights);
            let f = final_score(c.retrieval_score, m, weights);
            ScoredProvider {
                provider_id: c.provider_id.clone(),
                score: f,
                matcher_score: m,
            }
        })
        .collect();

    // Sort by final score desc, stable on provider_id to keep output
    // deterministic on ties (important for snapshot tests).
    scored.sort_by(|a, b| {
        b.score
            .partial_cmp(&a.score)
            .unwrap_or(std::cmp::Ordering::Equal)
            .then_with(|| a.provider_id.cmp(&b.provider_id))
    });

    let offset = request.offset.max(0) as usize;
    let limit = if request.limit <= 0 {
        scored.len()
    } else {
        request.limit as usize
    };

    scored.into_iter().skip(offset).take(limit).collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    fn cand(id: &str, name: &str, description: &str, cats: &[&str], retrieval: f32) -> Candidate {
        Candidate {
            provider_id: id.into(),
            display_name: name.into(),
            description: description.into(),
            category_slugs: cats.iter().map(|s| (*s).into()).collect(),
            country_code: "RU".into(),
            city_slug: String::new(),
            legal_form_code: String::new(),
            retrieval_score: retrieval,
        }
    }

    #[test]
    fn tokenize_handles_cyrillic_and_punctuation() {
        let toks = tokenize("  Разработка  web-сайтов!  ");
        assert_eq!(toks, vec!["разработка", "web", "сайтов"]);
    }

    #[test]
    fn empty_query_and_no_facets_gives_zero_matcher_score() {
        let c = cand("p1", "Name", "Desc", &["it"], 0.9);
        let s = matcher_score(&[], &[], &c, &Weights::default());
        assert_eq!(s, 0.0);
    }

    #[test]
    fn name_hit_weighs_more_than_description_hit() {
        let w = Weights::default();
        let qtoks = tokenize("разработка");
        let top = cand("p1", "Разработка ПО", "общее описание", &[], 0.0);
        let low = cand("p2", "Компания", "Занимаемся разработкой", &[], 0.0);
        let top_score = matcher_score(&qtoks, &[], &top, &w);
        let low_score = matcher_score(&qtoks, &[], &low, &w);
        assert!(top_score > low_score, "{} vs {}", top_score, low_score);
    }

    #[test]
    fn rank_sorts_desc_and_respects_pagination() {
        let w = Weights::default();
        let req = RankRequest {
            query: "it разработка".into(),
            category_slugs: vec!["it".into()],
            country_codes: vec![],
            city_slugs: vec![],
            legal_form_codes: vec![],
            limit: 2,
            offset: 1,
            candidates: vec![
                cand("p1", "IT разработка", "web", &["it"], 0.5),
                cand("p2", "Юридическая компания", "legal", &["legal"], 0.9),
                cand("p3", "Digital Agency", "разработка сайтов", &["it"], 0.3),
                cand("p4", "Другая компания", "другое", &[], 0.1),
            ],
        };
        let out = rank(&req, &w);
        assert_eq!(out.len(), 2, "limit=2 must be honored");
        // With offset=1 the top hit (p1) is skipped; next two in the sorted
        // order must appear.
        assert_ne!(out[0].provider_id, "p1");
    }

    #[test]
    fn facet_match_boosts_matcher_score() {
        let w = Weights::default();
        let with_facet = cand("p1", "Name", "Desc", &["it"], 0.0);
        let without = cand("p2", "Name", "Desc", &["legal"], 0.0);
        let qtoks = tokenize("name");
        let s_with = matcher_score(&qtoks, &["it".into()], &with_facet, &w);
        let s_without = matcher_score(&qtoks, &["it".into()], &without, &w);
        assert!(s_with > s_without);
    }

    #[test]
    fn final_score_blends_retrieval_and_matcher() {
        let w = Weights::default();
        let fs = final_score(1.0, 10.0, &w);
        let expected = w.retrieval * 1.0 + w.matcher * 10.0;
        assert!((fs - expected).abs() < 1e-6);
    }
}
