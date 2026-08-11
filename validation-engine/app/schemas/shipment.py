"""Shipment — the extraction contract's output schema.

Keys-only by design.  There are deliberately NO HS codes, duty rates, or any
customs VALUES here (the anti-hallucination contract): the extractor names
what the shipment IS (category, quantity, weight, destination), never what it
is worth or how it is taxed.  Downstream cost/tax research happens only via
the read-only db_tools surface, never by the extraction layer.

Sentinels encode "unstated" so the caller can ask the user instead of the
extractor inventing a value:

- ``quantity == -1``      → quantity not stated
- ``weight_grams == -1``  → weight not stated
- ``destination_country == "unknown"`` → destination not stated

The ISO2 *format* of ``destination_country`` is validated deterministically
in ``app.services.validate`` (schema-level allows any string, including the
``"unknown"`` sentinel).

``raw_transcript`` is stored for the demo log ONLY.  It is NEVER sent to any
model: ``GeminiExtractor`` excludes it from the prior-Shipment object it hands
back to the LLM on a re-prompt (see app/services/extract.py).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

# The EXACT seeded product-category slugs (product_categories table, todo 7).
# Verified against the live DB — do not edit these without re-checking psql.
CATEGORY_SLUGS: tuple[str, ...] = (
    "block-printed-textiles",
    "embroidered-bags-pouches",
    "embroidered-home-textiles",
    "handloom-scarves-stoles",
    "imitation-artisan-jewellery",
    "jute-products",
    "small-brass-metalware",
    "small-woodware",
)

# Literal[*CATEGORY_SLUGS] expands to the exact 8 slugs (PEP 646) and emits an
# `enum` in the JSON schema that GeminiExtractor sends as response_schema.
CategorySlug = Literal[*CATEGORY_SLUGS]

# Sentinel values the extractors use for "unstated" fields.
QUANTITY_UNSTATED = -1
WEIGHT_UNSTATED = -1
DESTINATION_UNSTATED = "unknown"


class Shipment(BaseModel):
    """One export shipment extracted from a spoken utterance.

    All values are ENGLISH schema values (category slugs, ISO2 country codes,
    gram-quantities) even when the user spoke hi/kn — the extraction contract
    normalises the language boundary, never the other way.
    """

    product_category: CategorySlug
    quantity: int  # -1 sentinel when unstated
    weight_grams: int  # -1 sentinel when unstated
    destination_country: (
        str  # ISO2, or "unknown" sentinel (format validated in validate.py)
    )
    confidence: Literal["high", "medium", "low"]
    raw_transcript: str | None = None  # demo-log ONLY; never sent to any model


__all__ = [
    "CATEGORY_SLUGS",
    "DESTINATION_UNSTATED",
    "QUANTITY_UNSTATED",
    "WEIGHT_UNSTATED",
    "CategorySlug",
    "Shipment",
]
