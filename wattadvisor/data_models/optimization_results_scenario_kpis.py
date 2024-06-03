from typing import Optional

from pydantic import BaseModel, Field


class OptimizationResultsScenarioKpis(BaseModel):
    total_investment_cost: Optional[float]
    total_operational_cost: Optional[float]
    total_purchase_cost: Optional[float]
    total_income: Optional[float]
    total_annuities: float