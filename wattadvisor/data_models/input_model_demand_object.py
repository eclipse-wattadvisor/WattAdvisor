from pydantic import BaseModel, Field, confloat

from .enums import EnergyType, Resolution, EnergyUnit


class InputModelDemandObject(BaseModel):
    demand_values: list[confloat(ge=0)] = Field(min_items=1)
    resolution: Resolution
    unit: EnergyUnit
    energy_type : EnergyType