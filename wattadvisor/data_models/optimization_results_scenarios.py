"""Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

from typing import Optional

from pydantic import BaseModel, Field

from .optimization_results_scenario_object import OptimizationResultsScenarioObject


class OptimizationResultsScenarios(BaseModel):

    target_scenario: OptimizationResultsScenarioObject
    current_scenario: Optional[OptimizationResultsScenarioObject] = Field(default=None)