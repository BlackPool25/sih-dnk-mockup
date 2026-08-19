from dataclasses import dataclass
from decimal import Decimal


class PackagingError(Exception):
    """Raised when a packaging calculation cannot be completed."""


@dataclass(frozen=True)
class Package:
    """
    Represents one available packaging option.

    Weight is stored in grams.
    Dimensions are stored in centimeters.
    Cost is stored in minor currency units.
    """

    package_id: str
    name: str

    tare_weight_g: int

    length_cm: Decimal
    width_cm: Decimal
    height_cm: Decimal

    cost_minor: int

    max_product_weight_g: int | None = None


@dataclass(frozen=True)
class Parcel:
    """
    Represents a constructed shipment parcel.

    Product weight + packaging weight = actual parcel weight.
    """

    package_id: str

    product_weight_g: int
    packaging_weight_g: int

    actual_weight_g: int

    length_cm: Decimal
    width_cm: Decimal
    height_cm: Decimal

    packaging_cost_minor: int


def calculate_product_weight(
    unit_weight_g: int,
    quantity: int,
) -> int:
    """
    Calculate total product weight for an item.

    Example:
        unit_weight_g = 500
        quantity = 3

        total = 1500g
    """

    if unit_weight_g <= 0:
        raise PackagingError(
            "Unit product weight must be greater than zero"
        )

    if quantity <= 0:
        raise PackagingError(
            "Quantity must be greater than zero"
        )

    return unit_weight_g * quantity


def validate_package(package: Package) -> None:
    """
    Validate a packaging option before it is used.
    """

    if not package.package_id.strip():
        raise PackagingError(
            "Package ID cannot be empty"
        )

    if package.tare_weight_g < 0:
        raise PackagingError(
            "Packaging weight cannot be negative"
        )

    if package.length_cm <= 0:
        raise PackagingError(
            "Package length must be greater than zero"
        )

    if package.width_cm <= 0:
        raise PackagingError(
            "Package width must be greater than zero"
        )

    if package.height_cm <= 0:
        raise PackagingError(
            "Package height must be greater than zero"
        )

    if package.cost_minor < 0:
        raise PackagingError(
            "Packaging cost cannot be negative"
        )

    if (
        package.max_product_weight_g is not None
        and package.max_product_weight_g <= 0
    ):
        raise PackagingError(
            "Maximum product weight must be greater than zero"
        )


def can_package_product(
    package: Package,
    product_weight_g: int,
) -> bool:
    """
    Determine whether a packaging option can contain the product.

    The maximum product weight applies to product weight before
    packaging tare weight is added.
    """

    validate_package(package)

    if product_weight_g <= 0:
        raise PackagingError(
            "Product weight must be greater than zero"
        )

    if package.max_product_weight_g is None:
        return True

    return product_weight_g <= package.max_product_weight_g


def build_parcel(
    package: Package,
    product_weight_g: int,
) -> Parcel:
    """
    Construct a parcel from product weight and packaging.

    The actual shipping weight includes packaging weight.
    """

    if not can_package_product(
        package=package,
        product_weight_g=product_weight_g,
    ):
        raise PackagingError(
            f"Package {package.package_id!r} cannot contain "
            f"{product_weight_g}g of product"
        )

    actual_weight_g = (
        product_weight_g
        + package.tare_weight_g
    )

    return Parcel(
        package_id=package.package_id,
        product_weight_g=product_weight_g,
        packaging_weight_g=package.tare_weight_g,
        actual_weight_g=actual_weight_g,
        length_cm=package.length_cm,
        width_cm=package.width_cm,
        height_cm=package.height_cm,
        packaging_cost_minor=package.cost_minor,
    )


def calculate_package_volume_cm3(
    package: Package,
) -> Decimal:
    """
    Calculate packaging volume in cubic centimeters.
    """

    validate_package(package)

    return (
        package.length_cm
        * package.width_cm
        * package.height_cm
    )