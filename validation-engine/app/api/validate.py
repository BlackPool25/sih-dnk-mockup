"""POST /validate — partial-order merge + graded validation.

Accepts a partial ``OrderPayload``, merges it into a persisted Order row
(with ``SELECT ... FOR UPDATE``), runs ``graded_evaluate()``, and returns
a ``ValidationReport``.  Business errors are in the report, not HTTP errors.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter
from pydantic import BaseModel, ValidationError
from sqlalchemy import select

from app.db import SessionLocal
from app.models.line_item import LineItem
from app.models.order import Order, OrderStatus
from app.schemas.order import OrderPayload
from app.schemas.shipment import CONSIGNEE_UNSTATED, ShipmentDraft
from app.services.binding import validate_e_fira_reconciliation
from app.services.db_tools import get_state_sales_tax, search_categories
from app.services.docs.document import build_document_data
from app.services.docs.onboarding import generate_onboarding_kit
from app.services.extract import CategoryUnknownError
from app.services.graded import ErrorEntry, ValidationReport, graded_evaluate
from app.services.report import _resolve_missing_template
from app.services.sanity import TurnError, sanity_violations
from app.services.validate import (
    _all_draft_fields_stated,
    missing_required,
    validate_document_rules,
    validate_shipment,
)
from app.models.order import ValidationState

router = APIRouter(prefix="/validate", tags=["validation"])

# Fields that CANNOT change once the order is confirmed (binding freeze).
_BINDING_FIELDS: frozenset[str] = frozenset(
    {"iec", "ad_code", "bank_account", "bank_name", "ifsc", "seller_id", "buyer_id"}
)

# Payload fields sent as strings but stored as UUID columns.
_UUID_FIELDS: frozenset[str] = frozenset({"seller_id", "buyer_id"})

# Order fields writable per payload — maps payload field name to Order attribute.
# line_items is handled separately (full-replace semantics).
_ORDER_FIELDS: frozenset[str] = frozenset(
    {
        "destination_country",
        "value_minor",
        "currency",
        "consignee",
        "net_weight_g",
        "gross_weight_g",
        "article_id",
        "iec",
        "gstin",
        "ad_code",
        "bank_account",
        "bank_name",
        "ifsc",
        "quote_id",
        "exporter_name",
        "exporter_address",
        "state_code",
        "seller_id",
        "buyer_id",
    }
)

# Statuses at/above which binding fields are frozen.
_FROZEN_STATUSES: frozenset[OrderStatus] = frozenset(
    {
        OrderStatus.confirmed,
        OrderStatus.paid_held,
        OrderStatus.in_transit,
        OrderStatus.delivered,
        OrderStatus.disputed,
        OrderStatus.settled,
        OrderStatus.refunded,
    }
)


def _merge_order(payload: OrderPayload, session) -> tuple[Order, list[ErrorEntry]]:
    """Merge partial payload into an Order row; return (order, blocking_entries).

    Strategy:
    - payload.order_id is None → create new Order.
    - payload.order_id is set → SELECT FOR UPDATE on existing Order.
    - Per-field merge: payload field wins when not None; absent payload fields
      retain the existing DB value.
    - Binding freeze: when Order.status is frozen, binding fields in the
      payload are DISCARDED (existing value retained) and a blocking report
      entry is emitted.
    - Version is bumped.
    - Line items: None → retain; [] → clear; non-empty → replace full set.
    """
    blocking: list[ErrorEntry] = []

    if payload.order_id is None:
        order = Order(id=uuid.uuid4())
        session.add(order)
    else:
        order = session.execute(
            select(Order).where(Order.id == uuid.UUID(payload.order_id)).with_for_update()
        ).scalar_one_or_none()
        if order is None:
            raise ValueError(f"order not found: {payload.order_id}")

    frozen = order.status in _FROZEN_STATUSES

    # Merge scalar fields.
    for field in _ORDER_FIELDS:
        value = getattr(payload, field, None)
        if value is None:
            continue  # absent — retain existing
        if frozen and field in _BINDING_FIELDS:
            blocking.append(
                ErrorEntry(
                    field=field,
                    severity="block",
                    message=(
                        f"binding field {field!r} cannot be changed "
                        f"after order is {order.status.value!r}"
                    ),
                    action="blocking",
                )
            )
            continue
        if field in _UUID_FIELDS:
            try:
                value = uuid.UUID(value)
            except ValueError:
                blocking.append(
                    ErrorEntry(
                        field=field,
                        severity="error",
                        message="invalid UUID",
                        action="blocking",
                    )
                )
                continue
        setattr(order, field, value)

    # Merge line items (full-replace semantics when non-None).
    if payload.line_items is not None:
        # Delete existing line items.
        for existing in list(order.line_items):
            session.delete(existing)
        order.line_items.clear()
        # Insert new ones.
        for li_data in payload.line_items:
            li = LineItem(
                order_id=order.id,
                category_slug=li_data.category_slug,
                quantity=li_data.quantity,
                weight_g=li_data.weight_g,
                hs_code=li_data.hs_code,
                value_minor=li_data.value_minor,
                dimensions=li_data.dimensions,
            )
            order.line_items.append(li)
            session.add(li)

    order.version = (order.version or 0) + 1
    return order, blocking


@router.post("", response_model=ValidationReport)
def post_validate(
    payload: OrderPayload,
    include_onboarding_kit: bool = False,
    include_e_fira: bool = False,
) -> ValidationReport:
    """Merge partial order payload and run graded validation.

    Returns a ValidationReport with status 200 — business errors are
    embedded in the report, never surfaced as HTTP errors.

    Query params:
        include_onboarding_kit: when true, attaches an onboarding_kit
            section to the report.
        include_e_fira: when true, runs e-FIRA reconciliation against
            the order and merges any errors into the report.
    """
    with SessionLocal.begin() as session:
        try:
            order, blocking = _merge_order(payload, session)
        except ValueError as exc:
            # Order not found, invalid UUID, etc. — still 200.
            return ValidationReport(
                status="invalid",
                validation_state="invalid",
                order_state="quote_accepted",
                errors=[
                    ErrorEntry(
                        field="order_id", severity="error", message=str(exc), action="check_input"
                    )
                ],
                missing=[],
                warnings=[],
                doc_ready=False,
                order_id=payload.order_id or "",
                prompt_template="",
                action_template="",
            )

        # Run graded validation on the merged order.
        report = graded_evaluate(order)

        # Inject binding-freeze blocking entries.
        for entry in blocking:
            report.errors.insert(0, entry)
            # Recompute status after injecting blocking errors
            has_errors = any(e.severity in ("error", "block") for e in report.errors)
            has_incomplete = any(e.severity == "incomplete" for e in report.errors)
            if has_incomplete:
                report.status = "incomplete"
                report.validation_state = ValidationState.incomplete.value
                report.doc_ready = False
            elif has_errors:
                report.status = "invalid"
                report.validation_state = ValidationState.invalid.value
                report.doc_ready = False

        # ── e-FIRA reconciliation (query-param gated) ────────────────
        if include_e_fira:
            e_fira_errors = validate_e_fira_reconciliation(order)
            for entry in e_fira_errors:
                report.errors.append(entry)

        # ── onboarding kit (query-param gated) ───────────────────────
        if include_onboarding_kit:
            report.onboarding_kit = generate_onboarding_kit(
                pan=None,  # derived from IEC in real impl
                has_bank_account=bool(order.bank_account),
                bank_name=order.bank_name,
                bank_account=order.bank_account,
                ifsc=order.ifsc,
                iec=order.iec,
            )

        pricing_error: str | None = None
        if report.validation_state == "ready" and report.status == "ready" and order.line_items:
            if order.pricing_breakdown is not None and order.parcels is not None:
                pass
            else:
                try:
                    from app.services.pricing_client import query_optimal_assignment_sync

                    pricing_resp = query_optimal_assignment_sync(order, order.line_items)
                    order.pricing_breakdown = pricing_resp
                    order.parcels = pricing_resp.get("parcels", [])
                except Exception as exc:  # noqa: BLE001 — pricing must not block validation
                    pricing_error = str(exc)
        if report.validation_state == "ready" and report.status == "ready" and order.parcels:
            try:
                from app.services.tracking_client import register_shipments_for_order

                register_shipments_for_order(order, order.parcels or [])
            except Exception:
                pass
        # Persist last_report snapshot (+ pricing_error side-channel).
        report_dict = report.model_dump()
        if pricing_error is not None:
            report_dict["pricing_error"] = pricing_error
        # Persist validation_state on order for list/get
        try:
            order.validation_state = ValidationState(report.validation_state)  # type: ignore[assignment]
        except Exception:
            pass
        order.last_report = report_dict

    return report


# ---------------------------------------------------------------------------
# POST /api/validate/shipment — per-turn draft validation (Wave 1).
# Business errors live in the report, never as HTTP errors (no 500s).
# ---------------------------------------------------------------------------


class MissingField(BaseModel):
    """One required PBE field with no resolvable value + bilingual prompts."""

    field_key: str
    label: str
    prompt_template_hi: str
    prompt_template_en: str


class DocumentRules(BaseModel):
    """Outcome of the official filling-rule checks (errors block)."""

    errors: list[str]
    warnings: list[str]


class DbInfo(BaseModel):
    """The researched cost/tax surface for the turn — everything traceable."""

    category: dict | None = None
    hs_codes: list[dict] = []
    cth: str | None = None
    product_description: str | None = None
    duties: list[dict] = []
    lane: dict | None = None
    lane_error: str | None = None
    state_sales_tax: dict | None = None
    landed_cost_minor: int | None = None


class ValidationTurnReport(BaseModel):
    """The per-turn validation report — draft + errors + research surface."""

    draft: ShipmentDraft
    business_errors: list[TurnError] = []
    missing_required: list[MissingField] = []
    document_rules: DocumentRules = DocumentRules(errors=[], warnings=[])
    document_ready: bool = False
    db_info: DbInfo = DbInfo()


class ValidateShipmentRequest(BaseModel):
    """One validated turn: the accumulated draft + seller identifiers."""

    draft: ShipmentDraft
    form_type: str = "PBE_IV"
    iec: str | None = None
    gstin: str | None = None
    state_iso2: str | None = None


shipment_router = APIRouter(prefix="/api/validate", tags=["validation"])


@shipment_router.post("/shipment", response_model=ValidationTurnReport)
def validate_shipment_turn(payload: ValidateShipmentRequest) -> ValidationTurnReport:
    """Validate one accumulated draft and assemble the DB research surface."""
    draft = payload.draft
    try:
        shipment = draft.to_shipment()
    except CategoryUnknownError:
        return ValidationTurnReport(
            draft=draft,
            business_errors=[
                TurnError(field="product_category", message="category not disambiguated")
            ],
        )

    business_errors: list[TurnError] = []
    try:
        validate_shipment(shipment)
    except ValidationError as exc:
        business_errors = [
            TurnError(
                field=str(error["loc"][0]) if error["loc"] else "shipment",
                message=str(error["msg"]),
            )
            for error in exc.errors()
        ]

    # Post-hoc sanity gate (Wave 1 T1): a value can be business-valid yet
    # implausible (quantity=2000 for small-woodware) — re-ask via
    # pick_next_field (business-error-wins) instead of booking it.
    seen_fields = {error.field for error in business_errors}
    for error in sanity_violations(draft, draft.product_category):
        if error.field not in seen_fields:
            business_errors.append(error)
            seen_fields.add(error.field)

    try:
        data = build_document_data(
            shipment,
            payload.form_type,
            consignee=draft.consignee if draft.consignee != CONSIGNEE_UNSTATED else None,
            value_minor=draft.value_minor if draft.value_minor > 0 else None,
            iec=payload.iec,
            gstin=payload.gstin,
            state_code=payload.state_iso2,
        )
    except (LookupError, ValueError) as exc:
        # Unknown lane pair / over-cap weight — partial report, never 500.
        return ValidationTurnReport(
            draft=draft,
            business_errors=business_errors,
            db_info=DbInfo(lane_error=str(exc)),
        )
    except Exception as exc:
        return ValidationTurnReport(
            draft=draft,
            business_errors=business_errors + [TurnError(field="document", message=str(exc))],
        )

    missing: list[MissingField] = []
    try:
        for key in missing_required(data, payload.form_type):
            label = (data.field_schema.get(key) or {}).get("label") or key
            missing.append(
                MissingField(
                    field_key=key,
                    label=label,
                    prompt_template_hi=_resolve_missing_template(key, "hi").format(
                        field_key=key, label=label, example=""
                    ),
                    prompt_template_en=_resolve_missing_template(key, "en").format(
                        field_key=key, label=label, example=""
                    ),
                )
            )
    except Exception:
        missing = []

    rules = DocumentRules(errors=[], warnings=[])
    try:
        result = validate_document_rules(data)
        rules = DocumentRules(errors=result.errors, warnings=result.warnings)
    except Exception:
        pass

    state_tax: dict | None = None
    if payload.state_iso2 and shipment.destination_country == "US":
        try:
            state_tax = get_state_sales_tax(payload.state_iso2)
        except KeyError:
            state_tax = None

    hs_codes = data.hs_codes
    try:
        category = next(
            (
                c
                for c in search_categories(draft.product_category)
                if c["slug"] == draft.product_category
            ),
            None,
        )
    except Exception:
        category = None

    db_info = DbInfo(
        category=category,
        hs_codes=hs_codes,
        cth=hs_codes[0]["hs6"][:4] if hs_codes else None,
        product_description=data.category_name,
        duties=data.duties,
        lane=data.lane,
        state_sales_tax=state_tax,
        landed_cost_minor=data.landed_cost_minor,
    )
    return ValidationTurnReport(
        draft=draft,
        business_errors=business_errors,
        missing_required=missing,
        document_rules=rules,
        document_ready=(
            not business_errors
            and not rules.errors
            and not missing
            and _all_draft_fields_stated(draft)
        ),
        db_info=db_info,
    )


__all__ = ["router", "shipment_router"]
