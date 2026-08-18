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
CONSIGNEE_UNSTATED = "unknown"
VALUE_UNSTATED = -1


class Shipment(BaseModel):
    """One export shipment extracted from a spoken utterance.

    All values are ENGLISH schema values (category slugs, ISO2 country codes,
    gram-quantities) even when the user spoke hi/kn — the extraction contract
    normalises the language boundary, never the other way.
    """

    product_category: CategorySlug
    quantity: int  # -1 sentinel when unstated
    weight_grams: int  # -1 sentinel when unstated
    destination_country: str  # ISO2, or "unknown" sentinel (format validated in validate.py)
    confidence: Literal["high", "medium", "low"]
    raw_transcript: str | None = None  # demo-log ONLY; never sent to any model


class ShipmentDraft(BaseModel):
    """Multi-turn accumulation schema — superset of ``Shipment`` plus the two
    optional order fields the PBE completeness gates need.

    Same English-schema-value contract and sentinel discipline as ``Shipment``:

    - ``product_category == None``  → category not yet disambiguated (never an
      invented slug; once set it is a real ``CategorySlug``)
    - ``quantity == -1``            → quantity not stated
    - ``weight_grams == -1``        → weight not stated
    - ``destination_country == "unknown"`` → destination not stated
    - ``consignee == "unknown"``    → consignee not stated
    - ``value_minor == -1``         → declared value not stated (INR minor units)

    ``raw_transcript`` is stored for the demo log ONLY and is never sent to any
    model (``GeminiDraftExtractor`` excludes it from prior-draft reprompts).
    """

    product_category: CategorySlug | None = None
    quantity: int = QUANTITY_UNSTATED
    weight_grams: int = WEIGHT_UNSTATED
    destination_country: str = DESTINATION_UNSTATED
    consignee: str = CONSIGNEE_UNSTATED
    value_minor: int = VALUE_UNSTATED
    confidence: Literal["high", "medium", "low"] = "low"
    raw_transcript: str | None = None

    def to_shipment(self) -> "Shipment":
        """Project the draft onto the strict ``Shipment`` contract.

        Raises ``CategoryUnknownError`` (imported lazily to avoid a cycle) when
        the category is not yet disambiguated — the caller must ask first.
        """
        if self.product_category is None:
            from app.services.extract import CategoryUnknownError

            raise CategoryUnknownError(
                "product_category is None — disambiguate the category before "
                "projecting the draft onto the Shipment contract"
            )
        return Shipment(
            product_category=self.product_category,
            quantity=self.quantity,
            weight_grams=self.weight_grams,
            destination_country=self.destination_country,
            confidence=self.confidence,
            raw_transcript=None,
        )


__all__ = [
    "CATEGORY_SLUGS",
    "CONSIGNEE_UNSTATED",
    "DESTINATION_UNSTATED",
    "QUANTITY_UNSTATED",
    "VALUE_UNSTATED",
    "WEIGHT_UNSTATED",
    "CategorySlug",
    "Shipment",
    "ShipmentDraft",
]
