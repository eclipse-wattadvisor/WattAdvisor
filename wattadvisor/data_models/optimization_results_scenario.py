"""Contains the definition of a pydantic model
representing the results of a single optimization scenario.

Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

from pydantic import Field

from ..data_models.base_model import BaseModelCustom
from .optimization_results_scenario_kpis import OptimizationResultsScenarioKpis


class OptimizationResultsScenario(BaseModelCustom):
    components: list[dict] = Field(min_length=1)
    kpis: OptimizationResultsScenarioKpis