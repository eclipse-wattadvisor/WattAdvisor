"""Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

from pydantic import BaseModel, Field, confloat

from .enums import EnergyType, Resolution, EnergyUnit


class InputModelDemandObject(BaseModel):
    demand_values: list[confloat(ge=0)] = Field(min_items=1)
    resolution: Resolution
    unit: EnergyUnit
    energy_type : EnergyType