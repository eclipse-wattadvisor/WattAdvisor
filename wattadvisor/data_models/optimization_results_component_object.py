"""Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

from typing import List, Union, Optional

from pydantic import BaseModel, Field

from .enums import PowerUnitComponent, StorageComponent, AreaUnitComponent, FeedinComponent, PurchaseComponent
from .optimization_results_component_energy_production_object import OptimizationResultsComponentEnergyProductionObject


class OptimizationResultsComponentObjectPower(BaseModel):
    component_type: PowerUnitComponent
    installed_power: float = Field(ge=0)
    investment_cost: float = Field(ge=0)
    operational_cost: float = Field(ge=0)
    annuity: float = Field(ge=0)
    produced_energy:  Optional[List[OptimizationResultsComponentEnergyProductionObject]] = Field(max_items=2)

class OptimizationResultsComponentObjectPurchaseFeedin(BaseModel):
    component_type: Union[PurchaseComponent, FeedinComponent]
    purchase_cost: float
    annuity: float
    produced_energy: Optional[List[OptimizationResultsComponentEnergyProductionObject]] = Field(max_items=1)

class OptimizationResultsComponentObjectArea(BaseModel):
    component_type: AreaUnitComponent
    installed_power: float = Field(ge=0)
    investment_cost: float = Field(ge=0)
    operational_cost: float = Field(ge=0)
    annuity: float = Field(ge=0)
    produced_energy:  Optional[List[OptimizationResultsComponentEnergyProductionObject]] = Field(max_items=1)

class OptimizationResultsComponentObjectStorage(BaseModel):
    component_type: StorageComponent
    installed_power: float = Field(ge=0)
    installed_capacity: float = Field(ge=0)
    investment_cost: float = Field(ge=0)
    operational_cost: float = Field(ge=0)
    annuity: float = Field(ge=0)