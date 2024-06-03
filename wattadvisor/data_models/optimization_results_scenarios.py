from typing import Optional

from pydantic import BaseModel, Field

from .optimization_results_scenario_object import OptimizationResultsScenarioObject


class OptimizationResultsScenarios(BaseModel):

    target_scenario: OptimizationResultsScenarioObject
    current_scenario: Optional[OptimizationResultsScenarioObject] = Field(default=None)