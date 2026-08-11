"""POST /validate — partial-order merge + graded validation.

Accepts a partial ``OrderPayload``, merges it into a persisted Order row
(with ``SELECT ... FOR UPDATE``), runs ``graded_evaluate()``, and returns
a ``ValidationReport``.  Business errors are in the report, not HTTP errors.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter
from sqlalchemy import select

from app.db import SessionLocal
from app.models.line_item import LineItem
from app.models.order import Order, OrderStatus
from app.schemas.order import OrderPayload
from app.services.binding import validate_e_fira_reconciliation
from app.services.docs.onboarding import generate_onboarding_kit
from app.services.graded import ErrorEntry, ValidationReport, graded_evaluate

router = APIRouter(prefix="/validate", tags=["validation"])

# Fields that CANNOT change once the order is confirmed (binding freeze).
_BINDING_FIELDS: frozenset[str] = frozenset(
    {"iec", "ad_code", "bank_account", "bank_name", "ifsc"}
)

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
            select(Order)
            .where(Order.id == uuid.UUID(payload.order_id))
            .with_for_update()
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


@router.post("/", response_model=ValidationReport)
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
                errors=[ErrorEntry(field="order_id", severity="error", message=str(exc), action="check_input")],
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

        # Persist last_report snapshot.
        order.last_report = report.model_dump()

    return report


__all__ = ["router"]
