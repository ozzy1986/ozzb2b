#!/usr/bin/env bash
# API + search smoke test for the RU outsourcing ingest.
set -euo pipefail

pp() {
  python3 -c '
import json, sys
d = json.load(sys.stdin)
mode = sys.argv[1]
if mode == "providers":
    print("total:", d.get("total"))
    for it in d.get("items", []):
        name = it.get("display_name")
        city = (it.get("city") or {}).get("name")
        lf = (it.get("legal_form") or {}).get("code")
        print("  -", name, "|", city, "|", lf)
elif mode == "search":
    print("backend:", d.get("backend"))
    print("total:", d.get("total"))
    for it in d.get("items", []):
        print("  -", it.get("display_name"))
elif mode == "categories":
    tops = [c["slug"] for c in d if c.get("parent_id") is None]
    print(" ".join(tops))
' "$1"
}

echo "== GET /providers?country=RU =="
curl -s 'http://127.0.0.1:8001/providers?country=RU&per_page=5' | pp providers

echo
echo "== GET /search?q=software&country=RU =="
curl -s 'http://127.0.0.1:8001/search?q=software&country=RU&per_page=5' | pp search

echo
echo "== GET /categories (top level) =="
curl -s 'http://127.0.0.1:8001/categories' | pp categories

echo
echo "== public: https://ozzb2b.com/providers?country=ru =="
curl -sI https://ozzb2b.com/providers?country=ru | head -1
echo "== public: https://ozzb2b.com/providers/reksoft =="
curl -sI https://ozzb2b.com/providers/reksoft | head -1
