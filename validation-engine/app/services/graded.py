"""Graded evaluation — only fires validation passes whose inputs are present.

Every pass is wrapped in try/except; exceptions become structured report
entries, never 500s.  The function receives a fully-loaded Order object and
returns a ValidationReport.
"""

from __future__ import annotations

import re
from typing import Literal

import pycountry
from pydantic import BaseModel

from app.models.order import Order, OrderStatus, ValidationState
from app.schemas.shipment import (
    DESTINATION_UNSTATED,
    QUANTITY_UNSTATED,
    WEIGHT_UNSTATED,
    Shipment,
)

ErrorSeverity = Literal["error", "warning", "incomplete", "block"]
ErrorAction = Literal["blocking", "fix_value", "fix_format", "check_input", "provide_field", "provide_line_items", "provide_missing_fields", "freeze_payout"]


class ErrorEntry(BaseModel):
    """Single validation error with bilingual prompt templates.

    prompt_template_hi/en are populated at report-build time from DB flags
    (prompt.error.{field}.hi/en).  They are empty until build_report()
    fills them.
    """

    field: str
    severity: ErrorSeverity
    message: str
    action: ErrorAction
    prompt_template_hi: str = ""
    prompt_template_en: str = ""


class MissingEntry(BaseModel):
    """A required PBE field that is still missing.

    label and example are drawn from the PBE field schema; when the schema
    row is unavailable they remain empty.  prompt_template_hi/en are
    populated at report-build time from DB flags.
    """

    field_key: str
    label: str = ""
    example: str = ""
    prompt_template_hi: str = ""
    prompt_template_en: str = ""


class ValidationReport(BaseModel):
    """Structured validation outcome — returned as JSON by POST /validate.

    Refined in task 6; ErrorEntry and MissingEntry carry bilingual prompt
    templates populated at report-build time from DB flags.
    """

    status: str  # "incomplete" | "invalid" | "ready"
    validation_state: str  # matches ValidationState enum
    order_state: str  # matches OrderStatus enum
    errors: list[ErrorEntry] = []
    missing: list[MissingEntry] = []
    warnings: list[str] = []
    doc_ready: bool = False
    order_id: str = ""
    prompt_template: str = ""
    action_template: str = ""
    onboarding_kit: dict | None = None


# ── format validators ──────────────────────────────────────────────────
_ISO2_RE = re.compile(r"^[A-Z]{2}$")
_IEC_RE = re.compile(r"^[A-Za-z0-9]{10}$")
_AD_CODE_RE = re.compile(r"^\d{14}$")
_IFSC_RE = re.compile(r"^[A-Za-z]{4}0[A-Za-z0-9]{6}$")


def _iso2_valid(country: str | None) -> bool:
    """True iff country is a real ISO 3166-1 alpha-2 code."""
    if country is None:
        return False
    return (
        _ISO2_RE.match(country) is not None
        and pycountry.countries.get(alpha_2=country) is not None
    )


def _iec_valid(iec: str | None) -> bool:
    """True iff iec is 10-char alphanumeric."""
    if iec is None:
        return True  # absent is not a violation
    return bool(_IEC_RE.match(iec))


def _ad_code_valid(ad_code: str | None) -> bool:
    """True iff ad_code is 14 digits."""
    if ad_code is None:
        return True
    return bool(_AD_CODE_RE.match(ad_code))


def _ifsc_valid(ifsc: str | None) -> bool:
    """True iff ifsc matches 4alpha+0+6alphanumeric."""
    if ifsc is None:
        return True
    return bool(_IFSC_RE.match(ifsc))


# ── pass 1: validate_line_items (stub — task 7 implements fully) ─────


def _pass_line_items(order: Order) -> list[ErrorEntry]:
    """Validate every line item (delegated to validate_line_items module)."""
    entries: list[ErrorEntry] = []
    try:
        from app.services.validate_line_items import validate_line_items

        entries = validate_line_items(order)
    except Exception as exc:  # noqa: BLE001
        entries.append(
            ErrorEntry(
                field="line_items",
                severity="error",
                message=f"line item validation error: {exc}",
                action="check_input",
            )
        )
    return entries


# ── pass 2: validate_document_rules (gated) ──────────────────────────


def _pass_document_rules(order: Order) -> list[ErrorEntry]:
    """Run validate_document_rules when DocumentData can be built.

    Gate: category_slug (from first line item) + destination_country +
    weight_grams + form_type all present.  Exceptions from
    build_document_data become report entries.
    """
    entries: list[ErrorEntry] = []
    try:
        # Gate checks — every input must be present.
        first_li = order.line_items[0] if order.line_items else None
        category_slug = first_li.category_slug if first_li else None
        destination_country = order.destination_country
        weight_grams = order.gross_weight_g or order.net_weight_g

        # Hard-coded form type — the DNK engine targets PBE_IV (Postal Bill of Export).
        form_type = "PBE_IV"

        missing_gate: list[str] = []
        if not category_slug:
            missing_gate.append("category_slug (first line item)")
        if not destination_country:
            missing_gate.append("destination_country")
        if not weight_grams:
            missing_gate.append("weight_grams")
        if missing_gate:
            entries.append(
                ErrorEntry(
                    field="document_rules",
                    severity="incomplete",
                    message=f"skipped — missing gate inputs: {', '.join(missing_gate)}",
                    action="provide_missing_fields",
                )
            )
            return entries

        # Build DocumentData via build_document_data with try/except.
        # Build requires a Shipment object.
        quantity = first_li.quantity if first_li and first_li.quantity else QUANTITY_UNSTATED
        shipment = Shipment(
            product_category=category_slug,
            quantity=quantity,
            weight_grams=weight_grams or WEIGHT_UNSTATED,
            destination_country=destination_country or DESTINATION_UNSTATED,
            confidence="high",
        )

        try:
            from app.services.docs.document import build_document_data

            data = build_document_data(
                shipment,
                form_type,
                consignee=order.consignee,
                value_minor=order.value_minor,
                iec=order.iec,
                gstin=order.gstin,
                net_weight_g=order.net_weight_g,
                exporter_name=order.exporter_name,
                exporter_address=order.exporter_address,
                state_code=order.state_code,
            )
        except LookupError as exc:
            entries.append(
                ErrorEntry(
                    field="document_rules",
                    severity="error",
                    message=f"data lookup failure: {exc}",
                    action="check_input",
                )
            )
            return entries
        except ValueError as exc:
            entries.append(
                ErrorEntry(
                    field="document_rules",
                    severity="error",
                    message=f"data validation failure: {exc}",
                    action="check_input",
                )
            )
            return entries
        except Exception as exc:  # noqa: BLE001
            entries.append(
                ErrorEntry(
                    field="document_rules",
                    severity="error",
                    message=f"unexpected error building document data: {exc}",
                    action="check_input",
                )
            )
            return entries

        # Run validate_document_rules.
        try:
            from app.services.validate import (
                validate_document_rules,  # lazy — circular import
            )

            result = validate_document_rules(data)
            for msg in result.errors:
                entries.append(
                    ErrorEntry(
                        field="document_rules",
                        severity="error",
                        message=msg,
                        action="fix_value",
                    )
                )
            for msg in result.warnings:
                entries.append(
                    ErrorEntry(
                        field="document_rules",
                        severity="warning",
                        message=msg,
                        action="check_input",
                    )
                )
        except Exception as exc:  # noqa: BLE001
            entries.append(
                ErrorEntry(
                    field="document_rules",
                    severity="error",
                    message=f"document rule evaluation error: {exc}",
                    action="check_input",
                )
            )

    except Exception as exc:  # noqa: BLE001
        entries.append(
            ErrorEntry(
                field="document_rules",
                severity="error",
                message=f"document rules pass failed: {exc}",
                action="check_input",
            )
        )
    return entries


# ── pass 3: missing_required ─────────────────────────────────────────


def _pass_missing_required(order: Order) -> list[ErrorEntry]:
    """Run missing_required when form_type + DocumentData exist.

    Gate: same inputs as pass 2.
    """
    entries: list[ErrorEntry] = []
    try:
        first_li = order.line_items[0] if order.line_items else None
        category_slug = first_li.category_slug if first_li else None
        destination_country = order.destination_country
        weight_grams = order.gross_weight_g or order.net_weight_g
        form_type = "PBE_IV"

        if not (category_slug and destination_country and weight_grams):
            return entries  # silently skip — pass 2 already reported the gate

        quantity = first_li.quantity if first_li and first_li.quantity else QUANTITY_UNSTATED
        shipment = Shipment(
            product_category=category_slug,
            quantity=quantity,
            weight_grams=weight_grams or WEIGHT_UNSTATED,
            destination_country=destination_country or DESTINATION_UNSTATED,
            confidence="high",
        )

        try:
            from app.services.docs.document import build_document_data

            data = build_document_data(
                shipment,
                form_type,
                consignee=order.consignee,
                value_minor=order.value_minor,
                iec=order.iec,
                gstin=order.gstin,
                net_weight_g=order.net_weight_g,
                exporter_name=order.exporter_name,
                exporter_address=order.exporter_address,
                state_code=order.state_code,
            )
        except Exception:  # noqa: BLE001
            return entries  # pass 2 already reported the failure

        try:
            from app.services.validate import missing_required  # lazy — circular import

            missing = missing_required(data, form_type)
            for key in missing:
                entries.append(
                    ErrorEntry(
                        field=key,
                        severity="incomplete",
                        message=f"required field {key!r} is missing",
                        action="provide_field",
                    )
                )
        except Exception as exc:  # noqa: BLE001
            entries.append(
                ErrorEntry(
                    field="missing_required",
                    severity="error",
                    message=f"missing-required check failed: {exc}",
                    action="check_input",
                )
            )

    except Exception as exc:  # noqa: BLE001
        entries.append(
            ErrorEntry(
                field="missing_required",
                severity="error",
                message=f"missing-required pass failed: {exc}",
                action="check_input",
            )
        )
    return entries


# ── pass 4: basic field validation ───────────────────────────────────


def _pass_basic_fields(order: Order) -> list[ErrorEntry]:
    """Validate ISO2, IEC, AD_CODE, IFSC formats.

    Runs when destination_country is present.
    """
    entries: list[ErrorEntry] = []
    try:
        country = order.destination_country
        if country is not None:
            if not _ISO2_RE.match(country):
                entries.append(
                    ErrorEntry(
                        field="destination_country",
                        severity="error",
                        message=f"invalid ISO2 format: {country!r}",
                        action="fix_format",
                    )
                )
            elif not _iso2_valid(country):
                entries.append(
                    ErrorEntry(
                        field="destination_country",
                        severity="warning",
                        message=f"unknown country code: {country!r}",
                        action="check_input",
                    )
                )

        if order.iec is not None and not _iec_valid(order.iec):
            entries.append(
                ErrorEntry(
                    field="iec",
                    severity="error",
                    message=f"invalid IEC format: {order.iec!r} (expect 10-char alphanumeric)",
                    action="fix_format",
                )
            )

        if order.ad_code is not None and not _ad_code_valid(order.ad_code):
            entries.append(
                ErrorEntry(
                    field="ad_code",
                    severity="error",
                    message=f"invalid AD code format: {order.ad_code!r} (expect 14 digits)",
                    action="fix_format",
                )
            )

        if order.ifsc is not None and not _ifsc_valid(order.ifsc):
            entries.append(
                ErrorEntry(
                    field="ifsc",
                    severity="error",
                    message=f"invalid IFSC format: {order.ifsc!r} (expect 4alpha+0+6alphanumeric)",
                    action="fix_format",
                )
            )

        # ── exporter identity validation ──────────────────────────
        if order.iec is not None and not order.exporter_name:
            entries.append(
                ErrorEntry(
                    field="exporter_name",
                    severity="error",
                    message="exporter_name is required when IEC is provided",
                    action="provide_field",
                )
            )
        if order.exporter_name is not None and not order.exporter_address:
            entries.append(
                ErrorEntry(
                    field="exporter_address",
                    severity="incomplete",
                    message="exporter_address is required when exporter_name is provided",
                    action="provide_field",
                )
            )
        if order.state_code is not None and len(order.state_code) != 2:
            entries.append(
                ErrorEntry(
                    field="state_code",
                    severity="error",
                    message=f"state_code must be exactly 2 characters, got {order.state_code!r}",
                    action="fix_format",
                )
            )

    except Exception as exc:  # noqa: BLE001
        entries.append(
            ErrorEntry(
                field="basic_fields",
                severity="error",
                message=f"basic field validation failed: {exc}",
                action="check_input",
            )
        )
    return entries


# ── pass 5: exporter binding ─────────────────────────────────────────


def _pass_exporter_binding(order: Order) -> list[ErrorEntry]:
    """Validate exporter binding when IEC or AD-code fields are present.

    Delegates to ``validate_exporter_binding(order)`` which checks IEC/AD-code/IFSC
    formats, bank-account/bank-name consistency, DGFT bank lookup, lock-on-order,
    and version checks.
    """
    entries: list[ErrorEntry] = []
    try:
        if order.iec is None and order.ad_code is None:
            return entries  # nothing to bind — skip silently

        from app.services.binding import (
            validate_exporter_binding,  # lazy — circular import
        )

        entries = validate_exporter_binding(order)
    except Exception as exc:  # noqa: BLE001
        entries.append(
            ErrorEntry(
                field="exporter_binding",
                severity="error",
                message=f"exporter binding validation failed: {exc}",
                action="check_input",
            )
        )
    return entries


# ── pass 6: e-FIRA (stub) ────────────────────────────────────────────


def _pass_e_fira(order: Order) -> list[ErrorEntry]:
    """Stub — actual e-FIRA reconciliation runs via query params in endpoint.

    The POST /validate endpoint accepts ``include_e_fira=true`` and calls
    ``validate_e_fira_reconciliation(order)`` directly, merging results
    into the report.  This pass exists so the graded pipeline has a
    consistent slot for e-FIRA when it moves into the automatic flow.
    """
    return []  # endpoint wires real validate_e_fira_reconciliation


# ── synthesis ────────────────────────────────────────────────────────


def _synthesize_report(
    order: Order,
    doc_errors: list[ErrorEntry],
    missing_keys: list[ErrorEntry],
    field_errors: list[ErrorEntry],
    li_errors: list[ErrorEntry],
    binding_errors: list[ErrorEntry] | None = None,
) -> ValidationReport:
    """Combine all pass outputs into a single ValidationReport."""
    all_errors = li_errors + doc_errors + missing_keys + field_errors
    if binding_errors:
        all_errors += binding_errors

    # Extract missing field entries and warnings.
    missing: list[MissingEntry] = []
    warnings: list[str] = []
    errors: list[ErrorEntry] = []

    for entry in all_errors:
        sev = entry.severity
        if sev == "incomplete":
            missing.append(MissingEntry(field_key=entry.field))
            errors.append(entry)
        elif sev == "warning":
            warnings.append(entry.message)
        else:
            errors.append(entry)

    # Determine overall status.
    has_errors = any(e.severity in ("error", "block") for e in errors)
    has_incomplete = any(e.severity == "incomplete" for e in errors)

    if has_incomplete:
        status = "incomplete"
        validation_state = ValidationState.incomplete.value
    elif has_errors:
        status = "invalid"
        validation_state = ValidationState.invalid.value
    else:
        status = "ready"
        validation_state = ValidationState.ready.value

    # doc_ready: true when no errors and no missing entries.
    doc_ready = not errors and not missing

    return ValidationReport(
        status=status,
        validation_state=validation_state,
        order_state=order.status.value if order.status else OrderStatus.quote_accepted.value,
        errors=errors,
        missing=missing,
        warnings=warnings,
        doc_ready=doc_ready,
        order_id=str(order.id),
        prompt_template="",
        action_template="",
    )


# ── public ───────────────────────────────────────────────────────────


def graded_evaluate(order: Order) -> ValidationReport:
    """Graded validation — only fires passes whose inputs are present.

    Passes run in order:
    1. validate_line_items
    2. validate_document_rules (gated)
    3. missing_required (gated)
    4. basic field validation
    5. exporter binding (gated on iec/ad_code)

    Every pass is individually try/except-wrapped — exceptions become
    structured report entries, never 500s.
    """
    li_errors = _pass_line_items(order)
    doc_errors = _pass_document_rules(order)
    missing_keys = _pass_missing_required(order)
    field_errors = _pass_basic_fields(order)
    binding_errors = _pass_exporter_binding(order)

    return _synthesize_report(
        order, doc_errors, missing_keys, field_errors, li_errors, binding_errors
    )


__all__ = [
    "ErrorEntry",
    "MissingEntry",
    "ValidationReport",
    "graded_evaluate",
]
