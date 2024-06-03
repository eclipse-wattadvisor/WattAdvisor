"""Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

from typing import Optional

from pydantic import BaseModel

from .input_model_single_tariff_energy_object import InputModelSingleTariffEnergyObject


class InputModelSingleTariffObject(BaseModel):
    energy: InputModelSingleTariffEnergyObject
    power: Optional[float]