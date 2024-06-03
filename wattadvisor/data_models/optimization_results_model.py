"""Definition of the returned response body containing optimization results

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