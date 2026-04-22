"""Smoke tests for the observability config files shipped in `infra/`.

These run in CI without a real Prometheus/Grafana: they just make sure the
scrape targets match the services that actually expose /metrics, so a typo
in the config file doesn't silently break our dashboards in production.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PROM_CONFIG = REPO_ROOT / "infra" / "prometheus" / "prometheus.yml"
LOKI_CONFIG = REPO_ROOT / "infra" / "loki" / "loki-config.yaml"
PROMTAIL_CONFIG = REPO_ROOT / "infra" / "promtail" / "promtail-config.yaml"
GRAFANA_DS = REPO_ROOT / "infra" / "grafana" / "provisioning" / "datasources" / "datasource.yml"
OVERVIEW_DASHBOARD = REPO_ROOT / "infra" / "grafana" / "dashboards" / "ozzb2b-overview.json"


def test_prometheus_config_exists_and_scrapes_every_service() -> None:
    text = PROM_CONFIG.read_text(encoding="utf-8")
    # Each service with a /metrics endpoint must be explicitly referenced.
    for target in ("api:8000", "chat:8090", "events:8095", "matcher:8090"):
        assert target in text, f"{target!r} missing from Prometheus scrape config"
    # Every service we scrape must have a matching job_name for easy filtering.
    for job in ("job_name: api", "job_name: chat", "job_name: events", "job_name: matcher"):
        assert job in text, f"{job!r} missing from Prometheus scrape config"


def test_loki_config_pins_retention_and_filesystem_storage() -> None:
    text = LOKI_CONFIG.read_text(encoding="utf-8")
    assert "retention_period" in text
    assert "filesystem" in text
    assert "replication_factor: 1" in text


def test_promtail_scrapes_ozzb2b_compose_project() -> None:
    text = PROMTAIL_CONFIG.read_text(encoding="utf-8")
    # We must only ingest logs from our compose project, never noisy neighbours.
    assert "com.docker.compose.project=ozzb2b" in text
    assert "http://loki:3100/loki/api/v1/push" in text


def test_grafana_datasource_points_at_prometheus_and_loki() -> None:
    text = GRAFANA_DS.read_text(encoding="utf-8")
    assert "http://prometheus:9090" in text
    assert "http://loki:3100" in text
    # Datasource UIDs are referenced from the dashboard JSON; keep them in sync.
    assert "ozzb2b-prometheus" in text
    assert "ozzb2b-loki" in text


def test_overview_dashboard_references_provisioned_datasource_uids() -> None:
    text = OVERVIEW_DASHBOARD.read_text(encoding="utf-8")
    assert '"uid": "ozzb2b-prometheus"' in text
    assert '"uid": "ozzb2b-loki"' in text
    # Sanity: core API metrics panels must query the metric names we emit.
    assert "ozzb2b_api_http_requests_total" in text
    assert "ozzb2b_api_http_request_duration_seconds_bucket" in text
