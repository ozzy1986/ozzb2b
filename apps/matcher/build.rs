// Generates the tonic/prost modules for the matcher gRPC API.
//
// The protos live outside the crate (under repo-root `proto/`) so they can be
// consumed by other languages (Python, Go) from the same source of truth.
// We feed the shared directory as an include root and emit into Cargo's
// OUT_DIR; `src/main.rs` pulls them in via `tonic::include_proto!`.
use std::path::PathBuf;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let crate_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let proto_root = crate_dir.join("../../proto");
    let proto_file = proto_root.join("ozzb2b/matcher/v1/matcher.proto");

    tonic_build::configure()
        .build_client(false)
        .build_server(true)
        .compile_protos(
            &[proto_file.to_str().expect("proto path is valid utf-8")],
            &[proto_root.to_str().expect("proto root is valid utf-8")],
        )?;

    println!("cargo:rerun-if-changed={}", proto_root.display());
    Ok(())
}
