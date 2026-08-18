"""MCP-shaped tool registry — the curated model-facing surface.

The Gemini function-calling loop may only see these tools. Each tool
carries a precise JSON-schema for its parameters and a handler that wraps
``db_tools`` (or the voice-pipeline translate contract) and projects the
result to decision-relevant fields ONLY.

Anti-poisoning invariant: provenance (source_url, source_level, confidence,
is_estimate, effective_from/effective_to) stays in the application ledger
and is NEVER serialized into model context — the model gets exactly what it
needs to help the user fill the form, nothing more.

Tools are intentionally NOT exposed to the model loop: ``extract_draft``
(the model IS the extractor), ``validate_shipment`` (deterministic gate that
rejects sentinels which are legal mid-conversation), ``generate_docs``
(terminal action). Those remain API surfaces only.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Callable

import httpx

from app.services.db_tools import (
    get_config_flag,
    get_state_sales_tax,
    lookup_duty,
    lookup_hs_codes,
    quote_lane,
    search_categories,
)

VOICE_PIPELINE_URL = os.environ.get("VOICE_PIPELINE_URL", "http://127.0.0.1:8002")


@dataclass(frozen=True)
class MCPTool:
    """A model-callable tool: name, description, JSON-schema parameters, handler."""

    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[..., Any]


# --- parameter schemas (JSON-schema subset the SDK converter understands) ----


def _str_prop(description: str | None = None, *, default: str | None = None) -> dict[str, Any]:
    prop: dict[str, Any] = {"type": "string"}
    if description:
        prop["description"] = description
    if default is not None:
        prop["default"] = default
    return prop


def _int_prop(description: str | None = None) -> dict[str, Any]:
    prop: dict[str, Any] = {"type": "integer"}
    if description:
        prop["description"] = description
    return prop


def _object_schema(
    properties: dict[str, Any], required: list[str] | None = None
) -> dict[str, Any]:
    schema: dict[str, Any] = {"type": "object", "properties": properties}
    if required is not None:
        schema["required"] = required
    return schema


_SEARCH_CATEGORIES_SCHEMA = _object_schema(
    {"query": _str_prop("Category slug, name, or spoken Hindi/English word.")},
    required=["query"],
)

_LOOKUP_HS_CODES_SCHEMA = _object_schema(
    {
        "category": _str_prop("Product category slug to filter HS codes by."),
        "hs6": _str_prop("6-digit HS code prefix to filter by."),
    },
    required=[],
)

_LOOKUP_DUTY_SCHEMA = _object_schema(
    {
        "country_iso2": _str_prop("Destination country ISO-2 code (e.g. US)."),
        "hs6": _str_prop("Optional 6-digit HS code to narrow duty rows."),
    },
    required=["country_iso2"],
)

_QUOTE_LANE_SCHEMA = _object_schema(
    {
        "country_iso2": _str_prop("Destination country ISO-2 code (e.g. US)."),
        "weight_g": _int_prop("Shipment weight in grams."),
        "lane": _str_prop("Lane scheme.", default="ITPS"),
    },
    required=["country_iso2", "weight_g"],
)

_GET_STATE_SALES_TAX_SCHEMA = _object_schema(
    {"state_iso2": _str_prop("US state ISO-2 code (e.g. CA).")},
    required=["state_iso2"],
)

_GET_CONFIG_FLAG_SCHEMA = _object_schema(
    {"key": _str_prop("Config flag key (e.g. cn22.sdr_max).")},
    required=["key"],
)

_TRANSLATE_ITEM_SCHEMA = _object_schema(
    {
        "key": _str_prop("Stable identifier for the item."),
        "text": _str_prop("Source text (Hindi/Devanagari)."),
        "kind": _str_prop("translate or transliterate.", default="transliterate"),
    },
    required=["key", "text"],
)

_TRANSLATE_FREE_TEXT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "description": "Free-text items to transliterate/translate in one batch.",
            "items": _TRANSLATE_ITEM_SCHEMA,
        }
    },
    "required": ["items"],
}


# --- handlers (filtered projections — provenance never leaves the ledger) ----


def _search_categories_handler(query: str) -> list[dict[str, Any]]:
    rows = search_categories(query)
    return [
        {"slug": r["slug"], "name": r["name"], "hs6_default": r["hs6_default"]}
        for r in rows
    ]


def _lookup_hs_codes_handler(
    category: str | None = None, hs6: str | None = None
) -> list[dict[str, Any]]:
    rows = lookup_hs_codes(category=category, hs6=hs6)
    return [
        {
            "hs6": r["hs6"],
            "itc_hs_8": r["itc_hs_8"],
            "description": r["description"],
            "category_slug": r["category_slug"],
        }
        for r in rows
    ]


def _lookup_duty_handler(
    country_iso2: str, hs6: str | None = None
) -> list[dict[str, Any]]:
    rows = lookup_duty(country_iso2=country_iso2, hs6=hs6)
    return [
        {
            "country_iso2": r["country_iso2"],
            "hs6": r["hs6"],
            "rate_type": r["rate_type"],
            "rate_pct": r["rate_pct"],
            "amount_minor": r["amount_minor"],
            "threshold_minor": r["threshold_minor"],
            "currency": r["currency"],
            "basis": r["basis"],
        }
        for r in rows
    ]


def _quote_lane_handler(
    country_iso2: str, weight_g: int, lane: str = "ITPS"
) -> dict[str, Any]:
    try:
        result = quote_lane(country_iso2=country_iso2, weight_g=weight_g, lane=lane)
    except (LookupError, ValueError) as exc:
        return {"error": str(exc)}
    return {
        "cost_minor": result["cost_minor"],
        "weight_cap_g": result["weight_cap_g"],
        "volume_free": result["volume_free"],
        "transit_min_days": result["transit_min_days"],
        "transit_max_days": result["transit_max_days"],
    }


def _get_state_sales_tax_handler(state_iso2: str) -> dict[str, Any]:
    try:
        result = get_state_sales_tax(state_iso2)
    except KeyError as exc:
        return {"error": str(exc)}
    return {
        "state_iso2": result["state_iso2"],
        "state_name": result["state_name"],
        "state_rate_pct": result["state_rate_pct"],
        "combined_min_pct": result["combined_min_pct"],
        "combined_max_pct": result["combined_max_pct"],
        "nexus_threshold_usd": result["nexus_threshold_usd"],
    }


def _get_config_flag_handler(key: str) -> dict[str, Any]:
    try:
        result = get_config_flag(key)
    except KeyError as exc:
        return {"error": str(exc)}
    return {"flag_key": result["flag_key"], "flag_value": result["flag_value"]}


def _make_translate_free_text_handler(
    transport: httpx.BaseTransport | None = None,
) -> Callable[[list[dict[str, Any]]], dict[str, Any]]:
    """Returns the translate_free_text handler bound to a client.

    Failure is converted to an error dict — the tool loop must NEVER raise
    (translation is best-effort; the extraction must not die because the
    voice-pipeline is unreachable).
    """

    def handler(items: list[dict[str, Any]]) -> dict[str, Any]:
        client = httpx.Client(
            base_url=VOICE_PIPELINE_URL, timeout=60.0, transport=transport
        )
        try:
            response = client.post(
                "/translate/text",
                json={"items": items},
            )
            response.raise_for_status()
            return response.json()
        except Exception as exc:  # noqa: BLE001 - tool loop contract: never raise
            return {"error": f"translate_free_text unavailable: {exc}"}
        finally:
            client.close()

    return handler


def get_mcp_tools(
    translate_transport: httpx.BaseTransport | None = None,
) -> list[MCPTool]:
    """The curated model-facing tool registry (order is declaration order)."""
    return [
        MCPTool(
            name="search_categories",
            description=(
                "Find product categories by slug, name, or spoken Hindi/English "
                "keyword. Returns up to 5 matching categories with their default "
                "HS6 code."
            ),
            parameters=_SEARCH_CATEGORIES_SCHEMA,
            handler=_search_categories_handler,
        ),
        MCPTool(
            name="lookup_hs_codes",
            description=(
                "Look up HS codes for a product category or by 6-digit HS prefix. "
                "Returns the 8-digit ITC HS and description."
            ),
            parameters=_LOOKUP_HS_CODES_SCHEMA,
            handler=_lookup_hs_codes_handler,
        ),
        MCPTool(
            name="lookup_duty",
            description=(
                "Look up applicable import duty rates for a destination country, "
                "optionally narrowed by HS code."
            ),
            parameters=_LOOKUP_DUTY_SCHEMA,
            handler=_lookup_duty_handler,
        ),
        MCPTool(
            name="quote_lane",
            description=(
                "Quote a postal lane for a destination country and shipment "
                "weight. Returns cost in paise, weight cap, volume allowance and "
                "transit days."
            ),
            parameters=_QUOTE_LANE_SCHEMA,
            handler=_quote_lane_handler,
        ),
        MCPTool(
            name="get_state_sales_tax",
            description=(
                "Get US state sales-tax rate, combined min/max rates and nexus "
                "threshold for a state ISO-2 code."
            ),
            parameters=_GET_STATE_SALES_TAX_SCHEMA,
            handler=_get_state_sales_tax_handler,
        ),
        MCPTool(
            name="get_config_flag",
            description=(
                "Read a config flag (e.g. cn22.sdr_max, the SDR ceiling that "
                "selects CN22 vs CN23)."
            ),
            parameters=_GET_CONFIG_FLAG_SCHEMA,
            handler=_get_config_flag_handler,
        ),
        MCPTool(
            name="translate_free_text",
            description=(
                "Transliterate/translate free-text items (consignee names, "
                "addresses) from Hindi/Devanagari to English in one batched call. "
                "Use for any free-text field the user spoke in Hindi."
            ),
            parameters=_TRANSLATE_FREE_TEXT_SCHEMA,
            handler=_make_translate_free_text_handler(translate_transport),
        ),
    ]


__all__ = [
    "MCPTool",
    "VOICE_PIPELINE_URL",
    "get_mcp_tools",
]
