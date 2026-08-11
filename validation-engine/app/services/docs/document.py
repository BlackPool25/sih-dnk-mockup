"""``DocumentData`` — the deterministic document payload (todo 11, wave 1).

``field_values`` is the SINGLE source of every rendered PBE field value:
- DB lookups through ``app.services.db_tools`` (category identity, HS rows,
  duties, lane quote) feed the DERIVED entries at build time;
- the VALIDATED Shipment keys (``validate_shipment`` already ran) feed the
  derived weight/quantity/destination entries;
- CLI order fields (``consignee``, ``value_minor``, ``iec``, ``gstin``, …)
  feed their derived entries — a provided ``field_values`` entry ALWAYS wins
  over a derived one (merge order: ``{**derived, **provided}``).

Every provided entry is verified against the ``pbe_field_schemas`` DB
metadata (``value_type`` / ``options``) by ``_verify_field_values``, and
``resolve_value(field_key)`` is the single formatting point (money/number
units) — provided value or "—" when absent.  Later waves (validate.py,
renderer, CLI) read ONLY ``resolve_value``.

Validity is deterministic-only: ``DocumentData.model_validate`` (shape/types)
+ ``missing_required`` (completeness against ``pbe_field_schemas.required``) +
``validate_document_rules`` (the official PBE/CN22 filling rules of
pbe-iii-iv-fields.md §7) are the only gates — the LLM is NEVER the validator
and no model validates the document.  ``destination_country`` is deliberately a
plain string here: the ISO2 reality check lives in ``validate_shipment`` (CLI)
and completeness in ``missing_required`` (renderer) — a non-ISO2 value fails
``missing_required`` with ``consignee_details`` reported missing.

# allow: SIZE_OK — one cohesive unit (model + its two validators + builder +
# projection) whose public surface is pinned by waves 2-5; splitting the
# validators or builder out of the model file would fragment the single
# import surface the later waves rely on.
"""

from __future__ import annotations

import re
from typing import Literal, NoReturn

from pydantic import BaseModel, Field, ValidationError, model_validator
from sqlalchemy import select

from app.db import SessionLocal
from app.models import PbeFieldSchema
from app.schemas.shipment import Shipment
from app.services.cache import cache
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

_URL_RE = r"^https?://"


class SenderBlock(BaseModel):
    """The exporter/sender block (CN22/CN23 + invoice) — all optional.

    The seller supplies these via the CLI later (wave 4); until then every
    field is None and renders "—" (the exporter fills them at the counter).
    """

    name_address: str | None = None
    sender_ref: str | None = None  # Customs reference (IOSS for the EU) — DNK SOP
    non_delivery: str | None = None  # abandoned / return / non-priority
    num_invoices: str | None = None  # number of invoices/licenses/certificates


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

    # Wave-1: the single source of rendered field values.  ``field_values``
    # holds every PBE field value (derived at build time or provided by the
    # CLI); ``field_schema`` is the pbe_field_schemas metadata keyed by
    # field_key (value_type/options/label) used to verify provided values.
    field_values: dict[str, int | str] = Field(default_factory=dict)
    field_schema: dict[str, dict] = Field(default_factory=dict)
    sender: SenderBlock = Field(default_factory=SenderBlock)

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

    @model_validator(mode="after")
    def _verify_field_values(self) -> DocumentData:
        """Every provided field_value is checked against pbe_field_schemas.

        - number/money: int (a str is coerced via int(); anything else, or a
          negative money value, is rejected).
        - boolean / string-with-options: must be one of the options' values
          when the schema row declares any (the DB stores a JSON null literal
          on rows WITHOUT options — detect via ``options and options.get(...)``,
          never ``is not None``).
        - url: must match ``^https?://``.
        - a key absent from ``field_schema`` is skipped (defensive: extra
          values may exist for forms without schema rows).
        """
        for key, value in self.field_values.items():
            spec = self.field_schema.get(key)
            if spec is None:
                continue  # defensive — no schema row for this form/key
            vt = spec["value_type"]
            label = spec["label"]
            if vt in ("number", "money"):
                if not isinstance(value, int):
                    try:
                        value = int(value)
                    except (TypeError, ValueError):
                        self._field_value_error(
                            key, label,
                            f"expects an integer for value_type {vt!r}, "
                            f"got {value!r}",
                        )
                    self.field_values[key] = value
                if vt == "money" and value < 0:
                    self._field_value_error(
                        key, label, f"money value must not be negative, got {value!r}"
                    )
            elif vt in ("boolean", "string"):
                allowed = (spec["options"] or {}).get("values")
                if allowed and value not in allowed:
                    self._field_value_error(
                        key, label,
                        f"must be one of {allowed}, got {value!r}",
                    )
            elif vt == "url":
                if not re.match(_URL_RE, str(value)):
                    self._field_value_error(
                        key, label, f"expects a URL starting with http(s)://, got {value!r}"
                    )
        return self

    def _field_value_error(self, key: str, label: str, detail: str) -> NoReturn:
        """Raise a pydantic ValidationError locating the offending entry."""
        msg = f"field {key!r} ({label}) {detail}"
        raise ValidationError.from_exception_data(
            "DocumentData",
            [{
                "type": "value_error",
                "loc": ("field_values", key),
                "msg": msg,
                "input": self.field_values.get(key),
                "ctx": {"error": ValueError(msg)},
            }],
        )

    def resolve_value(self, field_key: str) -> str:
        """The single formatting point for a rendered field — "—" when absent.

        Looks ONLY at ``field_values`` (derived at build time or provided by
        the CLI): a provided value always wins over a derivation.  Formatting
        follows the field's ``value_type``: money renders through ``_money``,
        quantity_unit/weights get their unit suffixes, everything else is
        ``str(raw)``.
        """
        raw = self.field_values.get(field_key)
        if raw is None:
            return "—"
        vt = self.field_schema.get(field_key, {}).get("value_type")
        if vt == "money":
            return _money(int(raw))
        if vt == "number":
            if field_key == "quantity_unit":
                return f"{raw} Nos"
            if field_key in ("gross_weight", "net_weight"):
                return f"{raw} g"
            return str(raw)
        return str(raw)


def _money(minor: int | None) -> str:
    """Render an INR minor-unit amount as rupees — "—" when absent."""
    if minor is None:
        return "—"
    return f"₹{minor / 100:,.2f}"


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
    field_values: dict[str, int | str] | None = None,
    sender: SenderBlock | None = None,
    net_weight_g: int | None = None,
    fob_minor: int | None = None,
    unit_value_minor: int | None = None,
    piece_gross_g: int | None = None,
) -> DocumentData:
    """Assemble a DocumentData from a VALIDATED Shipment + DB lookups.

    Derived field_values come from the category name, the primary HS row, the
    validated shipment, and the optional CLI order fields (consignee /
    value_minor / iec / gstin).  Provided ``field_values`` entries override
    derived ones (``{**derived, **provided}``).

    Raises:
        LookupError: category slug not found in ``product_categories``.
        LookupError/ValueError: from ``quote_lane`` (unknown lane / over cap).
        pydantic.ValidationError: ``form_type`` not one of the six form types,
            or a provided field_value violates its pbe_field_schemas metadata.
    """
    cats = search_categories(shipment.product_category)
    category = next((c for c in cats if c["slug"] == shipment.product_category), None)
    if category is None:
        raise LookupError(
            f"category {shipment.product_category!r} not found in product_categories"
        )
    lane = quote_lane(shipment.destination_country, shipment.weight_grams)
    hs_codes = lookup_hs_codes(shipment.product_category)
    cache_key = f"field_schemas:{form_type}"
    cached = cache.get(cache_key)
    if cached is not None:
        field_schema = cached
    else:
        with SessionLocal() as session:
            rows = session.scalars(
                select(PbeFieldSchema)
                .where(PbeFieldSchema.form_type == form_type)
                .order_by(PbeFieldSchema.id)
            ).all()
        field_schema = {
            r.field_key: {"value_type": r.value_type, "options": r.options, "label": r.label}
            for r in rows
        }
        cache.set(cache_key, field_schema)

    # Derived field values — every key is a pbe_field_schemas field_key.
    primary = hs_codes[0] if hs_codes else None
    derived: dict[str, int | str] = {
        "product_description": category["name"],
        "quantity_unit": shipment.quantity,
        "gross_weight": shipment.weight_grams,
        "net_weight": shipment.weight_grams,
        "destination_country": shipment.destination_country,
    }
    if primary is not None:
        derived["cth"] = primary["hs6"][:4]
    if consignee is not None:
        derived["consignee_details"] = consignee  # F7: verbatim, no country suffix
    if iec is not None:
        derived["iec"] = iec
    if gstin is not None:
        derived["gstin_or_as_applicable"] = gstin
    if value_minor is not None:
        derived["assessable_value"] = value_minor
        derived["amount_inr"] = value_minor
        derived["fob_value"] = value_minor
        derived["currency"] = "INR"
    if primary is not None:
        derived["hs_code"] = primary["hs6"]
        derived["ritc_itc_hs"] = primary["itc_hs_8"] or primary["hs6"]
        derived["si_no"] = "1"  # single-item consignment — line 1

    merged = {**derived, **(field_values or {})}  # provided always wins
    return DocumentData(
        category_slug=shipment.product_category,
        category_name=category["name"],
        quantity=shipment.quantity,
        weight_grams=shipment.weight_grams,
        destination_country=shipment.destination_country,
        form_type=form_type,
        hs_codes=hs_codes,
        duties=lookup_duty(shipment.destination_country),
        lane=lane,
        # Landed cost = declared value + freight, only when a value is given.
        landed_cost_minor=(
            value_minor + lane["cost_minor"] if value_minor is not None else None
        ),
        consignee=consignee,
        value_minor=value_minor,
        net_weight_g=net_weight_g,
        fob_minor=fob_minor,
        unit_value_minor=unit_value_minor,
        piece_gross_g=piece_gross_g,
        iec=iec,
        gstin=gstin,
        field_values=merged,
        field_schema=field_schema,
        sender=sender or SenderBlock(),
    )


__all__ = [
    "FORM_TYPES",
    "DocumentData",
    "FormType",
    "SenderBlock",
    "_money",
    "build_document_data",
    "to_shipment",
]
