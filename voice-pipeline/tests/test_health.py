"""GET /healthz — response shape and provider."""

from fastapi.testclient import TestClient

import main


def test_healthz_sarvam_provider() -> None:
    with TestClient(main.app) as client:
        response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "provider": "sarvam"}
