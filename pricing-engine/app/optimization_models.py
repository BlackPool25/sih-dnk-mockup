from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class OptimizationItem:
    item_id: str
    quantity: int
    unit_weight_g: int
    splittable: bool

    length_cm: Decimal
    width_cm: Decimal
    height_cm: Decimal


@dataclass(frozen=True)
class LaneOption:
    name: str
    lane_data: dict[str, Any]