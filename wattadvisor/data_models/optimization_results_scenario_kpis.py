"""Contains the definition of a pydantic model
representing the total KPIs of a single optimization scenario.

Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

from ..data_models.base_model import BaseModelCustom


class OptimizationResultsScenarioKpis(BaseModelCustom):
    total_co2_emissions: None | float
    total_investment_cost: None | float
    total_operational_cost: None | float
    total_purchase_cost: None | float
    total_income: None | float
    total_annuities: float
