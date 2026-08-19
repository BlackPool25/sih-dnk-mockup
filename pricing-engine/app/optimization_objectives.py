from enum import Enum
from typing import Any

from app.shipment_candidates import ShipmentCandidate


class OptimizationMode(str, Enum):
    """Supported shipment optimization objectives."""

    CHEAPEST = "CHEAPEST"
    FASTEST = "FASTEST"
    BALANCED = "BALANCED"


class OptimizationObjectiveError(Exception):
    """Raised when an optimization objective is invalid."""


def _candidate_transit_days(
    candidate: ShipmentCandidate,
) -> int:
    """
    Return the conservative transit time for a candidate.

    We use the maximum transit estimate because the optimizer
    should not assume the fastest end of the carrier's range.
    """

    if candidate.transit_max_days is not None:
        return candidate.transit_max_days

    if candidate.transit_min_days is not None:
        return candidate.transit_min_days

    raise OptimizationObjectiveError(
        f"Transit time is unavailable for lane "
        f"{candidate.lane!r}"
    )


def calculate_candidate_objective(
    candidate: ShipmentCandidate,
    mode: OptimizationMode,
) -> int:
    """
    Convert one shipment candidate into an integer objective value.

    Lower is always better.

    CHEAPEST:
        Minimize total monetary cost.

    FASTEST:
        Minimize transit time first, while using cost as a
        deterministic tie-breaker.

    BALANCED:
        Combine normalized cost and transit time.
    """

    if mode == OptimizationMode.CHEAPEST:
        return candidate.total_cost_minor

    transit_days = _candidate_transit_days(
        candidate
    )

    if mode == OptimizationMode.FASTEST:
        # Cost is included as a tie-breaker.
        #
        # The multiplier makes one additional transit day
        # more important than normal cost differences.
        return (
            transit_days * 1_000_000
            + candidate.total_cost_minor
        )

    if mode == OptimizationMode.BALANCED:
        # Balanced mode gives both cost and delivery time
        # meaningful influence.
        #
        # This is deliberately deterministic and integer-based
        # so it can be used directly by CP-SAT.
        return (
            candidate.total_cost_minor * 100
            + transit_days * 1_000
        )

    raise OptimizationObjectiveError(
        f"Unsupported optimization mode: {mode!r}"
    )


def calculate_solution_summary(
    candidates: list[ShipmentCandidate],
    selected_counts: list[int],
    mode: OptimizationMode,
) -> dict[str, Any]:
    """
    Produce an explanation-friendly summary of the selected
    shipment configuration.
    """

    if len(candidates) != len(selected_counts):
        raise OptimizationObjectiveError(
            "Candidate/count lengths do not match"
        )

    selected: list[ShipmentCandidate] = []

    for candidate, count in zip(
        candidates,
        selected_counts,
    ):
        if count < 0:
            raise OptimizationObjectiveError(
                "Candidate count cannot be negative"
            )

        selected.extend(
            [candidate] * count
        )

    if not selected:
        raise OptimizationObjectiveError(
            "No shipment candidates were selected"
        )

    total_cost_minor = sum(
        candidate.total_cost_minor
        for candidate in selected
    )

    total_shipping_cost_minor = sum(
        candidate.shipping_cost_minor
        for candidate in selected
    )

    total_packaging_cost_minor = sum(
        candidate.packaging_cost_minor
        for candidate in selected
    )

    transit_days = [
        _candidate_transit_days(candidate)
        for candidate in selected
    ]

    return {
        "mode": mode.value,
        "parcel_count": len(selected),
        "total_cost_minor": total_cost_minor,
        "shipping_cost_minor": (
            total_shipping_cost_minor
        ),
        "packaging_cost_minor": (
            total_packaging_cost_minor
        ),
        "estimated_transit_max_days": max(
            transit_days
        ),
        "estimated_transit_min_days": min(
            transit_days
        ),
    }