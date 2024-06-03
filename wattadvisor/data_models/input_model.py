"""Definition of the accepted input request body

Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
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