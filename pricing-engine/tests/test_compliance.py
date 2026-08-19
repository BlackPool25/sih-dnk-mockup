from decimal import Decimal

import pytest

from app.compliance import ComplianceError, check_compliance
from app.schemas import PricingRequest


def make_order() -> PricingRequest:
    return PricingRequest(
        destination_country="US",
        optimization_mode="CHEAPEST",
        items=[
            {
                "item_id": "item-1",
                "category_slug": "jute-products",
                "quantity": 1,
                "unit_weight_g": 500,
                "dimensions_cm": {
                    "length_cm": Decimal("20"),
                    "width_cm": Decimal("15"),
                    "height_cm": Decimal("5"),
                },
                "unit_value": {
                    "amount_minor": 10000,
                    "currency": "INR",
                },
                "splittable": True,
            }
        ],
    )


def make_classification(
    hs_code: bool = True,
) -> list[dict]:
    return [
        {
            "item_id": "item-1",
            "classification_status": (
                "classified" if hs_code else "category_only"
            ),
            "category": {
                "slug": "jute-products",
                "name": "Jute products",
            },
            "hs_code": (
                {
                    "hs6": "5310",
                    "itc_hs_8": "53101091",
                    "hts_10": None,
                    "description": "Jute woven fabrics",
                    "category_slug": "jute-products",
                    "provenance": {},
                }
                if hs_code
                else None
            ),
            "provenance": {
                "category": {},
                "hs_code": {},
            },
        }
    ]


def test_compliance_passes_with_complete_classification():
    result = check_compliance(
        order=make_order(),
        classifications=make_classification(hs_code=True),
    )

    assert result["status"] == "PASS"
    assert result["blocked"] is False
    assert result["destination_country"] == "US"

    assert len(result["checks"]) == 3

    assert all(
        check["status"] == "PASS"
        for check in result["checks"]
    )


def test_compliance_requests_review_when_hs_is_missing():
    result = check_compliance(
        order=make_order(),
        classifications=make_classification(hs_code=False),
    )

    assert result["status"] == "REVIEW"
    assert result["blocked"] is False

    hs_check = next(
        check
        for check in result["checks"]
        if check["check"] == "hs_classification"
    )

    assert hs_check["status"] == "REVIEW"
    assert hs_check["severity"] == "WARNING"


def test_compliance_blocks_invalid_classification_status():
    classifications = make_classification()

    classifications[0]["classification_status"] = "failed"

    result = check_compliance(
        order=make_order(),
        classifications=classifications,
    )

    assert result["status"] == "BLOCKED"
    assert result["blocked"] is True

    classification_check = next(
        check
        for check in result["checks"]
        if check["check"] == "product_classification"
    )

    assert classification_check["status"] == "FAIL"
    assert classification_check["severity"] == "ERROR"


def test_compliance_rejects_mismatched_classification_count():
    with pytest.raises(
        ComplianceError,
        match="Classification result count",
    ):
        check_compliance(
            order=make_order(),
            classifications=[],
        )