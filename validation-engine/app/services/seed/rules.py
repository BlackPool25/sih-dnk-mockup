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
    # --- country_ rules: hard blocks (severity=error) ---
    {
        "rule_key": "country_wood_ie_block",
        "severity": "error",
        "params": {"prohibited_destinations": ["IE"], "material": "wood"},
        "message": "Wood/wicker products prohibited for Ireland",
    },
    {
        "rule_key": "country_food_block",
        "severity": "error",
        "params": {"prohibited_categories": ["food"]},
        "message": "Food items are prohibited for all destinations",
    },
    {
        "rule_key": "country_plants_block",
        "severity": "error",
        "params": {"prohibited_categories": ["plants", "seeds"]},
        "message": "Plants and seeds are prohibited for all destinations",
    },
    {
        "rule_key": "country_lithium_block",
        "severity": "error",
        "params": {"prohibited_hs": ["8506", "8507"]},
        "message": "Lithium batteries are prohibited for all destinations",
    },
    {
        "rule_key": "country_liquids_threshold_block",
        "severity": "error",
        "params": {"threshold_ml": 100},
        "message": "Liquids above threshold are blocked",
    },
    # --- country_ rules: soft warnings (severity=warning) ---
    {
        "rule_key": "country_ayurveda_cosmetics_warn",
        "severity": "warning",
        "params": {"requires_noc": True},
        "message": "Ayurveda/cosmetics products require NOC",
    },
    {
        "rule_key": "country_magnets_threshold_warn",
        "severity": "warning",
        "params": {"max_mg": 4.5},
        "message": "Magnets near 4.5mG threshold need clearance",
    },
    {
        "rule_key": "country_bicon_biosecurity_warn",
        "severity": "warning",
        "params": {"destinations": ["AU"], "materials": ["wood", "jute"]},
        "message": "Australia biosecurity BICON check required for wood/jute",
    },
    {
        "rule_key": "country_duty_applicability_flag",
        "severity": "warning",
        "params": {"us_de_minimis_suspended": True, "uk_threshold_minor": 13500},
        "message": "Duty applicability flagged",
    },
    # --- country_ rules: per-destination hard blocks (6 additional) ---
    {
        "rule_key": "country_wood_de_block",
        "severity": "error",
        "params": {"prohibited_destinations": ["DE"], "material": "wood"},
        "message": "Wood/wicker products prohibited for Germany",
    },
    {
        "rule_key": "country_wood_fr_block",
        "severity": "error",
        "params": {"prohibited_destinations": ["FR"], "material": "wood"},
        "message": "Wood/wicker products prohibited for France",
    },
    {
        "rule_key": "country_food_au_block",
        "severity": "error",
        "params": {"prohibited_destinations": ["AU"], "category": "food"},
        "message": "Food items prohibited for Australia",
    },
    {
        "rule_key": "country_plants_nz_block",
        "severity": "error",
        "params": {"prohibited_destinations": ["NZ"], "category": "plants"},
        "message": "Plants and seeds prohibited for New Zealand",
    },
    {
        "rule_key": "country_leather_us_block",
        "severity": "error",
        "params": {"prohibited_destinations": ["US"], "category": "leather"},
        "message": "Leather goods prohibited for USA (Lacey Act)",
    },
    {
        "rule_key": "country_textiles_eu_block",
        "severity": "error",
        "params": {"prohibited_destinations": ["DE", "FR", "IT", "ES", "NL", "BE"], "category": "textiles"},
        "message": "Textiles prohibited for EU destinations (REACH)",
    },
]


def _import_rules(session: object) -> int:
    if len(RULES_SPECS) < 22:
        raise RuntimeError(
            f"filling-rules gate failed: {len(RULES_SPECS)} rules, expected >= 22"
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
