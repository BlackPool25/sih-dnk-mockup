from decimal import Decimal

from app.optimization_models import (
    LaneOption,
    OptimizationItem,
)
from app.packaging import Package
from app.shipment_candidates import (
    CandidateGenerationError,
    calculate_candidate,
    generate_item_quantity_options,
    generate_shipment_candidates,
)


def make_item(
    item_id: str,
    quantity: int,
    weight_g: int,
    splittable: bool = True,
) -> OptimizationItem:
    """Create a test optimization item."""

    return OptimizationItem(
        item_id=item_id,
        quantity=quantity,
        unit_weight_g=weight_g,
        splittable=splittable,
        length_cm=Decimal("10"),
        width_cm=Decimal("10"),
        height_cm=Decimal("10"),
    )


def make_package(
    tare_weight_g: int = 100,
    max_product_weight_g: int | None = 5000,
) -> Package:
    """Create a standard test package."""

    return Package(
        package_id="BOX-1",
        name="Standard box",
        tare_weight_g=tare_weight_g,
        length_cm=Decimal("20"),
        width_cm=Decimal("20"),
        height_cm=Decimal("20"),
        cost_minor=50,
        max_product_weight_g=max_product_weight_g,
    )


def make_itps_lane(
    weight_cap_g: int = 5000,
) -> LaneOption:
    """Create a test ITPS lane."""

    return LaneOption(
        name="ITPS",
        lane_data={
            "lane": "ITPS",
            "first_slab_g": 50,
            "first_slab_rate_minor": 100,
            "addl_slab_g": 50,
            "addl_slab_rate_minor": 20,
            "weight_cap_g": weight_cap_g,
            "volume_free": True,
            "divisor": None,
            "transit_min_days": 18,
            "transit_max_days": 28,
            "provenance": {},
        },
    )


def make_ems_lane(
    weight_cap_g: int = 20000,
) -> LaneOption:
    """Create a test EMS lane."""

    return LaneOption(
        name="EMS",
        lane_data={
            "lane": "EMS",
            "first_slab_g": 120,
            "first_slab_rate_minor": 120,
            "addl_slab_g": 50,
            "addl_slab_rate_minor": 30,
            "weight_cap_g": weight_cap_g,
            "volume_free": False,
            "divisor": 5000,
            "transit_min_days": 7,
            "transit_max_days": 14,
            "provenance": {},
        },
    )


# ============================================================
# Quantity option tests
# ============================================================


def test_splittable_item_generates_partial_quantities():
    """
    A splittable item with quantity 3 can contribute
    1, 2, or 3 units to a parcel.
    """

    items = [
        make_item(
            item_id="A",
            quantity=3,
            weight_g=500,
            splittable=True,
        )
    ]

    options = generate_item_quantity_options(items)

    quantities = {
        option["A"]
        for option in options
    }

    assert quantities == {1, 2, 3}


def test_non_splittable_item_cannot_be_partially_allocated():
    """
    A non-splittable item with quantity 3 can only be:

        0 units in a parcel
        OR
        all 3 units in the parcel.

    Empty parcels are removed by the generator, so the
    returned candidate quantity is only 3.
    """

    items = [
        make_item(
            item_id="A",
            quantity=3,
            weight_g=500,
            splittable=False,
        )
    ]

    options = generate_item_quantity_options(items)

    quantities = {
        option["A"]
        for option in options
    }

    assert quantities == {3}


def test_mixed_splittable_and_non_splittable_items():
    """
    Example:

        A = 2 units, splittable
        B = 1 unit, non-splittable

    Valid non-empty parcel combinations include:

        A=1, B=0
        A=2, B=0
        A=0, B=1
        A=1, B=1
        A=2, B=1

    But never a partial quantity for B.
    """

    items = [
        make_item(
            item_id="A",
            quantity=2,
            weight_g=500,
            splittable=True,
        ),
        make_item(
            item_id="B",
            quantity=1,
            weight_g=700,
            splittable=False,
        ),
    ]

    options = generate_item_quantity_options(items)

    expected = {
        ("A", "B")
    }

    actual = {
        tuple(
            option[item_id]
            for item_id in ("A", "B")
        )
        for option in options
    }

    assert actual == {
        (1, 0),
        (2, 0),
        (0, 1),
        (1, 1),
        (2, 1),
    }


# ============================================================
# Candidate calculation tests
# ============================================================


def test_candidate_includes_packaging_weight():
    """
    Product:

        4900g

    Packaging:

        100g

    Actual parcel:

        5000g
    """

    items = [
        make_item(
            item_id="A",
            quantity=1,
            weight_g=4900,
        )
    ]

    candidate = calculate_candidate(
        lane=make_itps_lane(),
        package=make_package(),
        item_quantities={"A": 1},
        items=items,
    )

    assert candidate is not None

    assert candidate.product_weight_g == 4900
    assert candidate.packaging_weight_g == 100
    assert candidate.actual_weight_g == 5000


def test_candidate_rejected_when_packaging_pushes_over_itps_cap():
    """
    Product:

        4950g

    Packaging:

        100g

    Actual:

        5050g

    ITPS cap:

        5000g

    Therefore the candidate is infeasible.
    """

    items = [
        make_item(
            item_id="A",
            quantity=1,
            weight_g=4950,
        )
    ]

    candidate = calculate_candidate(
        lane=make_itps_lane(weight_cap_g=5000),
        package=make_package(),
        item_quantities={"A": 1},
        items=items,
    )

    assert candidate is None


def test_candidate_calculates_itps_cost():
    """
    Product:

        500g

    Packaging:

        100g

    Actual parcel:

        600g

    ITPS:

        first 50g = 100
        remaining 550g
        11 additional 50g slabs
        11 × 20 = 220

    Shipping:

        100 + 220 = 320

    Packaging:

        50

    Total:

        370
    """

    items = [
        make_item(
            item_id="A",
            quantity=1,
            weight_g=500,
        )
    ]

    candidate = calculate_candidate(
        lane=make_itps_lane(),
        package=make_package(),
        item_quantities={"A": 1},
        items=items,
    )

    assert candidate is not None

    assert candidate.product_weight_g == 500
    assert candidate.packaging_weight_g == 100
    assert candidate.actual_weight_g == 600

    assert candidate.shipping_cost_minor == 320
    assert candidate.packaging_cost_minor == 50
    assert candidate.total_cost_minor == 370


def test_candidate_calculates_ems_volumetric_weight():
    """
    Product:

        1000g

    Packaging:

        100g

    Actual:

        1100g

    Package volume:

        20 × 20 × 20
        = 8000 cm³

    EMS volumetric weight:

        8000 / 5000 × 1000
        = 1600g

    Therefore:

        chargeable weight = 1600g
    """

    items = [
        make_item(
            item_id="A",
            quantity=1,
            weight_g=1000,
        )
    ]

    candidate = calculate_candidate(
        lane=make_ems_lane(),
        package=make_package(),
        item_quantities={"A": 1},
        items=items,
    )

    assert candidate is not None

    assert candidate.product_weight_g == 1000
    assert candidate.packaging_weight_g == 100
    assert candidate.actual_weight_g == 1100

    assert candidate.volumetric_weight_g == 1600
    assert candidate.chargeable_weight_g == 1600


def test_ems_candidate_rejected_when_chargeable_weight_exceeds_cap():
    """
    Actual weight:

        1100g

    Volumetric:

        1600g

    Chargeable:

        1600g

    EMS cap:

        1500g

    Therefore candidate must be rejected.
    """

    items = [
        make_item(
            item_id="A",
            quantity=1,
            weight_g=1000,
        )
    ]

    candidate = calculate_candidate(
        lane=make_ems_lane(weight_cap_g=1500),
        package=make_package(),
        item_quantities={"A": 1},
        items=items,
    )

    assert candidate is None


# ============================================================
# Validation tests
# ============================================================


def test_unknown_item_id_is_rejected():
    items = [
        make_item(
            item_id="A",
            quantity=1,
            weight_g=500,
        )
    ]

    try:
        calculate_candidate(
            lane=make_itps_lane(),
            package=make_package(),
            item_quantities={"UNKNOWN": 1},
            items=items,
        )
        assert False, "Expected CandidateGenerationError"
    except CandidateGenerationError as exc:
        assert "Unknown item ID" in str(exc)


def test_negative_quantity_is_rejected():
    items = [
        make_item(
            item_id="A",
            quantity=1,
            weight_g=500,
        )
    ]

    try:
        calculate_candidate(
            lane=make_itps_lane(),
            package=make_package(),
            item_quantities={"A": -1},
            items=items,
        )
        assert False, "Expected CandidateGenerationError"
    except CandidateGenerationError as exc:
        assert "Negative quantity" in str(exc)


def test_quantity_above_available_quantity_is_rejected():
    items = [
        make_item(
            item_id="A",
            quantity=2,
            weight_g=500,
        )
    ]

    try:
        calculate_candidate(
            lane=make_itps_lane(),
            package=make_package(),
            item_quantities={"A": 3},
            items=items,
        )
        assert False, "Expected CandidateGenerationError"
    except CandidateGenerationError as exc:
        assert "exceeds available quantity" in str(exc)


def test_non_splittable_partial_quantity_is_rejected():
    items = [
        make_item(
            item_id="A",
            quantity=3,
            weight_g=500,
            splittable=False,
        )
    ]

    try:
        calculate_candidate(
            lane=make_itps_lane(),
            package=make_package(),
            item_quantities={"A": 1},
            items=items,
        )
        assert False, "Expected CandidateGenerationError"
    except CandidateGenerationError as exc:
        assert "cannot be partially assigned" in str(exc)


# ============================================================
# Candidate generation tests
# ============================================================


def test_generate_candidates_for_multiple_lanes():
    items = [
        make_item(
            item_id="A",
            quantity=1,
            weight_g=500,
        )
    ]

    candidates = generate_shipment_candidates(
        items=items,
        packages=[make_package()],
        lanes=[
            make_itps_lane(),
            make_ems_lane(),
        ],
    )

    lanes = {
        candidate.lane
        for candidate in candidates
    }

    assert "ITPS" in lanes
    assert "EMS" in lanes


def test_generate_candidates_for_multiple_packages():
    items = [
        make_item(
            item_id="A",
            quantity=1,
            weight_g=500,
        )
    ]

    small_package = Package(
        package_id="SMALL",
        name="Small package",
        tare_weight_g=50,
        length_cm=Decimal("10"),
        width_cm=Decimal("10"),
        height_cm=Decimal("10"),
        cost_minor=25,
        max_product_weight_g=1000,
    )

    large_package = Package(
        package_id="LARGE",
        name="Large package",
        tare_weight_g=200,
        length_cm=Decimal("30"),
        width_cm=Decimal("30"),
        height_cm=Decimal("30"),
        cost_minor=75,
        max_product_weight_g=5000,
    )

    candidates = generate_shipment_candidates(
        items=items,
        packages=[
            small_package,
            large_package,
        ],
        lanes=[make_itps_lane()],
    )

    package_ids = {
        candidate.package_id
        for candidate in candidates
    }

    assert "SMALL" in package_ids
    assert "LARGE" in package_ids


def test_generate_candidates_removes_infeasible_itps_options():
    """
    Product:

        4950g

    Packaging:

        100g

    Actual:

        5050g

    ITPS cap:

        5000g

    Therefore no ITPS candidate should be generated.
    """

    items = [
        make_item(
            item_id="A",
            quantity=1,
            weight_g=4950,
        )
    ]

    candidates = generate_shipment_candidates(
        items=items,
        packages=[make_package()],
        lanes=[make_itps_lane()],
    )

    assert candidates == []


def test_generate_candidates_respects_non_splittable_item():
    """
    A non-splittable item with quantity 2 must appear as
    quantity 2 inside a candidate, never quantity 1.
    """

    items = [
        make_item(
            item_id="A",
            quantity=2,
            weight_g=500,
            splittable=False,
        )
    ]

    candidates = generate_shipment_candidates(
        items=items,
        packages=[make_package()],
        lanes=[make_itps_lane()],
    )

    assert len(candidates) > 0

    quantities = {
        candidate.item_quantities["A"]
        for candidate in candidates
    }

    assert quantities == {2}


def test_generate_candidates_allows_splittable_quantity():
    """
    A splittable item with quantity 3 should produce candidates
    containing 1, 2, and 3 units where feasible.
    """

    items = [
        make_item(
            item_id="A",
            quantity=3,
            weight_g=500,
            splittable=True,
        )
    ]

    candidates = generate_shipment_candidates(
        items=items,
        packages=[make_package()],
        lanes=[make_itps_lane()],
    )

    quantities = {
        candidate.item_quantities["A"]
        for candidate in candidates
    }

    assert quantities == {1, 2, 3}