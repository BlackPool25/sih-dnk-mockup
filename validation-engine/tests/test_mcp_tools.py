"""MCP-shaped tool registry — the curated model-facing surface.

Each tool carries name / description / JSON-schema parameters / handler.
Handlers wrap ``db_tools`` and project to decision-relevant fields ONLY —
provenance (source_url, source_level, confidence, is_estimate, effective
windows) stays in the app ledger and never enters model context, so the
model cannot be poisoned by data it does not need.

Translate tool hits the voice-pipeline /translate/text contract over a
sync httpx client with an injectable transport (tests use MockTransport).
"""

from __future__ import annotations

import json

import httpx

from app.services.mcp_tools import MCPTool, get_mcp_tools

EXPECTED_TOOLS = {
    "search_categories",
    "lookup_hs_codes",
    "lookup_duty",
    "quote_lane",
    "get_state_sales_tax",
    "get_config_flag",
    "translate_free_text",
}


def test_registry_exposes_seven_curated_tools() -> None:
    tools = get_mcp_tools()
    assert {t.name for t in tools} == EXPECTED_TOOLS


def test_every_tool_is_mcptool_with_description_and_schema() -> None:
    for tool in get_mcp_tools():
        assert isinstance(tool, MCPTool)
        assert tool.description
        assert tool.parameters  # non-empty JSON schema
        assert callable(tool.handler)


def test_required_params_precise() -> None:
    by_name = {t.name: t.parameters for t in get_mcp_tools()}
    assert by_name["search_categories"]["required"] == ["query"]
    assert by_name["lookup_hs_codes"]["required"] == []
    assert by_name["lookup_duty"]["required"] == ["country_iso2"]
    assert by_name["quote_lane"]["required"] == ["country_iso2", "weight_g"]
    assert by_name["get_state_sales_tax"]["required"] == ["state_iso2"]
    assert by_name["get_config_flag"]["required"] == ["key"]
    assert by_name["translate_free_text"]["required"] == ["items"]


def test_param_types_precise() -> None:
    props = {t.name: t.parameters["properties"] for t in get_mcp_tools()}
    assert props["quote_lane"]["weight_g"]["type"] == "integer"
    assert props["quote_lane"]["lane"]["default"] == "ITPS"
    assert props["lookup_duty"]["hs6"]["type"] == "string"
    assert props["get_state_sales_tax"]["state_iso2"]["type"] == "string"
    items = props["translate_free_text"]["items"]
    assert items["type"] == "array"
    assert items["items"]["type"] == "object"
    assert "key" in items["items"]["properties"]
    assert "text" in items["items"]["properties"]
    assert "kind" in items["items"]["properties"]


def test_search_categories_filters_provenance() -> None:
    tool = next(t for t in get_mcp_tools() if t.name == "search_categories")
    rows = tool.handler(query="jute")
    assert rows
    for row in rows:
        assert set(row) <= {"slug", "name", "hs6_default"}
        assert "source_url" not in row
        assert "confidence" not in row
        assert "is_estimate" not in row


def test_lookup_duty_filters_provenance() -> None:
    tool = next(t for t in get_mcp_tools() if t.name == "lookup_duty")
    rows = tool.handler(country_iso2="US")
    assert rows
    allowed = {
        "country_iso2",
        "hs6",
        "rate_type",
        "rate_pct",
        "amount_minor",
        "threshold_minor",
        "currency",
        "basis",
    }
    for row in rows:
        assert set(row) <= allowed


def test_quote_lane_filters_provenance() -> None:
    tool = next(t for t in get_mcp_tools() if t.name == "quote_lane")
    result = tool.handler(country_iso2="US", weight_g=100)
    assert set(result) == {
        "cost_minor",
        "weight_cap_g",
        "volume_free",
        "transit_min_days",
        "transit_max_days",
    }


def test_get_config_flag_filters_provenance() -> None:
    tool = next(t for t in get_mcp_tools() if t.name == "get_config_flag")
    assert tool.handler(key="cn22.sdr_max") == {
        "flag_key": "cn22.sdr_max",
        "flag_value": 300,
    }


def test_get_state_sales_tax_filters_provenance() -> None:
    tool = next(t for t in get_mcp_tools() if t.name == "get_state_sales_tax")
    result = tool.handler(state_iso2="CA")
    assert set(result) == {
        "state_iso2",
        "state_name",
        "state_rate_pct",
        "combined_min_pct",
        "combined_max_pct",
        "nexus_threshold_usd",
    }


def test_lookup_hs_codes_filters_provenance() -> None:
    tool = next(t for t in get_mcp_tools() if t.name == "lookup_hs_codes")
    rows = tool.handler(category="jute-products")
    assert rows
    for row in rows:
        assert set(row) <= {"hs6", "itc_hs_8", "description", "category_slug"}


def test_quote_lane_handler_never_raises_on_unknown_lane() -> None:
    # Model may guess a lane scheme that does not exist (e.g. "express").
    # The handler must return an error dict the model can see and recover
    # from — never propagate LookupError up through the tool loop (500).
    tool = next(t for t in get_mcp_tools() if t.name == "quote_lane")
    result = tool.handler(country_iso2="US", weight_g=100, lane="express")
    assert isinstance(result, dict)
    assert "error" in result
    assert "express" in result["error"]


def test_get_state_sales_tax_handler_never_raises_on_unknown_state() -> None:
    tool = next(t for t in get_mcp_tools() if t.name == "get_state_sales_tax")
    result = tool.handler(state_iso2="ZZ")
    assert isinstance(result, dict)
    assert "error" in result


def test_get_config_flag_handler_never_raises_on_unknown_key() -> None:
    tool = next(t for t in get_mcp_tools() if t.name == "get_config_flag")
    result = tool.handler(key="does.not.exist")
    assert isinstance(result, dict)
    assert "error" in result


def test_translate_free_text_posts_batched_payload() -> None:
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "items": [
                    {"key": "consignee", "english": "Shikha Sharma"},
                    {"key": "note", "english": "Ramesh Kumar"},
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    tool = next(
        t
        for t in get_mcp_tools(translate_transport=transport)
        if t.name == "translate_free_text"
    )
    result = tool.handler(
        items=[
            {"key": "consignee", "text": "शिखा शर्मा", "kind": "transliterate"},
            {"key": "note", "text": "रमेश कुमार", "kind": "transliterate"},
        ]
    )
    assert captured["url"].endswith("/translate/text")
    assert captured["body"] == {
        "items": [
            {"key": "consignee", "text": "शिखा शर्मा", "kind": "transliterate"},
            {"key": "note", "text": "रमेश कुमार", "kind": "transliterate"},
        ]
    }
    assert result == {
        "items": [
            {"key": "consignee", "english": "Shikha Sharma"},
            {"key": "note", "english": "Ramesh Kumar"},
        ]
    }


def test_translate_free_text_never_raises_on_upstream_failure() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(502, json={"detail": "Sarvam API error 500: boom"})

    transport = httpx.MockTransport(handler)
    tool = next(
        t
        for t in get_mcp_tools(translate_transport=transport)
        if t.name == "translate_free_text"
    )
    result = tool.handler(
        items=[{"key": "consignee", "text": "शिखा", "kind": "transliterate"}]
    )
    assert "error" in result  # dict, never raised
