//! Library crate for the matcher service.
//!
//! Scoring is kept in its own module so it can be unit-tested without spinning
//! up the tonic server. The gRPC types live in `proto::matcher_v1`.

pub mod proto {
    pub mod matcher_v1 {
        tonic::include_proto!("ozzb2b.matcher.v1");
    }
}

pub mod scoring;
pub mod service;
