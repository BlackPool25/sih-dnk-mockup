"""``DocumentData`` — the deterministic document payload (todo 11).

Assembled ONLY from three traceable sources:

- DB lookups through ``app.services.db_tools`` (the read-only tool surface):
  ``search_categories`` (category identity), ``lookup_hs_codes``,
  ``lookup_duty``, ``quote_lane``.
- The VALIDATED Shipment keys (``app.services.validate.validate_shipment``
  already ran): category_slug, quantity, weight_grams, destination_country.
- CLI order fields (optional): ``consignee``, ``value_minor``.

Validity is deterministic-only: ``DocumentData.model_validate`` (shape/types)
+ ``missing_required`` (completeness against ``pbe_field_schemas.required``) +
``validate_document_rules`` (the official PBE/CN22 filling rules of
pbe-iii-iv-fields.md §7) are the only gates — the LLM is NEVER the validator
and no model validates the document.  ``destination_country`` is deliberately a
plain string here: the ISO2 reality check lives in ``validate_shipment`` (CLI)
and completeness in ``missing_required`` (renderer) — a non-ISO2 value fails
``missing_required`` with ``consignee_details`` reported missing.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, model_validator

from app.schemas.shipment import Shipment
from app.services.db_tools import (
    lookup_duty,
    lookup_hs_codes,
    quote_lane,
    search_categories,
)

# The six renderable form types — the template map and the `documents` table
# doc_type column both key off these exact strings.
FORM_TYPES: tuple[str, ...] = (
    "PBE_III",
    "PBE_IV",
    "CN22",
    "CN23",
    "INVOICE",
    "PACKING_LIST",
)
FormType = Literal["PBE_III", "PBE_IV", "CN22", "CN23", "INVOICE", "PACKING_LIST"]


class DocumentData(BaseModel):
    """One renderable document's data — every field traceable.

    Fields come from the DB (hs_codes/duties/lane/category name), the
    validated Shipment (category_slug/quantity/weight_grams/
    destination_country) or the CLI order (consignee/value_minor — optional,
    rendered as "—" when omitted).
    """

    category_slug: str
    category_name: str
    quantity: int
    weight_grams: int
    destination_country: str
    form_type: FormType
    hs_codes: list[dict]  # verbatim rows from lookup_hs_codes()
    duties: list[dict]  # verbatim rows from lookup_duty()
    lane: dict  # verbatim row from quote_lane()
    # Declared value (INR minor units) + ITPS freight — None when the user
    # declined the optional value; duty rows stay visible separately.
    landed_cost_minor: int | None
    consignee: str | None = None  # optional CLI order field
    value_minor: int | None = None  # optional CLI order field

    # todo-14 filling-rule inputs (pbe-iii-iv-fields.md §7).  All optional —
    # the rules skip a check whose input is absent.  ``net_weight_g`` and
    # ``fob_minor`` get deterministic defaults (see ``_apply_defaults``) so a
    # document that only knows one figure is never rejected for lacking the
    # other.  ``unit_value_minor`` / ``piece_gross_g`` are per-piece values for
    # the Σ sub-piece rules; ``iec`` / ``gstin`` are the KYC/DGFT identifiers.
    net_weight_g: int | None = None
    fob_minor: int | None = None
    unit_value_minor: int | None = None
    piece_gross_g: int | None = None
    iec: str | None = None
    gstin: str | None = None

    @model_validator(mode="after")
    def _apply_defaults(self) -> DocumentData:
        """Deterministic defaults so a single known figure is never rejected.

        - ``net_weight_g`` defaults to ``weight_grams`` when only one weight is
          known (gross == net ⇒ gross ≤ 110% of net always holds).
        - ``fob_minor`` defaults to the declared cost value (``value_minor``)
          when only one value is known (FOB == invoice ⇒ FOB ≤ invoice holds).
        """
        if self.net_weight_g is None:
            self.net_weight_g = self.weight_grams
        if self.fob_minor is None and self.value_minor is not None:
            self.fob_minor = self.value_minor
        return self


def to_shipment(data: DocumentData) -> Shipment:
    """Project a DocumentData back onto the Shipment contract.

    The renderer's completeness gate (``missing_required``) only knows the
    four contract fields, so the deterministic values the document was
    assembled from are re-exposed as a Shipment — nothing is invented here.
    """
    return Shipment(
        product_category=data.category_slug,
        quantity=data.quantity,
        weight_grams=data.weight_grams,
        destination_country=data.destination_country,
        confidence="high",
    )


def build_document_data(
    shipment: Shipment,
    form_type: str,
    *,
    consignee: str | None = None,
    value_minor: int | None = None,
    iec: str | None = None,
    gstin: str | None = None,
) -> DocumentData:
    """Assemble a DocumentData from a VALIDATED Shipment + DB lookups.

    Raises:
        LookupError: category slug not found in ``product_categories``.
        LookupError/ValueError: from ``quote_lane`` (unknown lane / over cap).
        pydantic.ValidationError: ``form_type`` not one of the six form types.
    """
    cats = search_categories(shipment.product_category)
    category = next((c for c in cats if c["slug"] == shipment.product_category), None)
    if category is None:
        raise LookupError(
            f"category {shipment.product_category!r} not found in product_categories"
        )
    lane = quote_lane(shipment.destination_country, shipment.weight_grams)
    return DocumentData(
        category_slug=shipment.product_category,
        category_name=category["name"],
        quantity=shipment.quantity,
        weight_grams=shipment.weight_grams,
        destination_country=shipment.destination_country,
        form_type=form_type,
        hs_codes=lookup_hs_codes(shipment.product_category),
        duties=lookup_duty(shipment.destination_country),
        lane=lane,
        # Landed cost = declared value + freight, only when a value is given.
        landed_cost_minor=(
            value_minor + lane["cost_minor"] if value_minor is not None else None
        ),
        consignee=consignee,
        value_minor=value_minor,
        iec=iec,
        gstin=gstin,
    )


__all__ = [
    "FORM_TYPES",
    "DocumentData",
    "FormType",
    "build_document_data",
    "to_shipment",
]
