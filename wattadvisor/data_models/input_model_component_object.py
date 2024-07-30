"""Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""


from typing import Optional

from pydantic import BaseModel, Field

from ..data_models.enums import PowerUnitComponent, AreaUnitComponent, StorageComponent
from .input_model_component_normed_production_object import NormedProduction

class InputModelComponentPower(BaseModel):
    component_type: PowerUnitComponent
    installed_power: float = Field(ge=0)
    potential_power: Optional[float] = Field(ge=0, default=1e15)
    capex: Optional[float] = Field(ge=0)
    opex: Optional[float] = Field(ge=0)
    lifespan: Optional[float] = Field(ge=0)
    normed_production: Optional[NormedProduction]

class InputModelComponentArea(BaseModel):
    component_type: AreaUnitComponent
    installed_area: float = Field(ge=0)
    potential_area: Optional[float] = Field(ge=0, default=1e15)
    capex: Optional[float] = Field(ge=0)
    opex: Optional[float] = Field(ge=0)
    lifespan: Optional[float] = Field(ge=0)
    normed_production: Optional[NormedProduction]

class InputModelComponentStorage(BaseModel):
    component_type: StorageComponent
    installed_power: Optional[float] = Field(ge=0)
    potential_power: Optional[float] = Field(ge=0, default=1e15)
    installed_capacity: float = Field(ge=0)
    potential_capacity: Optional[float] = Field(ge=0, default=1e15)
    capex_capacity: Optional[float] = Field(ge=0)
    capex_power: Optional[float] = Field(ge=0)
    opex: Optional[float] = Field(ge=0)
    lifespan: Optional[float] = Field(ge=0)
