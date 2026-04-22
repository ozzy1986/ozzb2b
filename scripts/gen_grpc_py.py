"""Regenerate Python gRPC stubs for the API.

Run from repo root:

    python scripts/gen_grpc_py.py

Requires `grpcio-tools` (pulled in by the API's dev dependencies). The output
lands under `apps/api/src/ozzb2b_api/grpc_gen/` and is committed to the repo
so runtime containers don't need protoc.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from grpc_tools import protoc

REPO_ROOT = Path(__file__).resolve().parents[1]
PROTO_ROOT = REPO_ROOT / "proto"
OUT_DIR = REPO_ROOT / "apps" / "api" / "src" / "ozzb2b_api" / "grpc_gen"

PROTO_FILES = [
    PROTO_ROOT / "ozzb2b" / "matcher" / "v1" / "matcher.proto",
]


def main() -> int:
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)
    (OUT_DIR / "__init__.py").write_text(
        '"""Generated gRPC stubs for the API. Regenerate via scripts/gen_grpc_py.py."""\n',
        encoding="utf-8",
    )

    args = [
        "protoc",
        f"--proto_path={PROTO_ROOT}",
        f"--python_out={OUT_DIR}",
        f"--grpc_python_out={OUT_DIR}",
        *[str(p) for p in PROTO_FILES],
    ]
    rc = protoc.main(args)
    if rc != 0:
        print(f"protoc exited with code {rc}", file=sys.stderr)
        return rc

    for path in OUT_DIR.rglob("*.py"):
        rel = path.relative_to(OUT_DIR)
        parent = OUT_DIR.joinpath(*rel.parts[:-1])
        init = parent / "__init__.py"
        if not init.exists():
            init.write_text("", encoding="utf-8")

    # protoc emits absolute imports like `from ozzb2b.matcher.v1 import ...`
    # but we keep the generated tree nested inside `ozzb2b_api.grpc_gen` so
    # it does not clash with a top-level `ozzb2b` package in the installed
    # distribution. Rewrite every generated file to match.
    prefix = "ozzb2b_api.grpc_gen."
    for path in OUT_DIR.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        rewritten = text.replace(
            "from ozzb2b.", f"from {prefix}ozzb2b."
        ).replace(
            "import ozzb2b.", f"import {prefix}ozzb2b."
        )
        if rewritten != text:
            path.write_text(rewritten, encoding="utf-8")

    print("gRPC stubs regenerated under", OUT_DIR.relative_to(REPO_ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
