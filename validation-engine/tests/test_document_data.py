"""Tests for the Wave-1 ``app.services.docs.document`` rework — ``field_values``
as the SINGLE source of rendered values.

These hit the LIVE seeded DB (no fixtures — the container must be up and the
``pbe_field_schemas`` table seeded), like the rest of the suite.  Every test
builds a complete DocumentData via ``build_document_data`` from a validated
Shipment, exactly as the renderer does today.

Pinned regressions:
- F7 duplicate: ``consignee_details`` must NOT append " / US" (the old
  renderer glued the destination country onto the consignee).
- F2: ``iec`` / ``gstin_or_as_applicable`` must be derived into field_values.
"""

import pytest
from pydantic import ValidationError

from app.schemas.shipment import Shipment
from app.services.docs.document import DocumentData, SenderBlock, build_document_data
from app.services.validate import missing_required, validate_shipment


def _validated_shipment() -> Shipment:
    """A complete, validated Shipment (embroidered-home-textiles -> US)."""
    return validate_shipment(
        Shipment(
            product_category="embroidered-home-textiles",
            quantity=8,
            weight_grams=400,
            destination_country="US",
            confidence="high",
        )
    )


def _build(form_type: str = "PBE_IV", **kw: object) -> DocumentData:
    """A complete DocumentData from REAL DB lookups: validated shipment +
    iec/gstin/value_minor/consignee (the todo-14 gate inputs).  Keyword
    overrides replace the defaults (e.g. consignee=None omits it)."""
    kwargs: dict[str, object] = {
        "consignee": "Jane Doe, 123 Main St",
        "value_minor": 200000,
        "iec": "IN1234567890",
        "gstin": "29ABCDE1234F1Z5",
    }
    kwargs.update(kw)
    return build_document_data(_validated_shipment(), form_type, **kwargs)


def test_resolve_value_provided_over_computed() -> None:
    """A provided field_value renders; a provided value beats a derived one."""
    data = _build()
    patched = data.model_copy(
        update={"field_values": {**data.field_values, "scheme_code": "rodtep"}}
    )
    assert patched.resolve_value("scheme_code") == "rodtep"

    # product_description is DERIVED from the category name — a provided value
    # must win over that derivation.
    patched = data.model_copy(
        update={
            "field_values": {
                **data.field_values,
                "product_description": "Custom silk scarf",
            }
        }
    )
    assert patched.resolve_value("product_description") == "Custom silk scarf"


def test_resolve_value_absent_renders_dash() -> None:
    """A schema field with no provided value and no derivation renders "—"."""
    data = _build()
    assert data.resolve_value("boe_no") == "—"


def test_field_values_verified_against_db_schema() -> None:
    """Every provided field_value is checked against pbe_field_schemas metadata."""
    with pytest.raises(ValidationError):
        _build(field_values={"scheme_code": "bogus"})  # options: drawback/rodtep/rosctl
    with pytest.raises(ValidationError):
        _build(field_values={"export_duty_amount": "not-an-int"})  # money
    with pytest.raises(ValidationError):
        _build("PBE_III", field_values={"ecomm_url": "not-a-url"})  # url (PBE_III only)
    # control: a valid option value passes the same validator
    assert _build(field_values={"scheme_code": "rodtep"}).resolve_value("scheme_code") == "rodtep"


def test_consignee_details_does_not_append_country() -> None:
    """F7: consignee_details is the consignee verbatim — NO " / US" suffix."""
    data = _build()
    assert data.resolve_value("consignee_details") == "Jane Doe, 123 Main St"
    assert data.resolve_value("destination_country") == "US"


def test_sender_block_shape() -> None:
    """SenderBlock round-trips its four optional fields; empty = all None."""
    sender = SenderBlock(
        name_address="Acme Exports, Delhi",
        sender_ref="IOSS0001",
        non_delivery="return",
        num_invoices="2",
    )
    assert sender.name_address == "Acme Exports, Delhi"
    assert sender.sender_ref == "IOSS0001"
    assert sender.non_delivery == "return"
    assert sender.num_invoices == "2"
    empty = SenderBlock()
    assert empty.name_address is None
    assert empty.sender_ref is None
    assert empty.non_delivery is None
    assert empty.num_invoices is None


def test_money_and_number_formatting() -> None:
    """resolve_value is the single formatting point: money/number units."""
    data = _build()
    assert data.resolve_value("assessable_value") == "₹2,000.00"
    assert data.resolve_value("quantity_unit") == "8 Nos"
    assert data.resolve_value("gross_weight") == "400 g"


def test_iec_gstin_derived_into_field_values() -> None:
    """F2: iec / gstin_or_as_applicable are derived into field_values."""
    data = _build()
    assert data.resolve_value("iec") == "IN1234567890"
    assert data.resolve_value("gstin_or_as_applicable") == "29ABCDE1234F1Z5"


# --- missing_required (wave 2: completeness against ALL 7 DB-required keys) ---

def test_missing_required_reports_assessable_value() -> None:
    """F3: a document without a declared value reports assessable_value."""
    data = _build(consignee=None, value_minor=None)
    missing = missing_required(data, "PBE_IV")
    assert "assessable_value" in missing
    assert "consignee_details" in missing


def test_missing_required_covers_all_seven() -> None:
    """Every pbe_field_schemas.required key is covered, in id order."""
    bare = DocumentData(
        category_slug="embroidered-home-textiles",
        category_name="Embroidered Home Textiles",
        quantity=8,
        weight_grams=400,
        destination_country="US",
        form_type="PBE_IV",
        hs_codes=[],
        duties=[],
        lane={},
        landed_cost_minor=None,
    )
    assert missing_required(bare, "PBE_IV") == [
        "consignee_details",
        "product_description",
        "cth",
        "quantity_unit",
        "gross_weight",
        "net_weight",
        "assessable_value",
    ]


def test_missing_required_complete_document_empty() -> None:
    """A fully-supplied document (consignee + value + shipment) misses nothing."""
    data = _build()
    assert missing_required(data, "PBE_IV") == []
