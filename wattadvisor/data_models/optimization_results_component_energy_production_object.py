"""Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

from pydantic import BaseModel

from .enums import EnergyType


class OptimizationResultsComponentEnergyProductionObject(BaseModel):
    energy_type: EnergyType
    amount: float