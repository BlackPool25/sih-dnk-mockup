from typing import Any

from app.optimization_models import LaneOption, OptimizationItem
from app.optimization_objectives import OptimizationMode
from app.optimizer import OptimizationError, optimize_shipment
from app.packaging import Package


class OptimizationServiceError(Exception):
    """Raised when shipment optimization cannot be completed."""


def _validate_items(items: list[OptimizationItem]) -> None:
    if not items:
        raise OptimizationServiceError("At least one item is required")

    seen_ids: set[str] = set()
    for item in items:
        if item.item_id in seen_ids:
            raise OptimizationServiceError(f"Duplicate item ID: {item.item_id}")
        seen_ids.add(item.item_id)

        if item.quantity <= 0:
            raise OptimizationServiceError(
                f"Quantity must be greater than zero for item {item.item_id}"
            )
        if item.unit_weight_g <= 0:
            raise OptimizationServiceError(
                f"Unit weight must be greater than zero for item {item.item_id}"
            )
        if item.length_cm <= 0 or item.width_cm <= 0 or item.height_cm <= 0:
            raise OptimizationServiceError(
                f"Dimensions must be greater than zero for item {item.item_id}"
            )


def _validate_packages(packages: list[Package]) -> None:
    if not packages:
        raise OptimizationServiceError("At least one package option is required")

    seen_ids: set[str] = set()
    for package in packages:
        if package.package_id in seen_ids:
            raise OptimizationServiceError(
                f"Duplicate package ID: {package.package_id}"
            )
        seen_ids.add(package.package_id)

        if package.tare_weight_g < 0 or package.cost_minor < 0:
            raise OptimizationServiceError(
                f"Invalid packaging data for {package.package_id}"
            )
        if (
            package.length_cm <= 0
            or package.width_cm <= 0
            or package.height_cm <= 0
        ):
            raise OptimizationServiceError(
                f"Package dimensions must be greater than zero for {package.package_id}"
            )


def _validate_lanes(lanes: list[LaneOption]) -> None:
    if not lanes:
        raise OptimizationServiceError("At least one shipping lane is required")

    supported_lanes = {"ITPS", "EMS"}
    seen_lanes: set[str] = set()

    for lane in lanes:
        lane_name = lane.name.upper()
        if lane_name in seen_lanes:
            raise OptimizationServiceError(f"Duplicate shipping lane: {lane_name}")
        seen_lanes.add(lane_name)

        if lane_name not in supported_lanes:
            raise OptimizationServiceError(f"Unsupported shipping lane: {lane.name}")
        if not isinstance(lane.lane_data, dict):
            raise OptimizationServiceError(f"Invalid lane data for {lane.name}")


def optimize_order(
    items: list[OptimizationItem],
    packages: list[Package],
    lanes: list[LaneOption],
    optimization_mode: OptimizationMode | str = OptimizationMode.CHEAPEST,
    max_parcels: int | None = None,
    landed_cost: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate inputs and optimize shipment against available landed-cost data."""
    _validate_items(items)
    _validate_packages(packages)
    _validate_lanes(lanes)

    if isinstance(optimization_mode, str):
        try:
            optimization_mode = OptimizationMode(optimization_mode.upper())
        except ValueError as exc:
            raise OptimizationServiceError(
                f"Unsupported optimization mode: {optimization_mode!r}"
            ) from exc

    if max_parcels is not None and max_parcels <= 0:
        raise OptimizationServiceError("max_parcels must be greater than zero")

    if landed_cost is None:
        raise OptimizationServiceError(
            "Landed-cost data is required for pricing optimization"
        )

    try:
        result = optimize_shipment(
            items=items,
            packages=packages,
            lanes=lanes,
            optimization_mode=optimization_mode,
            max_parcels=max_parcels,
            landed_cost=landed_cost,
        )
    except OptimizationError as exc:
        raise OptimizationServiceError(str(exc)) from exc

    return _build_service_response(
        result=result,
        optimization_mode=optimization_mode,
    )


def _build_service_response(
    result: dict[str, Any],
    optimization_mode: OptimizationMode,
) -> dict[str, Any]:
    parcels = result.get("parcels", [])

    shipment_weight_g = sum(parcel["product_weight_g"] for parcel in parcels)
    packaging_weight_g = sum(parcel["packaging_weight_g"] for parcel in parcels)
    actual_weight_g = sum(parcel["actual_weight_g"] for parcel in parcels)

    shipping_cost_minor = sum(parcel["shipping_cost_minor"] for parcel in parcels)
    packaging_cost_minor = sum(parcel["packaging_cost_minor"] for parcel in parcels)
    total_cost_minor = sum(parcel["total_cost_minor"] for parcel in parcels)

    lane_breakdown: dict[str, int] = {}
    for parcel in parcels:
        lane = parcel["lane"]
        lane_breakdown[lane] = lane_breakdown.get(lane, 0) + 1

    return {
        "status": result["status"],
        "optimization_mode": optimization_mode.value,
        "shipment": {
            "parcel_count": len(parcels),
            "product_weight_g": shipment_weight_g,
            "packaging_weight_g": packaging_weight_g,
            "actual_weight_g": actual_weight_g,
        },
        "cost": {
            "shipping_cost_minor": shipping_cost_minor,
            "packaging_cost_minor": packaging_cost_minor,
            "total_cost_minor": total_cost_minor,
            "currency": result.get("currency", "INR"),
        },
        "lane_breakdown": lane_breakdown,
        "estimated_transit": {
            "min_days": result.get("estimated_transit_min_days"),
            "max_days": result.get("estimated_transit_max_days"),
        },
        "parcels": parcels,
        "landed_cost": result["landed_cost"],
    }
