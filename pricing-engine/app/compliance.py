from typing import Any
from app.schemas import PricingRequest

class ComplianceError(Exception):
    """Raised when compilance processing cannot be completed"""
def check_compliance(
        order:PricingRequest,
        classifications:list[dict[str,Any]],
)->dict[str,Any]:
    checks:list[dict[str,Any]]=[]
    if len(classifications)!=len(order.items):
        raise ComplianceError("Classification result count does not match order item count")
    category_failures=[
        result
        for result in classifications
        if result.get("classification_status")
        not in {"classified","category_only"}
    ]
    if category_failures:
        checks.append(
            {
                "check": "product_classification",
                "status": "FAIL",
                "severity": "ERROR",
                "message": (
                    "One or more items could not be classified."
                ),
            }
        )
    else:
        checks.append(
            {
                "check": "product_classification",
                "status": "PASS",
                "severity": "INFO",
                "message": "All items have a valid product category.",
            }
        )

    missing_hs=[
        result
        for result in classifications
        if result.get("hs_code") is None
    ]
    if missing_hs:
        checks.append(
            {
                "check": "hs_classification",
                "status": "REVIEW",
                "severity": "WARNING",
                "message": (
                    "One or more items do not have an HS code. "
                    "Duty/tax calculations may require manual review."
                ),
            }
        )
    else:
        checks.append(
            {
                "check": "hs_classification",
                "status": "PASS",
                "severity": "INFO",
                "message": "All items have an HS classification.",
            }
        )
    checks.append(
        {
            "check": "destination_country",
            "status": "PASS",
            "severity": "INFO",
            "message": (
                f"Destination country {order.destination_country} "
                "passed request validation."
            ),
        }
    )
    has_error=any(
        check["status"]=="FAIL"
        for check in checks
    )
    has_review=any(
        check["status"]=="REVIEW"
        for check in checks
    )

    if has_error:
        overall_status="BLOCKED"
        blocked=True
    elif has_review:
        overall_status="REVIEW"
        blocked=False
    else:
        overall_status="PASS"
        blocked=False
    return{
        "status": overall_status,
        "blocked": blocked,
        "destination_country": order.destination_country,
        "checks": checks,
    }