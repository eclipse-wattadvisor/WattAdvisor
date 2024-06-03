"""Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

from typing import List

from pydantic import BaseModel, Field

from .enums import EnergyPriceUnit, Resolution


class InputModelSingleTariffEnergyObject(BaseModel):
    price_values: List[float] = Field(min_items=1)
    resolution: Resolution
    unit: EnergyPriceUnit