from typing import Any

from ortools.sat.python import cp_model

from app.optimization_models import LaneOption, OptimizationItem
from app.optimization_objectives import OptimizationMode, calculate_solution_summary
from app.packaging import Package
from app.shipment_candidates import ShipmentCandidate, generate_shipment_candidates


class OptimizationError(Exception):
    """Raised when shipment optimization cannot be completed."""


def _candidate_covers_item(candidate: ShipmentCandidate, item_id: str) -> int:
    return candidate.item_quantities.get(item_id, 0)


def _transit_days(candidate: ShipmentCandidate) -> int:
    if candidate.transit_max_days is not None:
        return candidate.transit_max_days
    if candidate.transit_min_days is not None:
        return candidate.transit_min_days
    raise OptimizationError(f"Transit time is unavailable for lane {candidate.lane!r}")


def _validate_landed_cost(landed_cost: dict[str, Any]) -> None:
    required = {
        "destination_country", "currency", "product_value_minor",
        "insurance_minor", "other_additions_minor", "standard_duty_rate_percent",
        "tax_rate_percent", "include_duty_in_tax_base", "additional_tax_base_minor",
        "preferential_eligible", "platform_fee_rate_percent", "platform_fixed_fee_minor",
    }
    missing = sorted(required - landed_cost.keys())
    if missing:
        raise OptimizationError("Missing landed-cost fields: " + ", ".join(missing))


def optimize_shipment(
    items: list[OptimizationItem],
    packages: list[Package],
    lanes: list[LaneOption],
    optimization_mode: OptimizationMode = OptimizationMode.CHEAPEST,
    max_parcels: int | None = None,
    landed_cost: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Find the feasible shipment plan with the lowest applicable objective.

    The decision-dependent monetary component is the complete parcel cost:
    carrier shipping + packaging. The canonical landed-cost calculator is then
    run on the selected shipping total, so the returned landed cost is always
    consistent with the same pricing rules used elsewhere in the engine.
    """
    if not items:
        raise OptimizationError("At least one optimization item is required")
    if not packages:
        raise OptimizationError("At least one package is required")
    if not lanes:
        raise OptimizationError("At least one shipping lane is required")
    if landed_cost is None:
        raise OptimizationError("Landed-cost data is required for pricing optimization")

    _validate_landed_cost(landed_cost)

    if isinstance(optimization_mode, str):
        try:
            optimization_mode = OptimizationMode(optimization_mode.upper())
        except ValueError as exc:
            raise OptimizationError(f"Unsupported optimization mode: {optimization_mode!r}") from exc

    if max_parcels is None:
        max_parcels = min(sum(item.quantity for item in items), 10)
    if max_parcels <= 0:
        raise OptimizationError("max_parcels must be greater than zero")

    candidates = generate_shipment_candidates(items=items, packages=packages, lanes=lanes)
    if not candidates:
        raise OptimizationError("No feasible shipment candidates were found")

    model = cp_model.CpModel()
    candidate_used = [
        model.NewIntVar(0, max_parcels, f"candidate_{index}_count")
        for index in range(len(candidates))
    ]

    for item in items:
        terms = []
        for index, candidate in enumerate(candidates):
            quantity = _candidate_covers_item(candidate, item.item_id)
            if quantity > 0:
                terms.append(quantity * candidate_used[index])
        if not terms:
            raise OptimizationError(f"No candidate can carry item {item.item_id!r}")
        model.Add(sum(terms) == item.quantity)

    model.Add(sum(candidate_used) <= max_parcels)
    model.Add(sum(candidate_used) >= 1)

    monetary_objective = sum(
        candidate.total_cost_minor * candidate_used[index]
        for index, candidate in enumerate(candidates)
    )

    if optimization_mode == OptimizationMode.CHEAPEST:
        model.Minimize(monetary_objective)

    elif optimization_mode == OptimizationMode.FASTEST:
        max_transit = max(_transit_days(candidate) for candidate in candidates)
        cost_bound = max(
            1,
            max(candidate.total_cost_minor for candidate in candidates) * max_parcels,
        )
        transit_var = model.NewIntVar(0, max_transit, "max_transit_days")
        present_vars = []
        for index, candidate in enumerate(candidates):
            present = model.NewBoolVar(f"candidate_{index}_present")
            present_vars.append(present)
            model.Add(candidate_used[index] <= max_parcels * present)
            model.Add(candidate_used[index] >= present)
            model.Add(transit_var >= _transit_days(candidate)).OnlyEnforceIf(present)
        model.Add(sum(present_vars) >= 1)
        model.Minimize(transit_var * (cost_bound + 1) + monetary_objective)

    elif optimization_mode == OptimizationMode.BALANCED:
        max_transit = max(_transit_days(candidate) for candidate in candidates)
        transit_var = model.NewIntVar(0, max_transit, "max_transit_days")
        present_vars = []
        for index, candidate in enumerate(candidates):
            present = model.NewBoolVar(f"candidate_{index}_present")
            present_vars.append(present)
            model.Add(candidate_used[index] <= max_parcels * present)
            model.Add(candidate_used[index] >= present)
            model.Add(transit_var >= _transit_days(candidate)).OnlyEnforceIf(present)
        model.Add(sum(present_vars) >= 1)
        model.Minimize(monetary_objective * 70 + transit_var * 30)

    else:
        raise OptimizationError(f"Unsupported optimization mode: {optimization_mode!r}")

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 30.0
    solver.parameters.num_search_workers = 8
    status = solver.Solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise OptimizationError("No feasible shipment configuration was found")

    selected_counts = [solver.Value(variable) for variable in candidate_used]
    selected_parcels: list[dict[str, Any]] = []

    for index, candidate in enumerate(candidates):
        for _ in range(selected_counts[index]):
            selected_parcels.append({
                "parcel_id": f"parcel-{len(selected_parcels) + 1}",
                "lane": candidate.lane,
                "package_id": candidate.package_id,
                "item_quantities": dict(candidate.item_quantities),
                "product_weight_g": candidate.product_weight_g,
                "packaging_weight_g": candidate.packaging_weight_g,
                "actual_weight_g": candidate.actual_weight_g,
                "volumetric_weight_g": candidate.volumetric_weight_g,
                "chargeable_weight_g": candidate.chargeable_weight_g,
                "shipping_cost_minor": candidate.shipping_cost_minor,
                "packaging_cost_minor": candidate.packaging_cost_minor,
                "total_cost_minor": candidate.total_cost_minor,
                "transit_min_days": candidate.transit_min_days,
                "transit_max_days": candidate.transit_max_days,
                "objective_value": candidate.total_cost_minor,
            })

    summary = calculate_solution_summary(
        candidates=candidates,
        selected_counts=selected_counts,
        mode=optimization_mode,
    )

    from app.landed_cost import calculate_landed_cost

    landed_result = calculate_landed_cost(
        product_value_minor=int(landed_cost["product_value_minor"]),
        shipping_cost_minor=summary["shipping_cost_minor"],
        insurance_minor=int(landed_cost["insurance_minor"]),
        standard_duty_rate_percent=landed_cost["standard_duty_rate_percent"],
        tax_rate_percent=landed_cost["tax_rate_percent"],
        destination_country=str(landed_cost["destination_country"]),
        currency=str(landed_cost["currency"]),
        preferential_eligible=bool(landed_cost["preferential_eligible"]),
        preferential_rate_percent=landed_cost.get("preferential_rate_percent"),
        preferential_agreement=landed_cost.get("preferential_agreement"),
        preferential_reason=landed_cost.get("preferential_reason"),
        include_duty_in_tax_base=bool(landed_cost["include_duty_in_tax_base"]),
        additional_tax_base_minor=int(landed_cost["additional_tax_base_minor"]),
        fee_components=landed_cost.get("country_fee_components", []),
        other_additions_minor=int(landed_cost["other_additions_minor"]),
        platform_fee_rate_percent=landed_cost["platform_fee_rate_percent"],
        platform_fixed_fee_minor=int(landed_cost["platform_fixed_fee_minor"]),
    )

    return {
        "status": "OPTIMAL" if status == cp_model.OPTIMAL else "FEASIBLE",
        "optimization_mode": optimization_mode.value,
        "parcel_count": len(selected_parcels),
        "total_cost_minor": summary["total_cost_minor"],
        "shipping_cost_minor": summary["shipping_cost_minor"],
        "packaging_cost_minor": summary["packaging_cost_minor"],
        "estimated_transit_min_days": summary["estimated_transit_min_days"],
        "estimated_transit_max_days": summary["estimated_transit_max_days"],
        "currency": landed_result["currency"],
        "parcels": selected_parcels,
        "landed_cost": landed_result,
    }
