"""Compose healthy — no 0.0.0.0 bindings, required services present."""

from __future__ import annotations

from pathlib import Path

import re

COMPOSE = Path(__file__).parent.parent / "docker-compose.yml"


def test_no_0_0_0_0_bindings() -> None:
    text = COMPOSE.read_text()
    # check only port bindings (lines with 0.0.0.0:), comments mentioning 0.0.0.0 are allowed
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        assert "0.0.0.0:" not in line, f"compose must not bind 0.0.0.0 — found in: {line!r}"


def test_all_bindings_are_127_0_0_1() -> None:
    text = COMPOSE.read_text()
    # find all host port bindings like "127.0.0.1:8001:8000" vs bare ":8000"
    # ensure every ports entry contains 127.0.0.1
    ports = re.findall(r'"([^"]*:\d+:\d+)"', text)
    for p in ports:
        assert p.startswith("127.0.0.1:"), f"port binding {p!r} must be 127.0.0.1 bound"


def test_9_services_healthcheck_present() -> None:
    text = COMPOSE.read_text()
    # must contain healthcheck for marketplace and verification-service with curl -f http://localhost:8000/health
    assert "marketplace:" in text
    assert "verification-service:" in text
    assert "curl -f http://localhost:8000/health" in text
    # backend-core must have MARKETPLACE_URL
    assert "MARKETPLACE_URL" in text
    # volume and network retained
    assert "sih_dnk_pgdata" in text
    assert "dbnet" in text
    # depends_on db redis
    assert "depends_on" in text


def test_compose_has_expected_service_count() -> None:
    text = COMPOSE.read_text()
    # count services: db, redis, validation-engine, voice-pipeline, pricing-engine, tracking-api, frontend, backend-core, marketplace, verification-service (10)
    expected = ["db:", "redis:", "validation-engine:", "voice-pipeline:", "pricing-engine:", "tracking-api:", "frontend:", "backend-core:", "marketplace:", "verification-service:"]
    for svc in expected:
        assert svc in text, f"missing service {svc}"
