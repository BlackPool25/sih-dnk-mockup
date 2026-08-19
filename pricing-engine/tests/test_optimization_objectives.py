from app.optimization_objectives import (
    OptimizationMode,
    calculate_candidate_objective,
    calculate_solution_summary,
)
from app.shipment_candidates import ShipmentCandidate


def candidate(
    cost: int,
    transit_min: int,
    transit_max: int,
    shipping: int | None = None,
    packaging: int | None = None,
) -> ShipmentCandidate:
    if shipping is None:
        shipping = cost

    if packaging is None:
        packaging = 0

    return ShipmentCandidate(
        lane="ITPS",
        package_id="BOX-1",
        item_quantities={"item-1": 1},
        product_weight_g=1000,
        packaging_weight_g=100,
        actual_weight_g=1100,
        volumetric_weight_g=None,
        chargeable_weight_g=1100,
        shipping_cost_minor=shipping,
        packaging_cost_minor=packaging,
        total_cost_minor=cost,
        transit_min_days=transit_min,
        transit_max_days=transit_max,
    )


def test_cheapest_uses_total_cost():
    shipment = candidate(
        cost=500,
        transit_min=18,
        transit_max=28,
    )

    result = calculate_candidate_objective(
        shipment,
        OptimizationMode.CHEAPEST,
    )

    assert result == 500


def test_fastest_prioritizes_transit_time():
    fast = candidate(
        cost=1000,
        transit_min=7,
        transit_max=14,
    )

    slow = candidate(
        cost=500,
        transit_min=18,
        transit_max=28,
    )

    fast_score = calculate_candidate_objective(
        fast,
        OptimizationMode.FASTEST,
    )

    slow_score = calculate_candidate_objective(
        slow,
        OptimizationMode.FASTEST,
    )

    assert fast_score < slow_score


def test_cheapest_prefers_lower_cost():
    cheap = candidate(
        cost=500,
        transit_min=18,
        transit_max=28,
    )

    expensive = candidate(
        cost=1000,
        transit_min=7,
        transit_max=14,
    )

    cheap_score = calculate_candidate_objective(
        cheap,
        OptimizationMode.CHEAPEST,
    )

    expensive_score = calculate_candidate_objective(
        expensive,
        OptimizationMode.CHEAPEST,
    )

    assert cheap_score < expensive_score


def test_balanced_returns_integer_score():
    shipment = candidate(
        cost=500,
        transit_min=18,
        transit_max=28,
    )

    result = calculate_candidate_objective(
        shipment,
        OptimizationMode.BALANCED,
    )

    assert isinstance(result, int)
    assert result > 0


def test_solution_summary():
    first = candidate(
        cost=500,
        transit_min=18,
        transit_max=28,
        shipping=450,
        packaging=50,
    )

    second = candidate(
        cost=700,
        transit_min=7,
        transit_max=14,
        shipping=650,
        packaging=50,
    )

    result = calculate_solution_summary(
        candidates=[first, second],
        selected_counts=[1, 1],
        mode=OptimizationMode.CHEAPEST,
    )

    assert result["mode"] == "CHEAPEST"
    assert result["parcel_count"] == 2
    assert result["total_cost_minor"] == 1200
    assert result["shipping_cost_minor"] == 1100
    assert result["packaging_cost_minor"] == 100
    assert result["estimated_transit_max_days"] == 28
    assert result["estimated_transit_min_days"] == 14


def test_solution_summary_rejects_mismatched_lengths():
    first = candidate(
        cost=500,
        transit_min=18,
        transit_max=28,
    )

    try:
        calculate_solution_summary(
            candidates=[first],
            selected_counts=[],
            mode=OptimizationMode.CHEAPEST,
        )
        assert False
    except Exception:
        assert True