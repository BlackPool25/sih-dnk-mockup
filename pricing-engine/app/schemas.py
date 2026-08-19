from decimal import Decimal
from enum import StrEnum
from typing import Annotated
from pydantic import BaseModel,ConfigDict,Field

class OptimizationMode(StrEnum):
    cheapest="CHEAPEST"
    fastest="FASTEST"
    balanced="BALANCED"
class DimensionsCm(BaseModel):
    model_config = ConfigDict(extra="forbid")

    length_cm: Annotated[Decimal, Field(gt=0)]
    width_cm: Annotated[Decimal, Field(gt=0)]
    height_cm: Annotated[Decimal, Field(gt=0)]
class MoneyAmount(BaseModel):
    model_config = ConfigDict(extra="forbid")

    amount_minor: Annotated[int, Field(ge=0)]
    currency: Annotated[str, Field(pattern=r"^[A-Z]{3}$")]
class PricingItem(BaseModel):
    model_config=ConfigDict(extra="forbid")

    item_id:Annotated[str,Field(min_length=1)]
    category_slug:Annotated[str,Field(min_length=1)]
    quantity:Annotated[int,Field(gt=0)]
    unit_weight_g:Annotated[int,Field(gt=0)]
    dimensions_cm:DimensionsCm
    unit_value:MoneyAmount
    splittable:bool=True
class PricingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    destination_country: Annotated[str, Field(pattern=r"^[A-Z]{2}$")]
    optimization_mode: OptimizationMode = OptimizationMode.cheapest
    items: Annotated[list[PricingItem], Field(min_length=1)]
