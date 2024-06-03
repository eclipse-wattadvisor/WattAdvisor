from pydantic import BaseModel

from .enums import EnergyType


class OptimizationResultsComponentEnergyProductionObject(BaseModel):
    energy_type: EnergyType
    amount: float