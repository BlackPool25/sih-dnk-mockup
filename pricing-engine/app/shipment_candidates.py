from dataclasses import dataclass
from itertools import product

from app.optimization_models import (
    LaneOption,
    OptimizationItem,
)
from app.packaging import Package
from app.shipping import calculate_ems, calculate_itps


class CandidateGenerationError(Exception):
    """Raised when shipment candidates cannot be generated."""


@dataclass(frozen=True)
class ShipmentCandidate:
    """One feasible parcel configuration."""

    lane: str
    package_id: str

    item_quantities: dict[str, int]

    product_weight_g: int
    packaging_weight_g: int
    actual_weight_g: int

    volumetric_weight_g: int | None
    chargeable_weight_g: int

    shipping_cost_minor: int
    packaging_cost_minor: int
    total_cost_minor: int

    transit_min_days: int | None
    transit_max_days: int | None


def calculate_candidate(
    lane: LaneOption,
    package: Package,
    item_quantities: dict[str, int],
    items: list[OptimizationItem],
) -> ShipmentCandidate | None:
    """
    Calculate the exact cost and feasibility of one parcel.

    Product weight is calculated first.

    Packaging tare weight is then added.

    The resulting actual parcel weight is passed to
    ITPS/EMS feasibility and pricing.
    """

    product_weight_g = 0

    item_lookup = {
        item.item_id: item
        for item in items
    }

    for item_id, quantity in item_quantities.items():

        if item_id not in item_lookup:
            raise CandidateGenerationError(
                f"Unknown item ID: {item_id}"
            )

        if quantity < 0:
            raise CandidateGenerationError(
                f"Negative quantity for {item_id}"
            )

        item = item_lookup[item_id]

        if quantity > item.quantity:
            raise CandidateGenerationError(
                f"Quantity for {item_id} exceeds "
                f"available quantity"
            )

        # A non-splittable item must either be entirely
        # inside this parcel or completely absent.
        if (
            not item.splittable
            and quantity not in (0, item.quantity)
        ):
            raise CandidateGenerationError(
                f"Non-splittable item {item_id!r} "
                f"cannot be partially assigned"
            )

        product_weight_g += (
            quantity * item.unit_weight_g
        )

    if product_weight_g <= 0:
        return None

    if (
        package.max_product_weight_g is not None
        and product_weight_g
        > package.max_product_weight_g
    ):
        return None

    actual_weight_g = (
        product_weight_g
        + package.tare_weight_g
    )

    if lane.name == "ITPS":

        shipping = calculate_itps(
            lane=lane.lane_data,
            actual_weight_g=actual_weight_g,
        )

    elif lane.name == "EMS":

        shipping = calculate_ems(
            lane=lane.lane_data,
            actual_weight_g=actual_weight_g,
            length_cm=package.length_cm,
            width_cm=package.width_cm,
            height_cm=package.height_cm,
        )

    else:
        raise CandidateGenerationError(
            f"Unsupported lane: {lane.name}"
        )

    if not shipping["feasible"]:
        return None

    shipping_cost_minor = (
        shipping["shipping_cost_minor"]
    )

    if shipping_cost_minor is None:
        return None

    packaging_cost_minor = package.cost_minor

    return ShipmentCandidate(
        lane=lane.name,
        package_id=package.package_id,
        item_quantities=dict(item_quantities),
        product_weight_g=product_weight_g,
        packaging_weight_g=package.tare_weight_g,
        actual_weight_g=actual_weight_g,
        volumetric_weight_g=shipping.get(
            "volumetric_weight_g"
        ),
        chargeable_weight_g=shipping[
            "chargeable_weight_g"
        ],
        shipping_cost_minor=shipping_cost_minor,
        packaging_cost_minor=packaging_cost_minor,
        total_cost_minor=(
            shipping_cost_minor
            + packaging_cost_minor
        ),
        transit_min_days=shipping.get(
            "transit_min_days"
        ),
        transit_max_days=shipping.get(
            "transit_max_days"
        ),
    )


def generate_item_quantity_options(
    items: list[OptimizationItem],
) -> list[dict[str, int]]:
    """
    Generate valid item allocations for ONE parcel.

    Splittable item:
        quantity can range from 0 to the full quantity.

    Non-splittable item:
        quantity can only be:
            0
            OR
            full quantity

    Example:

        Item A:
            quantity = 3
            splittable = True

        Item B:
            quantity = 2
            splittable = False

    Possible values:

        A → 0, 1, 2, 3
        B → 0, 2
    """

    if not items:
        raise CandidateGenerationError(
            "At least one item is required"
        )

    quantity_ranges = []

    for item in items:

        if item.quantity <= 0:
            raise CandidateGenerationError(
                f"Invalid quantity for {item.item_id}"
            )

        if item.splittable:
            quantity_ranges.append(
                range(item.quantity + 1)
            )
        else:
            quantity_ranges.append(
                (0, item.quantity)
            )

    options: list[dict[str, int]] = []

    for quantities in product(
        *quantity_ranges
    ):

        option = {
            item.item_id: quantity
            for item, quantity in zip(
                items,
                quantities,
            )
        }

        # Empty parcel is not a candidate.
        if not any(
            quantity > 0
            for quantity in quantities
        ):
            continue

        options.append(option)

    return options


def generate_shipment_candidates(
    items: list[OptimizationItem],
    packages: list[Package],
    lanes: list[LaneOption],
) -> list[ShipmentCandidate]:
    """
    Generate all feasible single-parcel candidates.

    Each candidate contains:

        item allocation
        package
        shipping lane
        exact shipping cost
        packaging cost
        actual parcel weight
        chargeable weight
    """

    if not items:
        raise CandidateGenerationError(
            "At least one item is required"
        )

    if not packages:
        raise CandidateGenerationError(
            "At least one package is required"
        )

    if not lanes:
        raise CandidateGenerationError(
            "At least one shipping lane is required"
        )

    quantity_options = (
        generate_item_quantity_options(items)
    )

    candidates: list[ShipmentCandidate] = []

    for item_quantities in quantity_options:

        for package in packages:

            for lane in lanes:

                candidate = calculate_candidate(
                    lane=lane,
                    package=package,
                    item_quantities=item_quantities,
                    items=items,
                )

                if candidate is not None:
                    candidates.append(candidate)

    return candidates