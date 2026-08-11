"""Filling-rule seeds (rework wave 0) — the validation rules the booking
pipeline enforces on PBE/parcel data (later waves read these from
validate.py).  Every rule names fields that exist in the PBE-III/IV
schemas — provenance points at the forms-pbe fields doc.
"""

from __future__ import annotations

from app.models import FillingRule
from app.services.seed._common import SNAPSHOT_DATE, VERIFIED_AT

# --- filling rules --------------------------------------------------------------
#
# Validation rules the booking pipeline enforces on PBE/parcel data (later
# waves read these from validate.py).  Every rule names fields that exist in
# the PBE-III/IV schemas — provenance points at the forms-pbe fields doc.
# Money is integer minor units; field names below are the DocumentData keys.

RULES_SOURCE_URL = "data/02-dnk-documents/forms-pbe/pbe-iii-iv-fields.md"

RULES_SPECS: list[dict[str, object]] = [
    {
        "rule_key": "kyc_iec_or_gstin",
        "severity": "error",
        "params": {"identifier_fields": ["iec", "gstin"], "min_present": 1},
        "message": "booking requires at least one of IEC or GSTIN",
    },
    {
        "rule_key": "dgft_iec_missing",
        "severity": "error",
        "params": {"identifier_fields": ["iec"], "required": 1},
        "message": "DGFT registration data missing",
    },
    {
        "rule_key": "gross_net_110",
        "severity": "error",
        "params": {
            "max_ratio": 1.10,
            "gross_field": "gross_weight",
            "net_field": "net_weight",
        },
        "message": "gross weight exceeds 110% of net weight",
    },
    {
        "rule_key": "fob_le_invoice",
        "severity": "error",
        "params": {"fob_field": "fob_value", "invoice_field": "amount_inr"},
        "message": "FOB value exceeds invoice value",
    },
    {
        "rule_key": "sub_piece_value_sum",
        "severity": "error",
        "params": {
            "unit_field": "unit_value_minor",
            "parcel_field": "value_minor",
            "operator": "le",
        },
        "message": "Value of Sub pieces does not match",
    },
    {
        "rule_key": "sub_piece_weight_sum",
        "severity": "error",
        "params": {
            "unit_field": "piece_gross_g",
            "parcel_field": "weight_grams",
            "operator": "le",
        },
        "message": "Weight of Sub pieces does not match",
    },
    {
        "rule_key": "desc_hs_match",
        "severity": "error",
        "params": {"desc_field": "product_description", "hs_field": "cth"},
        "message": "Description does not match with HS Code/CTH",
    },
    {
        "rule_key": "itch_restricted_policy",
        "severity": "warning",
        "params": {"restricted_hs6": ["5303", "4403"]},
        "message": "ITCH code not applicable for restricted policy",
    },
]


def _import_rules(session: object) -> int:
    if len(RULES_SPECS) != 8:
        raise RuntimeError(
            f"filling-rules gate failed: {len(RULES_SPECS)} rules, expected 8"
        )
    for spec in RULES_SPECS:
        session.add(FillingRule(  # type: ignore[attr-defined]
            rule_key=spec["rule_key"],  # type: ignore[arg-type]
            enabled=True,
            severity=spec["severity"],  # type: ignore[arg-type]
            applies_to=None,
            params=spec["params"],  # type: ignore[arg-type]
            message=spec["message"],  # type: ignore[arg-type]
            source_url=RULES_SOURCE_URL, source_level="L2", confidence="high",
            is_estimate=False, effective_from=SNAPSHOT_DATE, verified_at=VERIFIED_AT,
        ))
    return len(RULES_SPECS)
