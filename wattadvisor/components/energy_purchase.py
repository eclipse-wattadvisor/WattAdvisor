"""Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

import pyomo.environ as pyoe
from pyomo.core.util import sum_product
import pandas as pd
from pydantic import Field, field_validator

from .non_investment_component import NonInvestmentComponent
import wattadvisor.data_models.enums as enums


class EnergyPurchase(NonInvestmentComponent):
    """Component that simulates the import and obtaining of energy from external sources 
        in different forms like gas, oil, electricity or heat.
        This component imports energy and applies a cost for the amount imported.

        Parameters
        ----------
        energy_price_scalar : float | None, optional
            Scalar price for purchasement per energy unit [€/kWh], by default None
        energy_price_profile : pd.Series | None, optional
            Time series containing hourly variant energy prices for one year, by default None
        power_price : float, optional
            Price to pay for maximum grid load per year [€/(kW * a)], by default 0
        co2_intensity : float, optional
            CO2 emission intensity of the energy purchase [g/kWh], by default 0
    """
    
    energy_price_scalar: float | None = None
    energy_price_profile: pd.Series | None = Field(default=None, exclude=True)
    power_price: float = Field(default=0)
    co2_intensity: float = Field(default=0)

    def __init__(self, **data):
        super().__init__(**data)

        if self.energy_price_profile is None:
            if self.energy_price_scalar is None:
                self.energy_price_scalar = 0
    
    @field_validator('energy_price_profile')
    @classmethod
    def check_time_series_length(cls, value: pd.Series | None) -> pd.Series | None:
        if value is not None and len(value) != 8760:
            raise ValueError("Covered time span by weather data is not 8760 hours.")
        
        return value

    def _load_params(self, model: pyoe.Model, t: pyoe.RangeSet) -> pyoe.Model:
        if self.energy_price_profile is None:
            self._energy_price_dict = {tx: self.energy_price_scalar for tx in t}
        else:
            self._energy_price_dict = self.energy_price_profile.set_axis(t).to_dict()

        self._power_price = pyoe.Param(initialize=self.power_price)
        model.add_component(f'{self.name}_power_price', self._power_price)

        self._energy_price_profile = pyoe.Param(t, initialize=self._energy_price_dict)
        model.add_component(f'{self.name}_energy_price_profile', self._energy_price_profile)

        return model

    def _add_variables(self, model: pyoe.Model, t: pyoe.RangeSet) -> pyoe.Model:

        #(Output) obtained electrical energy [kW]
        self._output=pyoe.Var(t, bounds=(0.0, None))
        model.add_component('{}_output'.format(self.name), self._output)

        # peak power [kW] purchased
        self._max_power=pyoe.Var(bounds=(0.0, None))
        model.add_component('{}_max_power'.format(self.name), self._max_power)

        # calculated cost [€], without regard to the optimization criteria
        self._purchase_cost=pyoe.Var()
        model.add_component('{}_purchase_cost'.format(self.name), self._purchase_cost)

        # calculated amount of co2 emissions [grams]
        self._co2_emissions=pyoe.Var(t, bounds=(0.0, None))
        model.add_component('{}_co2_emissions'.format(self.name), self._co2_emissions)

        # total cost, which is evaluated in the target function
        self._annuity=pyoe.Var()
        model.add_component('{}_annuity'.format(self.name), self._annuity)

        self.bilance_variables.output[self.energy_type] = self._output

        return model

    def _add_constraints(self, model: pyoe.Model, t: pyoe.RangeSet) -> pyoe.Model:

        # calculating the total cost by applying the price to the imported electricity
        self._eq01=pyoe.Constraint(expr=self._annuity == self._purchase_cost)
        model.add_component('{}_eq01'.format(self.name),self._eq01)

        self._eq02=pyoe.Constraint(expr=self._purchase_cost == sum_product(self._output, self._energy_price_profile, index=t) + self._max_power * self._power_price)
        model.add_component('{}_eq02'.format(self.name), self._eq02)
        
        self._eq03=pyoe.ConstraintList()
        model.add_component('{}_eq03'.format(self.name), self._eq03)
        for tx in t:
            self._eq03.add(self._co2_emissions[tx] == self._output[tx] * self.co2_intensity)

        # calculate peak power
        self._eq04=pyoe.ConstraintList()
        model.add_component('{}_eq04'.format(self.name), self._eq04)
        for tx in t:
            self._eq04.add(self._output[tx] <= self._max_power)

        return model