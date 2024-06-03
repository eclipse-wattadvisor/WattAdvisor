"""Definition of the accepted input request body

"""

from typing import Union, Optional

from pydantic import BaseModel, Field

from .input_model_component_object import InputModelComponentPower, InputModelComponentArea, InputModelComponentStorage
from .input_model_demand_object import InputModelDemandObject
from .input_model_energy_tariffs import InputModelEnergyTariffs
from .input_model_location import InputModelLocation


class InputModel(BaseModel):
    location: InputModelLocation = Field()
    interest_rate: Optional[float] = Field(gt=0, lt=1)
    energy_demands: list[InputModelDemandObject] = Field(min_items=1)
    energy_components: Optional[list[Union[InputModelComponentPower, InputModelComponentArea, InputModelComponentStorage]]]
    energy_tariffs: Optional[InputModelEnergyTariffs]