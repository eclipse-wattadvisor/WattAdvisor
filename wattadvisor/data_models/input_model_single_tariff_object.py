from typing import Optional

from pydantic import BaseModel

from .input_model_single_tariff_energy_object import InputModelSingleTariffEnergyObject


class InputModelSingleTariffObject(BaseModel):
    energy: InputModelSingleTariffEnergyObject
    power: Optional[float]