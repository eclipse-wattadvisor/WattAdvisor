from typing import List

from pydantic import BaseModel, Field

from .enums import EnergyPriceUnit, Resolution


class InputModelSingleTariffEnergyObject(BaseModel):
    price_values: List[float] = Field(min_items=1)
    resolution: Resolution
    unit: EnergyPriceUnit