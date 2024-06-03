"""Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

from typing import Optional

from pydantic import BaseModel


class OptimizationResultsScenarioKpis(BaseModel):
    total_investment_cost: Optional[float]
    total_operational_cost: Optional[float]
    total_purchase_cost: Optional[float]
    total_income: Optional[float]
    total_annuities: float