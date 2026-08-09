"""Deterministic-only validation — the SINGLE source of truth for verification.

The LLM NEVER validates anything.  A model response is parsed by Pydantic
(``Shipment.model_validate`` in extract.py) and then checked HERE — and only
here — against the business rules: ISO2 destination, quantity/weight bounds,
required-field completeness, and the OFFICIAL PBE/CN22 filling rules
(``validate_document_rules``, pbe-iii-iv-fields.md §7).  This module is pure
deterministic logic: no LLM calls, no imports from ``app.services.extract``.

Three surfaces:

- ``validate_shipment`` — raises ``ValidationError`` on a business-rule
  violation.  Sentinel values (-1 / "unknown") are the contract's way of
  saying "unstated" and are always accepted; the caller asks the user for the
  missing ones (see ``missing_required``).
- ``missing_required`` — queries ``pbe_field_schemas`` for the required fields
  of a form type and returns the PBE field keys whose source value in the
  Shipment is absent.  That list drives the "ask the user" flow.
- ``validate_document_rules`` — enforces the portal's official filling rules
  (gross ≤ 110% of net, FOB ≤ invoice, Σ sub-piece value/weight, description ↔
  HS/CTH, ITCH restricted-policy warning, DGFT/KYC gates) against a
  ``DocumentData``.  Returns a ``DocumentRuleResult`` whose ``errors`` carry
  the official rejection strings VERBATIM; the renderer raises on them.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
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
from app.services.db_tools import search_categories
from app.services.docs.document import DocumentData

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


# --- todo 14: the OFFICIAL PBE/CN22 filling rules (pbe-iii-iv-fields.md §7) ---
#
# Rejection strings are the portal's own error taxonomy (SOP v1.3 error table;
# dnk-sop-wayback.txt §3.2.1) — VERBATIM, never paraphrased.  Every rule is
# deterministic arithmetic / set logic / db_tools lookups; no model validates.

MSG_SUB_PIECE_VALUE = "Value of Sub pieces does not match"
MSG_SUB_PIECE_WEIGHT = "Weight of Sub pieces does not match"
MSG_GROSS_110_NET = "gross weight exceeds 110% of net weight"
MSG_FOB_INVOICE = "FOB value exceeds invoice value"
MSG_DESC_HS = "Description does not match with HS Code/CTH"
MSG_ITCH_RESTRICTED = "ITCH code not applicable for restricted policy"
MSG_DGFT_IEC_MISSING = "DGFT registration data missing"
MSG_KYC_IEC_OR_GSTIN = "booking requires at least one of IEC or GSTIN"

# HS/ITCH codes the corpus flags as restricted-policy (no standard-policy
# booking/claim): 5303 raw jute fibre (jute-products §1: "restricted-ish and
# biosecurity-heavy") and 4403 wood in the rough (small-woodware §4.1: raw
# timber/logs/sandalwood restricted/prohibited).  No restricted ITCH row is
# seeded for these — the warning fires only when such a code is selected.
_ITCH_RESTRICTED_POLICY_H6: frozenset[str] = frozenset({"5303", "4403"})

# Words too generic to prove a description↔HS match (tokens are ≥ 4 letters).
_DESC_STOPWORDS: frozenset[str] = frozenset(
    {"with", "other", "similar", "parts", "incl", "and", "or"}
)


@dataclass(frozen=True)
class DocumentRuleResult:
    """Outcome of the official filling-rule checks.

    ``errors`` reject the document (the renderer raises a pydantic
    ``ValidationError`` listing them); ``warnings`` surface e.g. an ITCH code
    not applicable for a restricted policy WITHOUT blocking.
    """

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _significant_words(text: str) -> set[str]:
    """Lowercase words of ≥ 4 letters minus the generic stopwords."""
    return {
        w for w in re.findall(r"[a-z]{4,}", text.lower())
        if w not in _DESC_STOPWORDS
    }


def _word_overlap(a: str, b: str) -> bool:
    return bool(_significant_words(a) & _significant_words(b))


def _canonical_category_name(category_slug: str) -> str | None:
    """The seeded DB name for a category slug — the trusted description."""
    for row in search_categories(category_slug):
        if row["slug"] == category_slug:
            return row["name"]
    return None


def _primary_hs_row(data: DocumentData) -> dict | None:
    """The first hs_codes row (lookup_hs_codes orders by hs6, deterministically)."""
    return data.hs_codes[0] if data.hs_codes else None


def _description_consistent(data: DocumentData, hs: dict) -> bool:
    """True iff the rendered description matches the chosen HS row.

    The description the form shows is the category name (PBE) or the HS row's
    own description (CN22/23 — identical by construction).  Word overlap with
    the chosen HS row's description proves consistency; a DB-curated category
    name is trusted even when it shares no literal word, because it was
    researched for the same HS code (e.g. "Embroidered Home Textiles" ↔ HS 6302
    "Bed linen…" share no word but are the same taxonomy).
    """
    hs_desc = hs.get("description") or ""
    rendered = (
        data.category_name
        if data.form_type in ("PBE_III", "PBE_IV")
        else hs_desc
    )
    if _word_overlap(rendered, hs_desc):
        return True
    canonical = _canonical_category_name(data.category_slug)
    return canonical is not None and rendered == canonical


def _itch_restricted(hs: dict) -> bool:
    """True iff the HS row's 6-digit code is restricted-policy ITCH."""
    for code in (hs.get("hs6"), hs.get("itc_hs_8")):
        if code:
            six = re.sub(r"\D", "", str(code))[:6]
            if six in _ITCH_RESTRICTED_POLICY_H6:
                return True
    return False


def validate_document_rules(document_data: DocumentData) -> DocumentRuleResult:
    """Enforce the official PBE/CN22 filling rules (pbe-iii-iv-fields.md §7).

    Deterministic-only — pure arithmetic / set logic / db_tools lookups; the
    LLM never validates.  ``errors`` carry the portal's official rejection
    strings VERBATIM; ``warnings`` (restricted-policy ITCH) do not block.

    Gate order (portal submission flow): KYC first (≥1 of IEC/GSTIN), then the
    DGFT/IEC gate, which applies once at least one KYC document exists.
    """
    data = DocumentData.model_validate(document_data)
    errors: list[str] = []
    warnings: list[str] = []

    if data.iec is None and data.gstin is None:
        errors.append(MSG_KYC_IEC_OR_GSTIN)
    elif data.iec is None:
        errors.append(MSG_DGFT_IEC_MISSING)

    # gross ≤ 110% of net — net defaults to the gross when only one weight is
    # known, so a parcel that exceeds the tolerance must declare it explicitly.
    if data.weight_grams > data.net_weight_g * 1.10:
        errors.append(MSG_GROSS_110_NET)

    # FOB ≤ invoice value — FOB defaults to the declared cost value.
    if data.fob_minor is not None and data.fob_minor > data.value_minor:
        errors.append(MSG_FOB_INVOICE)

    # Σ piece values ≤ parcel value (multi-piece, when a unit value is known).
    if (
        data.quantity > 1
        and data.unit_value_minor is not None
        and data.quantity * data.unit_value_minor > data.value_minor
    ):
        errors.append(MSG_SUB_PIECE_VALUE)

    # Σ piece gross weights ≤ parcel weight (multi-piece, when known).
    if (
        data.quantity > 1
        and data.piece_gross_g is not None
        and data.quantity * data.piece_gross_g > data.weight_grams
    ):
        errors.append(MSG_SUB_PIECE_WEIGHT)

    hs = _primary_hs_row(data)
    if hs is not None and not _description_consistent(data, hs):
        errors.append(MSG_DESC_HS)

    if hs is not None and _itch_restricted(hs):
        warnings.append(MSG_ITCH_RESTRICTED)

    return DocumentRuleResult(errors=errors, warnings=warnings)


__all__ = [
    "MSG_DESC_HS",
    "MSG_DGFT_IEC_MISSING",
    "MSG_FOB_INVOICE",
    "MSG_GROSS_110_NET",
    "MSG_ITCH_RESTRICTED",
    "MSG_KYC_IEC_OR_GSTIN",
    "MSG_SUB_PIECE_VALUE",
    "MSG_SUB_PIECE_WEIGHT",
    "DocumentRuleResult",
    "missing_required",
    "validate_document_rules",
    "validate_shipment",
]
