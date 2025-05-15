"""Definition of the returned response body containing optimization results

Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

from pydantic import Field

from ..data_models.base_model import BaseModelCustom
from .optimization_results_status import OptimizationResultsStatus
from .optimization_results_scenario import OptimizationResultsScenario


class OptimizationResults(BaseModelCustom):
    status: OptimizationResultsStatus
    current_scenario: None | OptimizationResultsScenario = Field(default=None)
    target_scenario: None | OptimizationResultsScenario = Field(default=None)