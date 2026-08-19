from typing import Any

from sqlalchemy.orm import Session

from app.repositories import lookup_hs_codes, search_categories
from app.schemas import PricingItem


class ClassificationError(Exception):
    """Raised when an item cannot be classified using the available data."""


def classify_item(
    session: Session,
    item: PricingItem,
) -> dict[str, Any]:
    """
    Classify one pricing item using the existing product-category
    and HS-code repositories.

    The function does not invent a classification. It only returns
    classifications supported by the database.
    """

    categories = search_categories(
        session=session,
        query=item.category_slug,
        limit=5,
    )

    if not categories:
        raise ClassificationError(
            f"No product category found for {item.category_slug!r}"
        )

    exact_category = next(
        (
            category
            for category in categories
            if category["slug"] == item.category_slug
        ),
        None,
    )

    if exact_category is None:
        raise ClassificationError(
            f"Product category {item.category_slug!r} was not found exactly"
        )

    hs_codes = lookup_hs_codes(
        session=session,
        category_slug=item.category_slug,
        limit=10,
    )

    hs_code = hs_codes[0] if hs_codes else None

    return {
        "item_id": item.item_id,
        "category": {
            "slug": exact_category["slug"],
            "name": exact_category["name"],
            "hs6_default": exact_category["hs6_default"],
            "pbe_desc_template": exact_category["pbe_desc_template"],
            "certifications": exact_category["certifications"],
            "lane_fit": exact_category["lane_fit"],
        },
        "hs_code": hs_code,
        "classification_status": (
            "classified"
            if hs_code is not None
            else "category_only"
        ),
        "provenance": {
            "category": exact_category["provenance"],
            "hs_code": (
                hs_code["provenance"]
                if hs_code is not None
                else None
            ),
        },
    }


def classify_order(
    session: Session,
    items: list[PricingItem],
) -> list[dict[str, Any]]:
    """
    Classify every item in an order.

    Classification is performed independently for each item so that
    one item's classification does not affect another item's result.
    """

    results: list[dict[str, Any]] = []

    for item in items:
        results.append(
            classify_item(
                session=session,
                item=item,
            )
        )

    return results