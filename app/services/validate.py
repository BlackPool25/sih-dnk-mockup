"""Deterministic-only validation — the SINGLE source of truth for verification.

The LLM NEVER validates anything.  A model response is parsed by Pydantic
(``Shipment.model_validate`` in extract.py) and then checked HERE — and only
here — against the business rules: ISO2 destination, quantity/weight bounds,
and required-field completeness.  This module is pure deterministic logic:
no LLM calls, no imports from ``app.services.extract``.

Two surfaces:

- ``validate_shipment`` — raises ``ValidationError`` on a business-rule
  violation.  Sentinel values (-1 / "unknown") are the contract's way of
  saying "unstated" and are always accepted; the caller asks the user for the
  missing ones (see ``missing_required``).
- ``missing_required`` — queries ``pbe_field_schemas`` for the required fields
  of a form type and returns the PBE field keys whose source value in the
  Shipment is absent.  That list drives the "ask the user" flow.
"""

from __future__ import annotations

import re
from typing import NoReturn

import pycountry
from pydantic import ValidationError
from sqlalchemy import select

from app.db import SessionLocal
from app.models import PbeFieldSchema
from app.schemas.shipment import (
    CATEGORY_SLUGS,
    DESTINATION_UNSTATED,
    QUANTITY_UNSTATED,
    WEIGHT_UNSTATED,
    Shipment,
)

_ISO2_RE = re.compile(r"^[A-Z]{2}$")

# Business-rule bounds (from the todo-10 spec).
_QUANTITY_MIN, _QUANTITY_MAX = 1, 10_000
_WEIGHT_MIN_G, _WEIGHT_MAX_G = 1, 50_000

# PBE field_key -> the Shipment field that can satisfy it (the extraction
# contract owns exactly these four shipment fields; every other required PBE
# field — iec, state_code, invoice_no_date, assessable_value, decl.* — is
# filled by asking the user, not by the extractor, and is NOT reported here).
_PBE_KEY_TO_SHIPMENT: dict[str, str] = {
    "product_description": "product_category",
    "cth": "product_category",
    "quantity_unit": "quantity",
    "gross_weight": "weight_grams",
    "net_weight": "weight_grams",
    "consignee_details": "destination_country",
}


def _error(loc: str, msg: str, input_value: object) -> dict:
    # pydantic-core requires the `ctx.error` for the value_error type; without
    # it `from_exception_data` raises TypeError("'error' required in context").
    return {
        "type": "value_error",
        "loc": (loc,),
        "msg": msg,
        "input": input_value,
        "ctx": {"error": ValueError(msg)},
    }


def _raise_validation_error(line_errors: list[dict]) -> NoReturn:
    raise ValidationError.from_exception_data("Shipment", line_errors)


def _is_real_iso2(country: str) -> bool:
    """True iff ``country`` is an actual ISO 3166-1 alpha-2 code.

    Format check (``^[A-Z]{2}$``) AND real-country check — "ZZ" passes the
    regex but is not a real code and must be rejected.
    """
    return (
        _ISO2_RE.match(country) is not None
        and pycountry.countries.get(alpha_2=country) is not None
    )


def validate_shipment(s: Shipment) -> Shipment:
    """Deterministic business validation; raises ValidationError on violation.

    Sentinel values are legal: ``quantity == -1``, ``weight_grams == -1`` and
    ``destination_country == "unknown"`` mean "unstated" — the extractor did
    not invent a value, and the caller asks the user (see ``missing_required``).
    """
    line_errors: list[dict] = []

    if s.quantity != QUANTITY_UNSTATED and not (
        _QUANTITY_MIN <= s.quantity <= _QUANTITY_MAX
    ):
        line_errors.append(
            _error(
                "quantity",
                f"quantity {s.quantity} outside {_QUANTITY_MIN}..{_QUANTITY_MAX} "
                f"(or the -1 sentinel)",
                s.quantity,
            )
        )

    if s.weight_grams != WEIGHT_UNSTATED and not (
        _WEIGHT_MIN_G <= s.weight_grams <= _WEIGHT_MAX_G
    ):
        line_errors.append(
            _error(
                "weight_grams",
                f"weight_grams {s.weight_grams} outside "
                f"{_WEIGHT_MIN_G}..{_WEIGHT_MAX_G} (or the -1 sentinel)",
                s.weight_grams,
            )
        )

    if s.destination_country != DESTINATION_UNSTATED and not _is_real_iso2(
        s.destination_country
    ):
        line_errors.append(
            _error(
                "destination_country",
                f"destination_country {s.destination_country!r} is not a real ISO2 "
                f"country code (or the {DESTINATION_UNSTATED!r} sentinel)",
                s.destination_country,
            )
        )

    if s.product_category not in CATEGORY_SLUGS:
        line_errors.append(
            _error(
                "product_category",
                f"product_category {s.product_category!r} not in the seeded slug set",
                s.product_category,
            )
        )

    if line_errors:
        _raise_validation_error(line_errors)
    return s


def _source_present(s: Shipment, shipment_key: str) -> bool:
    """Is the Shipment's source value for ``shipment_key`` actually known?"""
    if shipment_key == "quantity":
        return s.quantity != QUANTITY_UNSTATED
    if shipment_key == "weight_grams":
        return s.weight_grams != WEIGHT_UNSTATED
    if shipment_key == "destination_country":
        return _is_real_iso2(s.destination_country)  # "unknown" sentinel = absent
    if shipment_key == "product_category":
        return s.product_category in CATEGORY_SLUGS
    return False


def missing_required(s: Shipment, form_type: str) -> list[str]:
    """Required PBE fields of ``form_type`` the extractor did NOT supply.

    Queries ``pbe_field_schemas`` (required=true, ordered by id) and returns
    the field keys whose source value in the Shipment is absent (sentinel -1 /
    non-ISO2 destination).  Only the four contract fields are ever considered;
    required PBE fields outside the Shipment contract (iec, state_code, …) are
    not extractor concerns and are never reported here.

    The result drives the "ask the user" flow: for each key in the returned
    list, the caller prompts the user for that field.
    """
    with SessionLocal() as session:
        required_keys = session.scalars(
            select(PbeFieldSchema.field_key)
            .where(
                PbeFieldSchema.form_type == form_type,
                PbeFieldSchema.required.is_(True),
            )
            .order_by(PbeFieldSchema.id)
        ).all()

    missing = []
    for key in required_keys:
        shipment_key = _PBE_KEY_TO_SHIPMENT.get(key)
        if shipment_key is not None and not _source_present(s, shipment_key):
            missing.append(key)
    return missing


__all__ = [
    "missing_required",
    "validate_shipment",
]
