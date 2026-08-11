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
  of a form type and returns the PBE field keys with no resolvable value in a
  ``DocumentData`` (``resolve_value`` is the single formatting point — a
  field is missing when it renders "—").  Now covers ALL required fields,
  including ``assessable_value`` (the F3 gap).  That list drives the "ask the
  user" flow.
- ``validate_document_rules`` — enforces the portal's official filling rules
  (gross ≤ 110% of net, FOB ≤ invoice, Σ sub-piece value/weight, description ↔
  HS/CTH, ITCH restricted-policy warning, DGFT/KYC gates) against a
  ``DocumentData``.  The rule catalog is DB-DRIVEN: the ENABLED rows of the
  ``filling_rules`` table (Wave 0) are loaded per call — each row contributes
  its evaluator (keyed by ``rule_key``), its ``params``, its ``severity`` and
  its VERBATIM ``message``.  Returns a ``DocumentRuleResult`` whose ``errors``
  carry the official rejection strings; the renderer raises on them.
"""

from __future__ import annotations

import re
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import NoReturn

import pycountry
from pydantic import ValidationError
from sqlalchemy import select

from app.db import SessionLocal
from app.models import FillingRule, PbeFieldSchema
from app.schemas.shipment import (
    CATEGORY_SLUGS,
    DESTINATION_UNSTATED,
    QUANTITY_UNSTATED,
    WEIGHT_UNSTATED,
    Shipment,
)
from app.services.cache import cache
from app.services.db_tools import search_categories
from app.services.docs.document import DocumentData

_ISO2_RE = re.compile(r"^[A-Z]{2}$")

# Business-rule bounds (from the todo-10 spec).
_QUANTITY_MIN, _QUANTITY_MAX = 1, 10_000
_WEIGHT_MIN_G, _WEIGHT_MAX_G = 1, 50_000


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


def missing_required(data: DocumentData, form_type: str | None = None) -> list[str]:
    """Required PBE fields of ``form_type`` with no resolvable value.

    Queries ``pbe_field_schemas`` (required=true, ordered by id) and returns
    the field keys whose rendered value is the "—" placeholder (via
    ``DocumentData.resolve_value`` — the single formatting point).  Covers
    ALL required fields, including ``assessable_value`` (F3 fix: the old
    Shipment-projection could never see it).

    The result drives the "ask the user" flow: for each key in the returned
    list, the caller prompts the user for that field.
    """
    form_type = form_type or data.form_type
    with SessionLocal() as session:
        required_keys = session.scalars(
            select(PbeFieldSchema.field_key)
            .where(
                PbeFieldSchema.form_type == form_type,
                PbeFieldSchema.required.is_(True),
            )
            .order_by(PbeFieldSchema.id)
        ).all()
    return [key for key in required_keys if data.resolve_value(key) == "—"]


# --- todo 14: the OFFICIAL PBE/CN22 filling rules (pbe-iii-iv-fields.md §7) ---
#
# Wave 2: the rule CATALOG is DB-driven — the enabled rows of the
# ``filling_rules`` table (rule_key / severity / applies_to / params /
# message) are loaded per call; each row's evaluator below is looked up by
# rule_key and returns True when the rule is VIOLATED.  The MSG_* constants
# mirror the seeded messages (tests reference them; the DB row is the source
# of truth at runtime).

MSG_SUB_PIECE_VALUE = "Value of Sub pieces does not match"
MSG_SUB_PIECE_WEIGHT = "Weight of Sub pieces does not match"
MSG_GROSS_110_NET = "gross weight exceeds 110% of net weight"
MSG_FOB_INVOICE = "FOB value exceeds invoice value"
MSG_DESC_HS = "Description does not match with HS Code/CTH"
MSG_ITCH_RESTRICTED = "ITCH code not applicable for restricted policy"
MSG_DGFT_IEC_MISSING = "DGFT registration data missing"
MSG_KYC_IEC_OR_GSTIN = "booking requires at least one of IEC or GSTIN"

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


def _itch_restricted_with(hs: dict, restricted_hs6: list[str]) -> bool:
    """True iff the HS row's 6-digit code is in the restricted-policy set."""
    for code in (hs.get("hs6"), hs.get("itc_hs_8")):
        if code:
            six = re.sub(r"\D", "", str(code))[:6]
            if six in restricted_hs6:
                return True
    return False


# --- rule evaluators ---------------------------------------------------------
# Each evaluator returns True when its rule is VIOLATED.  ``params`` is the
# rule's ``filling_rules.params`` JSONB ({} when the row has none).  The
# evaluator registry maps rule_key -> evaluator; a DB row whose rule_key is
# not registered is reported as a warning and skipped (never crashes).


def _eval_kyc_iec_or_gstin(data: DocumentData, params: dict) -> bool:
    return data.iec is None and data.gstin is None


def _eval_dgft_iec_missing(data: DocumentData, params: dict) -> bool:
    return data.iec is None and data.gstin is not None


def _eval_gross_net_110(data: DocumentData, params: dict) -> bool:
    return data.weight_grams > data.net_weight_g * float(
        params.get("max_ratio", 1.10)
    )


def _eval_fob_le_invoice(data: DocumentData, params: dict) -> bool:
    return (
        data.fob_minor is not None
        and data.value_minor is not None
        and data.fob_minor > data.value_minor
    )


def _eval_sub_piece_value_sum(data: DocumentData, params: dict) -> bool:
    return (
        data.quantity > 1
        and data.unit_value_minor is not None
        and data.quantity * data.unit_value_minor > (data.value_minor or 0)
    )


def _eval_sub_piece_weight_sum(data: DocumentData, params: dict) -> bool:
    return (
        data.quantity > 1
        and data.piece_gross_g is not None
        and data.quantity * data.piece_gross_g > data.weight_grams
    )


def _eval_desc_hs_match(data: DocumentData, params: dict) -> bool:
    hs = _primary_hs_row(data)
    return hs is not None and not _description_consistent(data, hs)


def _eval_itch_restricted_policy(data: DocumentData, params: dict) -> bool:
    hs = _primary_hs_row(data)
    return hs is not None and _itch_restricted_with(
        hs, params.get("restricted_hs6", ["5303", "4403"])
    )


_EVALUATORS: dict[str, Callable[[DocumentData, dict], bool]] = {
    "kyc_iec_or_gstin": _eval_kyc_iec_or_gstin,
    "dgft_iec_missing": _eval_dgft_iec_missing,
    "gross_net_110": _eval_gross_net_110,
    "fob_le_invoice": _eval_fob_le_invoice,
    "sub_piece_value_sum": _eval_sub_piece_value_sum,
    "sub_piece_weight_sum": _eval_sub_piece_weight_sum,
    "desc_hs_match": _eval_desc_hs_match,
    "itch_restricted_policy": _eval_itch_restricted_policy,
}


def validate_document_rules(document_data: DocumentData) -> DocumentRuleResult:
    """Enforce the official PBE/CN22 filling rules (pbe-iii-iv-fields.md §7).

    DB-driven (wave 2): the ENABLED ``filling_rules`` rows are loaded per
    call; each contributes its evaluator (by rule_key), its params, its
    severity and its VERBATIM message — disabling a row disables the check
    and editing a row's message changes the rejection string.  ``errors``
    reject the document; ``warnings`` (restricted-policy ITCH) do not block.
    Deterministic-only — pure arithmetic / set logic / db_tools lookups; the
    LLM never validates.
    """
    data = DocumentData.model_validate(document_data)
    errors: list[str] = []
    warnings: list[str] = []
    # Lazy import — avoids circular import with country_rules module.
    from app.services.country_rules import _EVALUATORS as _COUNTRY_EVALUATORS
    evaluators = {**_COUNTRY_EVALUATORS, **_EVALUATORS}  # country rules first
    cache_key = "filling_rules:all"
    cached = cache.get(cache_key)
    if cached is not None:
        rules = cached
    else:
        with SessionLocal() as session:
            db_rules = session.scalars(
                select(FillingRule)
                .where(FillingRule.enabled.is_(True))
                .order_by(FillingRule.id)
            ).all()
        rules = [
            {
                "rule_key": r.rule_key,
                "applies_to": r.applies_to,
                "params": r.params,
                "severity": r.severity,
                "message": r.message,
            }
            for r in db_rules
        ]
        cache.set(cache_key, rules)
    for rule in rules:
        if rule["applies_to"] and data.form_type not in (rule["applies_to"] or {}).get(
            "form_types", []
        ):
            continue
        evaluator = evaluators.get(rule["rule_key"])
        if evaluator is None:
            print(
                f"warning: unknown filling rule {rule['rule_key']!r} in DB",
                file=sys.stderr,
            )
            continue
        if evaluator(data, rule["params"] or {}):
            (warnings if rule["severity"] == "warning" else errors).append(rule["message"])
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
