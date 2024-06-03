"""Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

from typing import Union

from pydantic import BaseModel, Field

from .optimization_results_component_object import (
    OptimizationResultsComponentObjectPower, OptimizationResultsComponentObjectPurchaseFeedin,
    OptimizationResultsComponentObjectArea, OptimizationResultsComponentObjectStorage)
from .optimization_results_scenario_kpis import OptimizationResultsScenarioKpis


class OptimizationResultsScenarioObject(BaseModel):
    components: list[Union[OptimizationResultsComponentObjectPower, OptimizationResultsComponentObjectPurchaseFeedin, OptimizationResultsComponentObjectArea, OptimizationResultsComponentObjectStorage]] = Field(min_items=1)
    kpis: OptimizationResultsScenarioKpis