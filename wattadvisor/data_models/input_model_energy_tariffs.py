from typing import Optional

from pydantic import BaseModel, Field

from .input_model_single_tariff_object import InputModelSingleTariffObject
from .input_model_single_tariff_energy_object import InputModelSingleTariffEnergyObject
from .enums import EnergyPriceUnit, Resolution


class InputModelEnergyTariffs(BaseModel):
    electrical_energy_purchase: Optional[InputModelSingleTariffObject]

    electrical_energy_feedin: InputModelSingleTariffObject = Field(
        default=InputModelSingleTariffObject(
            energy=InputModelSingleTariffEnergyObject(
                price_values=[0],
                resolution=Resolution.R1Y,
                unit=EnergyPriceUnit.EUR_PER_KWH),
            power=None))

    thermal_energy_purchase: Optional[InputModelSingleTariffObject]
    natural_gas_purchase: Optional[InputModelSingleTariffObject]