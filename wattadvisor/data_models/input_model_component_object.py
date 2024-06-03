from typing import Optional

from pydantic import BaseModel, Field

from ..data_models.enums import PowerUnitComponent, AreaUnitComponent, StorageComponent


class InputModelComponentPower(BaseModel):
    component_type: PowerUnitComponent
    installed_power: float = Field(ge=0)
    potential_power: Optional[float] = Field(ge=0, default=1e15)
    capex: Optional[float] = Field(ge=0)
    opex: Optional[float] = Field(ge=0)
    lifespan: Optional[float] = Field(ge=0)

class InputModelComponentArea(BaseModel):
    component_type: AreaUnitComponent
    installed_area: float = Field(ge=0)
    potential_area: Optional[float] = Field(ge=0, default=1e15)
    capex: Optional[float] = Field(ge=0)
    opex: Optional[float] = Field(ge=0)
    lifespan: Optional[float] = Field(ge=0)

class InputModelComponentStorage(BaseModel):
    component_type: StorageComponent
    installed_power: Optional[float] = Field(ge=0)
    potential_power: Optional[float] = Field(ge=0, default=1e15)
    installed_capacity: float = Field(ge=0)
    potential_capacity: Optional[float] = Field(ge=0, default=1e15)
    capex_capacity: Optional[float] = Field(ge=0)
    capex_power: Optional[float] = Field(ge=0)
    opex: Optional[float] = Field(ge=0)
    lifespan: Optional[float] = Field(ge=0)
