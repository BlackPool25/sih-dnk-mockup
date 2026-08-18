"""Country-specific rule evaluators — hard blocks, soft warnings, and duty flags.

Each evaluator receives ``(DocumentData, params)`` and returns **True** when the
rule is VIOLATED.  The caller (``validate_document_rules``) maps the result to
an ``error`` (blocking, hard-fail) or ``warning`` (non-blocking) based on the
rule's ``severity`` field in the ``filling_rules`` table.  Evaluators are
self-contained: no DB access, no LLM — deterministic checks only.

Design: these functions live in their own module so task 9 can wire them into
validate.py without modifying validate.py itself.  The ``_EVALUATORS`` dict at
module scope follows the same ``dict[str, Callable[[DocumentData, dict], bool]]``
contract as the one in validate.py.
"""

from __future__ import annotations

from collections.abc import Callable

from app.services.docs.document import DocumentData

# ---------------------------------------------------------------------------
# Hard blocks — return True = violation, severity=error, action=blocking
# ---------------------------------------------------------------------------


def _eval_wood_ie_block(data: DocumentData, params: dict) -> bool:
    """Wood/wicker products → Ireland are a hard block.

    Trigger: destination_country is "IE" AND the category_slug contains "wood".
    Destinations: IE (Ireland) only.
    Severity: error (blocking).

    Real-world basis: SPS (sanitary & phytosanitary) — Ireland enforces strict
    timber treatment (ISPM 15) for wooden articles; the exporter must clear
    phytosanitary compliance before customs accept the consignment.
    """
    return data.destination_country == "IE" and "wood" in data.category_slug.lower()


def _eval_food_block(data: DocumentData, params: dict) -> bool:
    """Food items → all destinations are blocked.

    Trigger: category_slug contains "food".
    Destinations: any (universal block).
    Severity: error (blocking).

    Real-world basis: exported food/consumables require FSSAI export clearance
    and destination-country FDA-equivalent pre-approval — this is never
    routable through a generic courier portal.
    """
    return "food" in data.category_slug.lower()


def _eval_plants_block(data: DocumentData, params: dict) -> bool:
    """Plants/seeds → all destinations are blocked.

    Trigger: category_slug contains "plant".
    Destinations: any (universal block).
    Severity: error (blocking).

    Real-world basis: plant material (seeds, live plants, bulbs, cuttings)
    requires a phytosanitary certificate from the Plant Quarantine Authority
    and an import permit from the destination country — a courier manifest
    cannot substitute.
    """
    return "plant" in data.category_slug.lower()


def _eval_lithium_block(data: DocumentData, params: dict) -> bool:
    """Lithium batteries/battery-powered articles → all destinations blocked.

    Trigger: any HS code row whose ``hs6`` starts with "8506" or "8507".
    Destinations: any (universal block).
    Severity: error (blocking).

    Real-world basis: lithium cells (HS 8506) and lithium-ion accumulators
    (HS 8507) are IATA/ICAO Dangerous Goods Class 9 — courier shipments must
    comply with Section II of PI 965/PI 966/PI 967, requiring a UN38.3 test
    summary and DG declaration that a generic portal cannot produce.
    """
    for hs in data.hs_codes:
        if hs.get("hs6", "").startswith(("8506", "8507")):
            return True
    return False


def _eval_liquids_threshold_block(data: DocumentData, params: dict) -> bool:
    """Liquids above volume threshold → blocked.

    Trigger: category_slug matches a liquid keyword (perfume / oil / liquid /
    cosmetic) AND quantity > ``params["threshold_ml"]`` (default 100).
    Destinations: any.
    Severity: error (blocking).

    Real-world basis: liquids > 100 ml are restricted under IATA air-cargo
    dangerous-goods regulations (flammable/combustible liquids in UN Class 3);
    a courier portal without DG paperwork cannot ship them.
    """
    threshold = params.get("threshold_ml", 100)
    is_liquid = any(
        kw in data.category_slug.lower() for kw in ["perfume", "oil", "liquid", "cosmetic"]
    )
    if is_liquid and data.quantity > threshold:
        return True
    return False


# ---------------------------------------------------------------------------
# Soft warnings — return True = violation, severity=warning, action=fix_value
# ---------------------------------------------------------------------------


def _eval_ayurveda_cosmetics_warn(data: DocumentData, params: dict) -> bool:
    """Ayurvedic/herbal/cosmetic products → NOC (No Objection Certificate) warning.

    Trigger: category_slug contains "ayurved", "cosmetic", or "herbal".
    Destinations: any.
    Severity: warning (non-blocking — prompts the exporter to obtain the NOC
    but does not reject the document).

    Real-world basis: Ayurvedic/Unani/Siddha formulations and cosmetics
    require a No Objection Certificate from the AYUSH ministry or DCGI
    before export clearance; courier portals flag this so the exporter
    attaches the NOC before the counter visit.
    """
    return any(kw in data.category_slug.lower() for kw in ["ayurved", "cosmetic", "herbal"])


def _eval_magnets_threshold_warn(data: DocumentData, params: dict) -> bool:
    """Magnetised articles near the 4.5 mG threshold → warning.

    Trigger: category_slug contains "magnet".
    Threshold: params["max_mg"] (default 4.5 — the IATA magnetic-field limit
    at 2.1 m from the package surface for air cargo).
    Destinations: any.
    Severity: warning (non-blocking — flags the item so the exporter can
    verify field-strength compliance before shipping).

    Real-world basis: IATA DGR UN2807 (Magnetised Material) — packages must
    not exceed 0.00525 gauss (5.25 mG) at 4.6 m, which the courier measures
    at a distance of 2.1 m (≈ 4.5 mG).  Items above this may require
    shielding or re-classification.
    """
    return "magnet" in data.category_slug.lower()


def _eval_bicon_biosecurity_warn(data: DocumentData, params: dict) -> bool:
    """AU biosecurity — BICON check for wood/jute products.

    Trigger: destination_country is "AU" AND category_slug contains "wood" or
    "jute".
    Destinations: AU (Australia) only.
    Severity: warning (non-blocking — the exporter must verify that the
    commodity is permitted under BICON before shipment, but the document
    itself is not rejected).

    Real-world basis: Australia's Biosecurity Import Conditions (BICON)
    database lists specific requirements for timber/bamboo (must be ISPM 15
    treated and free of bark) and jute/plant-fibre articles (may require
    fumigation).  An exporter who ships without checking BICON risks
    destruction at the border.
    """
    if data.destination_country != "AU":
        return False
    return any(kw in data.category_slug.lower() for kw in ["wood", "jute"])


def _eval_duty_applicability_flag(data: DocumentData, params: dict) -> bool:
    """Flag duty applicability for US (de minimis suspended) and UK (£135 threshold).

    Trigger:
      - US: always True (Section 321 de minimis is suspended for many
        goods of Chinese origin under recent executive orders; duty
        applicability flag is ON by default).
      - GB (UK): True when ``value_minor`` > £135.00 (13 500 paise) — the
        UK abolished the £15 Low Value Consignment Relief and set the
        customs-duty de minimis at £135.

    Destinations: US, GB.
    Severity: warning (non-blocking — the renderer uses this flag to decide
    whether to render the duty-line block; the document itself is never
    rejected on this flag alone).

    Real-world basis:
      - US EO 14195 (Feb 2025) and earlier Section 301/321 amendments
        removed de minimis for many categories.
      - UK — since 1 Jan 2021, goods valued > £135 incur import VAT and
        customs duty at the border (the £15 LVCR was abolished).
    """
    if data.destination_country == "US":
        return True  # flag always on for US
    if data.destination_country == "GB" and (data.value_minor or 0) > 13500:
        return True
    return False


# --- per-destination hard blocks (6 additional) ---


def _eval_wood_de_block(data: DocumentData, params: dict) -> bool:
    """Wood/wicker products → Germany are a hard block.

    Trigger: destination_country is "DE" AND category_slug contains "wood".
    Destinations: DE (Germany) only.
    Severity: error (blocking).
    """
    return data.destination_country == "DE" and "wood" in data.category_slug.lower()


def _eval_wood_fr_block(data: DocumentData, params: dict) -> bool:
    """Wood/wicker products → France are a hard block.

    Trigger: destination_country is "FR" AND category_slug contains "wood".
    Destinations: FR (France) only.
    Severity: error (blocking).
    """
    return data.destination_country == "FR" and "wood" in data.category_slug.lower()


def _eval_food_au_block(data: DocumentData, params: dict) -> bool:
    """Food items → Australia are a hard block.

    Trigger: destination_country is "AU" AND category_slug contains "food".
    Destinations: AU (Australia) only.
    Severity: error (blocking).
    """
    return data.destination_country == "AU" and "food" in data.category_slug.lower()


def _eval_plants_nz_block(data: DocumentData, params: dict) -> bool:
    """Plants/seeds → New Zealand are a hard block.

    Trigger: destination_country is "NZ" AND category_slug contains "plant".
    Destinations: NZ (New Zealand) only.
    Severity: error (blocking).
    """
    return data.destination_country == "NZ" and "plant" in data.category_slug.lower()


def _eval_leather_us_block(data: DocumentData, params: dict) -> bool:
    """Leather goods → USA are a hard block (Lacey Act declaration required).

    Trigger: destination_country is "US" AND category_slug contains "leather".
    Destinations: US only.
    Severity: error (blocking).
    """
    return data.destination_country == "US" and "leather" in data.category_slug.lower()


def _eval_textiles_eu_block(data: DocumentData, params: dict) -> bool:
    """Textiles → EU destinations are a hard block (REACH compliance required).

    Trigger: destination_country in EU countries AND category_slug contains "textile".
    Destinations: DE, FR, IT, ES, NL, BE (EU subset).
    Severity: error (blocking).
    """
    eu_countries = {"DE", "FR", "IT", "ES", "NL", "BE"}
    return data.destination_country in eu_countries and "textile" in data.category_slug.lower()


# ---------------------------------------------------------------------------
# Evaluator registry — same contract as validate.py._EVALUATORS
# ---------------------------------------------------------------------------

_EVALUATORS: dict[str, Callable[[DocumentData, dict], bool]] = {
    "country_wood_ie_block": _eval_wood_ie_block,
    "country_food_block": _eval_food_block,
    "country_plants_block": _eval_plants_block,
    "country_lithium_block": _eval_lithium_block,
    "country_liquids_threshold_block": _eval_liquids_threshold_block,
    "country_ayurveda_cosmetics_warn": _eval_ayurveda_cosmetics_warn,
    "country_magnets_threshold_warn": _eval_magnets_threshold_warn,
    "country_bicon_biosecurity_warn": _eval_bicon_biosecurity_warn,
    "country_duty_applicability_flag": _eval_duty_applicability_flag,
    # --- per-destination hard blocks (6 additional) ---
    "country_wood_de_block": _eval_wood_de_block,
    "country_wood_fr_block": _eval_wood_fr_block,
    "country_food_au_block": _eval_food_au_block,
    "country_plants_nz_block": _eval_plants_nz_block,
    "country_leather_us_block": _eval_leather_us_block,
    "country_textiles_eu_block": _eval_textiles_eu_block,
}

__all__ = [
    "_EVALUATORS",
    "_eval_wood_ie_block",
    "_eval_food_block",
    "_eval_plants_block",
    "_eval_lithium_block",
    "_eval_liquids_threshold_block",
    "_eval_ayurveda_cosmetics_warn",
    "_eval_magnets_threshold_warn",
    "_eval_bicon_biosecurity_warn",
    "_eval_duty_applicability_flag",
    "_eval_wood_de_block",
    "_eval_wood_fr_block",
    "_eval_food_au_block",
    "_eval_plants_nz_block",
    "_eval_leather_us_block",
    "_eval_textiles_eu_block",
]
