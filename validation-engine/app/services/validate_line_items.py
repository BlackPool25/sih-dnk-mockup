"""Deterministic line-item validation for a multi-product Order.

validate_line_items(order) → list[ErrorEntry]

Pure logic — no LLM calls, no imports from extract.  Returns a flat list of
structured ErrorEntry objects; the caller (graded.py) merges them into the
ValidationReport.

Coverage:
  • 0 items      → incomplete (provide_line_items)
  • 1 item       → single-product fast path (basic fields only)
  • N items      → per-item checks + cross-item aggregation (value, weight,
                    lane-cap, prohibited-flags)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.services.graded import ErrorEntry

if TYPE_CHECKING:
    from app.models.order import Order

# ── unstated sentinel value (pinned contract from Shipment schema) ─────
_UNSTATED = -1


def validate_line_items(order: Order) -> list[ErrorEntry]:
    """Validate every line item on an Order against business rules.

    Returns a flat list of ErrorEntry for the graded pipeline to merge.
    """
    entries: list[ErrorEntry] = []
    try:
        line_items = order.line_items

        # ── 0 items ─────────────────────────────────────────────────
        if not line_items:
            entries.append(
                ErrorEntry(
                    field="line_items",
                    severity="incomplete",
                    message="no line items provided",
                    action="provide_line_items",
                )
            )
            return entries

        # ── 1 item — short-circuit single-product path ──────────────
        if len(line_items) == 1:
            li = line_items[0]
            if not li.category_slug:
                entries.append(
                    ErrorEntry(
                        field="line_items[0].category_slug",
                        severity="incomplete",
                        message="line item 0 missing category_slug",
                        action="provide_line_items",
                    )
                )
            if li.quantity is not None and li.quantity != _UNSTATED and li.quantity <= 0:
                entries.append(
                    ErrorEntry(
                        field="line_items[0].quantity",
                        severity="error",
                        message="line item 0 quantity must be > 0",
                        action="fix_value",
                    )
                )
            if li.weight_g is not None and li.weight_g != _UNSTATED and li.weight_g <= 0:
                entries.append(
                    ErrorEntry(
                        field="line_items[0].weight_g",
                        severity="error",
                        message="line item 0 weight must be > 0",
                        action="fix_value",
                    )
                )
            return entries

        # ── N items — per-item + cross-item aggregation ─────────────
        sum_values = 0
        sum_weights = 0
        has_hard_prohibited = False

        for i, li in enumerate(line_items):
            # Per-item: category_slug
            if not li.category_slug:
                entries.append(
                    ErrorEntry(
                        field=f"line_items[{i}].category_slug",
                        severity="incomplete",
                        message=f"line item {i} missing category_slug",
                        action="provide_line_items",
                    )
                )

            # Per-item: quantity
            if li.quantity is not None and li.quantity != _UNSTATED and li.quantity <= 0:
                entries.append(
                    ErrorEntry(
                        field=f"line_items[{i}].quantity",
                        severity="error",
                        message=f"line item {i} quantity must be > 0",
                        action="fix_value",
                    )
                )

            # Per-item: weight
            if li.weight_g is not None and li.weight_g != _UNSTATED and li.weight_g <= 0:
                entries.append(
                    ErrorEntry(
                        field=f"line_items[{i}].weight_g",
                        severity="error",
                        message=f"line item {i} weight must be > 0",
                        action="fix_value",
                    )
                )

            # Aggregation — values
            if li.value_minor is not None:
                sum_values += li.value_minor

            # Aggregation — weights (skip unstated)
            if li.weight_g is not None and li.weight_g != _UNSTATED:
                sum_weights += li.weight_g

            # Conflicting restrictions (prohibited_flags)
            if li.prohibited_flags:
                flags: dict = li.prohibited_flags
                # Hard-prohibited: any truthy flag blocks the line (and whole order)
                if any(v for v in flags.values()):
                    has_hard_prohibited = True
                    entries.append(
                        ErrorEntry(
                            field=f"line_items[{i}].prohibited_flags",
                            severity="block",
                            message=f"line item {i} is hard-prohibited",
                            action="blocking",
                        )
                    )

        # ── Cross-item: Σ line values ≤ order value ─────────────────
        if (
            order.value_minor is not None
            and order.value_minor > 0
            and sum_values > order.value_minor
        ):
            entries.append(
                ErrorEntry(
                    field="line_items.value_minor",
                    severity="error",
                    message=(
                        f"sum of line item values ({sum_values}) "
                        f"exceeds order value ({order.value_minor})"
                    ),
                    action="fix_value",
                )
            )

        # ── Cross-item: Σ line weights ≤ parcel gross weight ────────
        if (
            order.gross_weight_g is not None
            and order.gross_weight_g > 0
            and sum_weights > order.gross_weight_g
        ):
            entries.append(
                ErrorEntry(
                    field="line_items.weight_g",
                    severity="error",
                    message=(
                        f"sum of line item weights ({sum_weights}g) "
                        f"exceeds parcel gross weight ({order.gross_weight_g}g)"
                    ),
                    action="fix_value",
                )
            )

        # ── Lane-cap per destination (via DB, never hardcoded) ──────
        if order.destination_country:
            try:
                from app.services.db_tools import quote_lane

                # Fetch lane info with a minimal weight to get the cap value.
                lane_info = quote_lane(order.destination_country, 1, lane="ITPS")
                cap: int | None = lane_info.get("weight_cap_g")
                if cap is not None:
                    for i, li in enumerate(line_items):
                        li_weight = li.weight_g
                        if li_weight is not None and li_weight != _UNSTATED and li_weight > cap:
                            entries.append(
                                ErrorEntry(
                                    field=f"line_items[{i}].weight_g",
                                    severity="block",
                                    message=(
                                        f"line item {i} weight ({li_weight}g) "
                                        f"exceeds lane cap ({cap}g) for "
                                        f"{order.destination_country}"
                                    ),
                                    action="blocking",
                                )
                            )
            except LookupError:
                pass  # unknown country/lane — skip cap check
            except ValueError:
                pass  # lane cap anomaly — skip cap check

        # ── Hard-prohibited gates whole order ────────────────────────
        if has_hard_prohibited:
            entries.append(
                ErrorEntry(
                    field="line_items",
                    severity="block",
                    message="order contains hard-prohibited items — entire consignment blocked",
                    action="blocking",
                )
            )

    except Exception:  # noqa: BLE001
        entries.append(
            ErrorEntry(
                field="line_items",
                severity="error",
                message="line item validation error",
                action="check_input",
            )
        )
    return entries
