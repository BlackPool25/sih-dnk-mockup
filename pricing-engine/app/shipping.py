from typing import Any
from decimal import Decimal,ROUND_CEILING

class ShippingCalculationError(Exception):
    """Raised when a shipping calculation cannot be performed"""
def _ceil_decimal(value:Decimal)->int:
    return int(
        value.to_integral_value(
            rounding=ROUND_CEILING
        )
    )
def calculate_itps(
        lane:dict[str,Any],
        actual_weight_g:int,
)->dict[str,Any]:
    if actual_weight_g<=0:
        raise ShippingCalculationError(
            "Actual parcel weight must be greater than zero"
        )
    if lane["lane"]!="ITPS":
        raise ShippingCalculationError(
         f"Expected ITPS lane,got{lane['lane']!r}"   
        )
    weight_cap_g=lane.get("weight_cap_g")
    if(
        weight_cap_g is not None
        and actual_weight_g>weight_cap_g
    ):
        return{
            "lane":"ITPS",
            "feasible":False,
            "reason":(
                f"Actual weight {actual_weight_g}g exceeds "
                f"ITPS weight cap of {weight_cap_g}g"
            ),
            "actual_weight_g":actual_weight_g,
            "chargeable_weight_g":actual_weight_g,
            "shipping_cost_minor":None,
        }
    first_slab_g=lane["first_slab_g"]
    first_slab_rate_minor=lane["first_slab_rate_minor"]
    addl_slab_g=lane["addl_slab_g"]
    addl_slab_rate_minor=lane["addl_slab_rate_minor"]
    if first_slab_g<=0:
        raise ShippingCalculationError(
            "ITPS first slab weight must be greater then zero"
        )
    if addl_slab_g<=0:
        raise ShippingCalculationError(
            "ITPS additonal slab weight must be greater than zero"
        )
    if actual_weight_g<=first_slab_g:
        additional_slabs=0
    else:
        remaining_weight=(
            actual_weight_g-first_slab_g
        )
        additional_slabs=_ceil_decimal(
            Decimal(remaining_weight)/Decimal(addl_slab_g)
        )
    shipping_cost_minor=(
        first_slab_rate_minor+(
            additional_slabs*addl_slab_rate_minor
        )
    )
    return{
        "lane": "ITPS",
        "feasible": True,
        "actual_weight_g": actual_weight_g,
        "volumetric_weight_g": None,
        "chargeable_weight_g": actual_weight_g,
        "additional_slabs": additional_slabs,
        "shipping_cost_minor": shipping_cost_minor,
        "currency": "INR",
        "transit_min_days": lane.get(
            "transit_min_days"
        ),
        "transit_max_days": lane.get(
            "transit_max_days"
        ),
        "provenance": lane.get(
            "provenance"
        ),
    }
def calculate_ems(
        lane:dict[str,Any],
        actual_weight_g:int,
        length_cm:Decimal,
        width_cm:Decimal,
        height_cm:Decimal,
)->dict[str,Any]:
    if actual_weight_g<=0:
        raise ShippingCalculationError(
            "Actual parcel weight must be greater than zero"
        )
    if(
        length_cm<=0
        or width_cm<=0
        or height_cm<=0
    ):
        raise ShippingCalculationError(
            "All parcel dimensions should be greater than zero"
        )
    if lane["lane"]!="EMS":
        raise ShippingCalculationError(
            f"Expected EMS lane,gpt {lane['lane']!r}"
        )
    divisor=lane.get("divisor")
    if divisor is None or divisor<=0:
        raise ShippingCalculationError(
            "EMS volumetric divisor is required"
        )
    volume_cm3=(
        length_cm
        *width_cm
        *height_cm
    )
    volumetric_weight_g=_ceil_decimal(
        (volume_cm3/Decimal(divisor))*Decimal(1000)
    )
    chargeable_weight_g=max(
        actual_weight_g,
        volumetric_weight_g
    )
    weight_cap_g=lane.get("weight_cap_g")
    if(
        weight_cap_g is not None and chargeable_weight_g> weight_cap_g):
        return{
            "lane": "EMS",
            "feasible": False,
            "reason": (
                f"Chargeable weight "
                f"{chargeable_weight_g}g exceeds "
                f"EMS weight cap of {weight_cap_g}g"
            ),
            "actual_weight_g": actual_weight_g,
            "volumetric_weight_g": volumetric_weight_g,
            "chargeable_weight_g": chargeable_weight_g,
            "shipping_cost_minor": None,
        }
    first_slab_g=lane["first_slab_g"]
    first_slab_rate_minor=lane["first_slab_rate_minor"]
    addl_slab_g=lane["addl_slab_g"]
    addl_slab_rate_minor=lane["addl_slab_rate_minor"]
    if first_slab_g<=0:
        raise ShippingCalculationError(
            "EMS first slab weight must be greater than zero"
        )
    if addl_slab_g<=0:
        raise ShippingCalculationError(
            "EMS additional slab weight must be greater than zero"
        )
    if chargeable_weight_g<=first_slab_g:
        additional_slabs=0
    else:
        remaining_weight=(
            chargeable_weight_g-first_slab_g
        )
        additional_slabs=_ceil_decimal(
            Decimal(remaining_weight)
            /Decimal(addl_slab_g)
        )
    shipping_cost_minor=(
        first_slab_rate_minor
        +(
            additional_slabs
            *addl_slab_rate_minor
        )
    )
    return{
        "lane": "EMS",
        "feasible": True,
        "actual_weight_g": actual_weight_g,
        "volumetric_weight_g": volumetric_weight_g,
        "chargeable_weight_g": chargeable_weight_g,
        "additional_slabs": additional_slabs,
        "shipping_cost_minor": shipping_cost_minor,
        "currency": "INR",
        "transit_min_days": lane.get(
            "transit_min_days"
        ),
        "transit_max_days": lane.get(
            "transit_max_days"
        ),
        "provenance": lane.get(
            "provenance"
        ),
    }
