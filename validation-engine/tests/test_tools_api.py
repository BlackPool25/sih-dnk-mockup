"""GET /api/tools/* — thin HTTP wrappers over db_tools with pinned negatives.

Happy paths return the db_tools result verbatim; each pinned negative maps to
its HTTP status: unknown duty country -> 200 [], unknown lane pair -> 404,
over-cap weight -> 422, unknown state/flag key -> 404.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.api import app

client = TestClient(app)


def test_categories_happy_path() -> None:
    response = client.get("/api/tools/categories", params={"query": "jute"})
    assert response.status_code == 200
    rows = response.json()
    assert rows
    assert any("jute" in r["slug"] for r in rows)
    assert "source_url" in rows[0]  # provenance on every result


def test_hs_codes_happy_path() -> None:
    response = client.get(
        "/api/tools/hs-codes", params={"category": "jute-products"}
    )
    assert response.status_code == 200
    rows = response.json()
    assert rows
    assert all(r["category_slug"] == "jute-products" for r in rows)


def test_duty_happy_path() -> None:
    response = client.get("/api/tools/duty", params={"country_iso2": "US"})
    assert response.status_code == 200
    assert response.json()


def test_duty_unknown_country_is_empty_list() -> None:
    response = client.get("/api/tools/duty", params={"country_iso2": "ZZ"})
    assert response.status_code == 200  # never 404
    assert response.json() == []


def test_lane_happy_path() -> None:
    response = client.get(
        "/api/tools/lane", params={"country_iso2": "US", "weight_g": 100}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["cost_minor"] > 0
    assert body["weight_cap_g"] == 5000


def test_lane_unknown_pair_is_404() -> None:
    response = client.get(
        "/api/tools/lane", params={"country_iso2": "ZZ", "weight_g": 100}
    )
    assert response.status_code == 404
    assert "detail" in response.json()


def test_lane_over_cap_is_422() -> None:
    response = client.get(
        "/api/tools/lane", params={"country_iso2": "US", "weight_g": 6000}
    )
    assert response.status_code == 422
    assert "detail" in response.json()


def test_state_sales_tax_happy_path() -> None:
    response = client.get("/api/tools/state-sales-tax", params={"state_iso2": "CA"})
    assert response.status_code == 200
    assert response.json()["state_name"] == "California"


def test_state_sales_tax_unknown_is_404() -> None:
    response = client.get("/api/tools/state-sales-tax", params={"state_iso2": "ZZ"})
    assert response.status_code == 404
    assert "detail" in response.json()


def test_config_flag_happy_path() -> None:
    response = client.get("/api/tools/config-flag", params={"key": "us.s301.rate_pct"})
    assert response.status_code == 200
    body = response.json()
    assert body["flag_key"] == "us.s301.rate_pct"
    assert "source_url" in body


def test_config_flag_unknown_is_404() -> None:
    response = client.get("/api/tools/config-flag", params={"key": "no.such.flag"})
    assert response.status_code == 404
    assert "detail" in response.json()
