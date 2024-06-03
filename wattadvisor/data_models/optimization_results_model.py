"""Definition of the returned response body containing optimization results

Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

from typing import Optional

from pydantic import BaseModel, Field

from .optimization_results_status import OptimizationResultsStatus
from .optimization_results_scenarios import OptimizationResultsScenarios
from .input_model import InputModel


class OptimizationResultsModel(BaseModel):
    status: OptimizationResultsStatus
    requested_input: InputModel
    results: Optional[OptimizationResultsScenarios] = Field(default=None)