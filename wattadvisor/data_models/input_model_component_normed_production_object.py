"""Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""


from typing import Optional

from pydantic import BaseModel, Field, confloat

from ..data_models.enums import EnergyType, Resolution, EnergyUnit

class NormedProduction(BaseModel):
    production_values: list[confloat(ge=0)] = Field(min_items=1)
    resolution: Resolution
    unit: EnergyUnit