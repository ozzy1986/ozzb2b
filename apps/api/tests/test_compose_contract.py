"""Structural contract tests for compose.prod.yml.

The VPS depends on compose.prod.yml behaving predictably:
  * every service must be restart-policied so a crash can self-heal;
  * every service that exposes a network port must advertise a healthcheck
    (so ``depends_on.condition: service_healthy`` is meaningful upstream);
  * host port bindings MUST be localhost-only — public traffic enters
    exclusively through the host reverse proxy (Apache or nginx).

These tests ensure regressions in any of the above are caught in CI
before a deploy accidentally opens a service to the public Internet or
strips its restart/healthcheck guardrails.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")


ROOT = Path(__file__).resolve().parents[3]
COMPOSE_PATH = ROOT / "compose.prod.yml"
ALERTMANAGER_NOOP_PATH = ROOT / "infra" / "alertmanager" / "alertmanager.noop.yml"
APACHE_CONFIG_DIR = ROOT / "infra" / "apache"


# Services that intentionally don't expose HTTP endpoints we can probe:
# Celery workers don't run an HTTP server, so they can't have a standard
# healthcheck. They have `restart: unless-stopped` so Docker still recovers
# on crash.
SERVICES_WITHOUT_HEALTHCHECK_OK = {"scraper", "scraper_beat"}


def _load_compose() -> dict:
    with COMPOSE_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_compose_file_exists() -> None:
    assert COMPOSE_PATH.is_file(), f"missing compose file at {COMPOSE_PATH}"


def test_every_service_has_restart_policy() -> None:
    compose = _load_compose()
    services = compose["services"]
    for name, spec in services.items():
        assert spec.get("restart") in {"unless-stopped", "always", "on-failure"}, (
            f"service {name!r} is missing a restart policy"
        )


def test_every_exposing_service_has_healthcheck() -> None:
    compose = _load_compose()
    for name, spec in compose["services"].items():
        if name in SERVICES_WITHOUT_HEALTHCHECK_OK:
            continue
        has_ports = bool(spec.get("ports"))
        # Background workers without ports still get skipped; they heal via
        # restart policy.
        if not has_ports:
            continue
        assert "healthcheck" in spec, (
            f"service {name!r} exposes ports but has no healthcheck — "
            f"depends_on.service_healthy won't work"
        )


PORT_BIND_RE = re.compile(
    r"^(?P<host_ip>[^:]+):(?P<host_port>\d+):(?P<cport>\d+)(?:/(?:tcp|udp))?$"
)


def test_every_port_binding_is_localhost_only() -> None:
    compose = _load_compose()
    offenders: list[str] = []
    for name, spec in compose["services"].items():
        for port in spec.get("ports") or []:
            if isinstance(port, dict):
                # Extended syntax: require `mode: host` + `host_ip`.
                if port.get("host_ip") not in {"127.0.0.1", "::1"}:
                    offenders.append(f"{name}: {port}")
                continue
            m = PORT_BIND_RE.match(str(port))
            if not m:
                offenders.append(f"{name}: unparseable port {port!r}")
                continue
            if m.group("host_ip") not in {"127.0.0.1", "::1"}:
                offenders.append(f"{name}: {port} binds to {m.group('host_ip')}")
    assert not offenders, (
        "Services must bind only to 127.0.0.1 — public traffic enters via "
        "the host reverse proxy. Offenders:\n  " + "\n  ".join(offenders)
    )


def test_critical_services_depend_on_healthy_upstreams() -> None:
    """web→api and events→clickhouse must only start after upstream is healthy."""
    compose = _load_compose()
    web = compose["services"]["web"]
    assert web["depends_on"]["api"]["condition"] == "service_healthy"

    events = compose["services"]["events"]
    assert events["depends_on"]["clickhouse"]["condition"] == "service_healthy"

    api = compose["services"]["api"]
    assert api["depends_on"]["meilisearch"]["condition"] == "service_healthy"


def test_scraper_has_exactly_one_beat_scheduler() -> None:
    """Production must run one scheduler beside the independently scalable workers."""
    services = _load_compose()["services"]
    worker = services["scraper"]
    beat = services["scraper_beat"]

    worker_command = " ".join(worker["command"])
    assert "--queues=scraper" in worker_command

    assert beat["image"] == worker["image"]
    assert beat["env_file"] == worker["env_file"]
    assert beat["extra_hosts"] == worker["extra_hosts"]

    command = " ".join(beat["command"])
    assert " beat " in f" {command} "
    assert " worker " not in f" {command} "
    assert "--schedule=/tmp/celerybeat-schedule" in command
    assert not beat.get("ports")


def test_alertmanager_has_secret_free_fallback_config() -> None:
    """Prometheus must not retain a permanently-down target without Telegram."""
    with ALERTMANAGER_NOOP_PATH.open(encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file)

    receiver = config["route"]["receiver"]
    receivers = {item["name"]: item for item in config["receivers"]}
    assert receiver in receivers
    assert "telegram_configs" not in receivers[receiver]


def test_grafana_admin_password_has_no_insecure_default() -> None:
    grafana = _load_compose()["services"]["grafana"]
    password = grafana["environment"]["GF_SECURITY_ADMIN_PASSWORD"]
    assert password.startswith("${OZZB2B_GRAFANA_ADMIN_PASSWORD:?")
    assert "change_me" not in password


@pytest.mark.parametrize(
    ("filename", "upstream"),
    [
        ("ozzb2b.com.conf", "http://127.0.0.1:3101/"),
        ("api.ozzb2b.com.conf", "http://127.0.0.1:8001/"),
        ("grafana.ozzb2b.com.conf", "http://127.0.0.1:3102/"),
    ],
)
def test_apache_vhosts_proxy_public_services_to_loopback(
    filename: str,
    upstream: str,
) -> None:
    config = (APACHE_CONFIG_DIR / filename).read_text(encoding="utf-8")
    assert f"ProxyPass / {upstream}" in config
    assert "0.0.0.0" not in config


def test_observability_stack_memory_limits_declared() -> None:
    """Observability stack must declare memory limits (protects the VPS)."""
    compose = _load_compose()
    should_have_mem_limit = {
        "clickhouse",
        "prometheus",
        "loki",
        "promtail",
        "grafana",
        "node_exporter",
        "cadvisor",
    }
    missing = [
        name
        for name in should_have_mem_limit
        if not compose["services"].get(name, {}).get("mem_limit")
    ]
    assert not missing, f"services without mem_limit: {missing}"
