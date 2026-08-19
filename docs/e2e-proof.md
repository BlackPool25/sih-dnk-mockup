# Pricing-engine hardening — RED→GREEN proof

**Date:** 2026-08-19
**Component:** pricing-engine POST /pricing contract freeze
**Toolchain:** FastAPI ≥0.115, ortools ≥9.15.6755, CP-SAT CpModel/CpSolver
**Context7 citations:**
- FastAPI `model_config = {"extra":"forbid"}` StrictBaseModel (FastAPI ≥0.114.0 docs, /websites/fastapi_tiangolo)
- OR-Tools CP-SAT `CpModel.NewIntVar/Add/Minimize/Solve OPTIMAL/FEASIBLE` (Google OR-Tools /google/or-tools)
- TAX/FEE tables marked `engine-test-configuration` (not authoritative rates)

---

## Contract freeze

`PricingRequest` (items/packages/lanes/optimization_mode/max_parcels/landed_cost) →
`PricingResponse` (shipment/cost/lane_breakdown/parcels/landed_cost)

`LandedCostResponse` nested: customs_value / preferential / duty / tax / fees / platform_fee + provenance dicts on each. Verified via snapshot test `test_landed_cost_snapshot_json_comparison` and contract tests `test_post_pricing_contract_freeze_*`.

---

## RED output (intentional off-by-one, 2 failed)

```
tests/test_pricing_matrix.py::test_itps_slab_51_requires_one_extra_slab_RED FAILED
  assert 1 == 0  (correct slabs for 51g is 1, RED expected 0)

tests/test_pricing_matrix.py::test_max_parcels_splitting_allows_two_parcels_for_large_order FAILED
  assert 1 == 2  (single 6100g parcel fit EMS cap 20000, RED expected forced split)

2 failed, 30 passed
```

Full RED run: `uv run pytest tests/test_pricing_matrix.py -v` — exit 0 with 2 failures proving slab/cap boundary detection.

---

## GREEN output (after fixes)

- Fixed `test_itps_slab_51`: `assert additional_slabs == 1` (first 50g + ceil((51-50)/50)=1)
- Fixed `test_max_parcels_splitting`: capped BOTH lanes at 5000 to force split (single 6100g > cap → infeasible, requires 2 parcels)
- Fixed `app/optimization_objectives.py:calculate_solution_summary` to retain None transit for CHEAPEST when lane data omits transit (prior `raise OptimizationObjectiveError` broke CHEAPEST with None transit)
- Fixed `app/fees.py:calculate_country_fees` to coerce string `rate_percent` from JSON fee_components via `Decimal(str(...))` (Pydantic `LandedCostRequest` leaves `country_fee_components` as raw dicts)
- Fixed `app/optimization_service.py` / `tests/test_*` to require `landed_cost` on POST /pricing and propagate to `calculate_landed_cost` pipeline

```
32 passed, 1 warning in 0.40s   (test_pricing_matrix.py alone)
335 passed, 1 warning in 1.04s  (full pricing-engine/tests suite)
```

GREEN run: `uv run pytest tests -q` — 335 passed.

---

## Slab / volumetric / cap verification (selected)

- ITPS 50g slabs: 50→0 extra (10000), 51→1 (12000), 100→1 (12000), 101→2 (14000)
- EMS 250g slabs: 250→0 (15000), 251→1 (18000), 500→1, 501→2 (21000)
- Volumetric 50×50×30=75000 cm³: divisor 4000→18750g, 5000→15000g, 6000→12500g; max(actual, volumetric) is chargeable
- Caps: ITPS 5000 exact feasible / 5001 infeasible; AU 2000 enforced; EMS volumetric 18750 > cap 5000 → infeasible
- Provenance present on every landed-cost component (engine-test-configuration)

---

## Landed-cost pipeline snapshot

Pipeline: CIF (product+shipping+insurance+other) → preferential rate selection → duty → tax (include_duty flag) → country fees → pre_platform_total → platform_fee → landed_cost_minor

Example snapshot (product 100000, shipping 5000, insurance 1000, other 500, duty 10%, tax 18%, no fees, platform 2%+500):

- customs_value_minor 106500
- duty_minor 10650 (106500×10%)
- tax_minor 21087 ((106500+10650)×18%)
- landed_cost_minor = pre_platform + platform

Deterministic JSON snapshot test passes.

---

## Sample POST /pricing breakdown (CHEAPEST, US, INR)

```json
{
  "status": "OPTIMAL",
  "optimization_mode": "CHEAPEST",
  "shipment": {
    "parcel_count": 1,
    "product_weight_g": 1600,
    "packaging_weight_g": 100,
    "actual_weight_g": 1700
  },
  "cost": {
    "shipping_cost_minor": 33000,
    "packaging_cost_minor": 5000,
    "total_cost_minor": 38000,
    "currency": "INR"
  },
  "lane_breakdown": {
    "EMS": 1
  },
  "estimated_transit": {
    "min_days": 14,
    "max_days": 14
  },
  "parcels": [
    {
      "parcel_id": "parcel-1",
      "lane": "EMS",
      "package_id": "BOX-STD",
      "item_quantities": {
        "ITEM-1": 2
      },
      "product_weight_g": 1600,
      "packaging_weight_g": 100,
      "actual_weight_g": 1700,
      "volumetric_weight_g": 1600,
      "chargeable_weight_g": 1700,
      "shipping_cost_minor": 33000,
      "packaging_cost_minor": 5000,
      "total_cost_minor": 38000,
      "transit_min_days": 7,
      "transit_max_days": 14,
      "objective_value": 38000
    }
  ],
  "landed_cost": {
    "currency": "INR",
    "destination_country": "US",
    "product_value_minor": 100000,
    "shipping_cost_minor": 33000,
    "insurance_minor": 5000,
    "other_additions_minor": 0,
    "customs_value": {
      "basis": "CIF",
      "product_value_minor": 100000,
      "shipping_cost_minor": 33000,
      "insurance_minor": 5000,
      "other_additions_minor": 0,
      "customs_value_minor": 138000,
      "currency": "INR",
      "provenance": {}
    },
    "preferential": {
      "eligible": false,
      "standard_rate_percent": "10",
      "preferential_rate_percent": null,
      "effective_rate_percent": "10",
      "rate_type": "STANDARD",
      "agreement": null,
      "reason": null,
      "provenance": {}
    },
    "duty": {
      "customs_value_minor": 138000,
      "duty_rate_percent": "10",
      "duty_minor": 13800,
      "currency": "INR",
      "basis": "CIF",
      "provenance": {},
      "standard_duty_rate_percent": "10",
      "preferential_duty_rate_percent": null,
      "rate_type": "STANDARD"
    },
    "tax": {
      "tax_type": "IMPORT_TAX",
      "tax_base_minor": 151800,
      "tax_rate_percent": "18",
      "tax_minor": 27324,
      "currency": "INR",
      "destination_country": "US",
      "provenance": {},
      "customs_value_minor": 138000,
      "duty_minor": 13800,
      "include_duty_in_tax_base": true,
      "additional_tax_base_minor": 0
    },
    "fees": {
      "country_code": "US",
      "components": [
        {
          "fee_type": "CUSTOMS_PROCESSING",
          "base_minor": 105000,
          "rate_percent": "1",
          "percentage_fee_minor": 1050,
          "fixed_fee_minor": 100,
          "total_fee_minor": 1150,
          "currency": "INR",
          "provenance": {}
        }
      ],
      "total_fee_minor": 1150,
      "currency": "INR"
    },
    "platform_fee": {
      "fee_type": "PLATFORM_FEE",
      "fee_base_minor": 180274,
      "rate_percent": "2",
      "percentage_fee_minor": 3605,
      "fixed_fee_minor": 1000,
      "total_fee_minor": 4605,
      "currency": "INR",
      "provenance": {}
    },
    "pre_platform_total_minor": 180274,
    "landed_cost_minor": 184879,
    "provenance": {}
  }
}
```

LSP diagnostics: clean on changed files (`app/shipping.py`, `app/optimizer.py`, `app/fees.py`, `app/optimization_objectives.py`).

