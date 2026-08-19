from decimal import Decimal

import pytest

from app.packaging import (
    Package,
    PackagingError,
    build_parcel,
    calculate_package_volume_cm3,
    calculate_product_weight,
    can_package_product,
)


def small_package() -> Package:
    return Package(
        package_id="BOX-S",
        name="Small box",
        tare_weight_g=100,
        length_cm=Decimal("20"),
        width_cm=Decimal("15"),
        height_cm=Decimal("10"),
        cost_minor=500,
        max_product_weight_g=2000,
    )


def test_calculate_product_weight():
    result = calculate_product_weight(
        unit_weight_g=500,
        quantity=3,
    )

    assert result == 1500


def test_package_can_contain_product():
    package = small_package()

    assert can_package_product(
        package=package,
        product_weight_g=1500,
    ) is True


def test_package_rejects_product_above_capacity():
    package = small_package()

    assert can_package_product(
        package=package,
        product_weight_g=2001,
    ) is False


def test_build_parcel_adds_packaging_weight():
    package = small_package()

    parcel = build_parcel(
        package=package,
        product_weight_g=1900,
    )

    assert parcel.product_weight_g == 1900
    assert parcel.packaging_weight_g == 100
    assert parcel.actual_weight_g == 2000


def test_actual_weight_includes_packaging():
    package = Package(
        package_id="BOX-5KG",
        name="5kg box",
        tare_weight_g=200,
        length_cm=Decimal("30"),
        width_cm=Decimal("20"),
        height_cm=Decimal("20"),
        cost_minor=1000,
        max_product_weight_g=5000,
    )

    parcel = build_parcel(
        package=package,
        product_weight_g=4900,
    )

    assert parcel.product_weight_g == 4900
    assert parcel.packaging_weight_g == 200
    assert parcel.actual_weight_g == 5100


def test_package_volume():
    package = small_package()

    volume = calculate_package_volume_cm3(package)

    assert volume == Decimal("3000")


def test_zero_product_weight_is_rejected():
    package = small_package()

    with pytest.raises(
        PackagingError,
        match="Product weight must be greater than zero",
    ):
        build_parcel(
            package=package,
            product_weight_g=0,
        )


def test_negative_packaging_weight_is_rejected():
    package = Package(
        package_id="BAD",
        name="Invalid package",
        tare_weight_g=-1,
        length_cm=Decimal("20"),
        width_cm=Decimal("20"),
        height_cm=Decimal("20"),
        cost_minor=100,
    )

    with pytest.raises(
        PackagingError,
        match="Packaging weight cannot be negative",
    ):
        build_parcel(
            package=package,
            product_weight_g=500,
        )


def test_package_capacity_is_checked():
    package = small_package()

    with pytest.raises(
        PackagingError,
        match="cannot contain",
    ):
        build_parcel(
            package=package,
            product_weight_g=2500,
        )