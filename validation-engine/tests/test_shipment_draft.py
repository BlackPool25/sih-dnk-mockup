"""ShipmentDraft — the multi-turn accumulation contract.

Pins: sentinels, default product_category=None, to_shipment() projection
(and its CategoryUnknownError when the category is not yet disambiguated),
and that Shipment stays the strict single-utterance contract (no consignee /
value_minor fields leaked into it).
"""

from __future__ import annotations

import pytest

from app.schemas.shipment import (
    CONSIGNEE_UNSTATED,
    DESTINATION_UNSTATED,
    QUANTITY_UNSTATED,
    VALUE_UNSTATED,
    WEIGHT_UNSTATED,
    Shipment,
    ShipmentDraft,
)
from app.services.extract import CategoryUnknownError


def test_draft_defaults_are_sentinels() -> None:
    draft = ShipmentDraft()
    assert draft.product_category is None
    assert draft.quantity == QUANTITY_UNSTATED
    assert draft.weight_grams == WEIGHT_UNSTATED
    assert draft.destination_country == DESTINATION_UNSTATED
    assert draft.consignee == CONSIGNEE_UNSTATED
    assert draft.value_minor == VALUE_UNSTATED
    assert draft.confidence == "low"


def test_draft_accepts_all_six_fields() -> None:
    draft = ShipmentDraft(
        product_category="jute-products",
        quantity=12,
        weight_grams=500,
        destination_country="DE",
        consignee="John Doe, 123 Berlin Str",
        value_minor=1500000,
        confidence="high",
    )
    assert draft.product_category == "jute-products"
    assert draft.quantity == 12
    assert draft.weight_grams == 500
    assert draft.destination_country == "DE"
    assert draft.consignee == "John Doe, 123 Berlin Str"
    assert draft.value_minor == 1500000
    assert draft.confidence == "high"


def test_to_shipment_projects_known_category() -> None:
    draft = ShipmentDraft(
        product_category="embroidered-home-textiles",
        quantity=8,
        weight_grams=400,
        destination_country="US",
        consignee="Jane Doe, 123 Main St",
        value_minor=200000,
        confidence="high",
        raw_transcript="ek gaadi ka kapa",
    )
    shipment = draft.to_shipment()
    assert isinstance(shipment, Shipment)
    assert shipment.product_category == "embroidered-home-textiles"
    assert shipment.quantity == 8
    assert shipment.weight_grams == 400
    assert shipment.destination_country == "US"
    assert shipment.confidence == "high"
    # The demo-log transcript never crosses the contract boundary.
    assert shipment.raw_transcript is None
    # Consignee/value are draft-only — they must not leak into Shipment.
    assert not hasattr(shipment, "consignee")
    assert not hasattr(shipment, "value_minor")


def test_to_shipment_raises_when_category_unset() -> None:
    draft = ShipmentDraft(quantity=3, weight_grams=250, destination_country="AE")
    with pytest.raises(CategoryUnknownError):
        draft.to_shipment()
