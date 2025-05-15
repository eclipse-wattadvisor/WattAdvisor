"""Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

import pyomo.environ as pyoe
from pydantic import Field

from .investment_component import InvestmentComponent
from ..data_models.enums import EnergyType


class SolidFuelBoiler(InvestmentComponent):
    """Component to turn an energy carrying medium like gas into thermal power.

        Parameters
        ----------
        capex : float, optional
            Capital expenditure cost of the component per thermal power [€/kW], by default 0
        opex : float, optional
            Operational expenditure cost of the component per CAPEX per year [%/a], by default 0
        installed_power : float, optional
            Already installed thermal power of the component [kW] which acts as a lower bound, by default 0
        potential_power : float | None, optional
            Maximum installable thermal power of the component [kW], by default None
        eff : float
            Thermal efficiency of the boiler [-]
    """

    capex: float = Field(ge=0, default=0)
    opex: float = Field(ge=0, default=0)
    installed_power: float = Field(ge=0, default=0)
    potential_power: float | None = Field(ge=0, default=None)
    eff: float = Field(ge=0)

    def _add_variables(self, model: pyoe.Model, t: pyoe.RangeSet) -> pyoe.Model:

        #(Output) thermal power [kW]
        self._output_thermal=pyoe.Var(t, bounds=(0.0, None))
        model.add_component('{}_output_thermal'.format(self.name), self._output_thermal)

        #(Input) gas consumption [kW]
        self._input_solid_fuel=pyoe.Var(t, bounds=(0.0, None))
        model.add_component('{}_input_solid_fuel'.format(self.name), self._input_solid_fuel)

        # total cost, which is evaluated in the target function
        self._annuity=pyoe.Var(bounds=(0.0, None))
        model.add_component('{}_annuity'.format(self.name), self._annuity)

        # annual running cost
        self._operational_cost=pyoe.Var(bounds=(0.0, None))
        model.add_component('{}_operational_cost'.format(self.name), self._operational_cost)

        # one-time installation cost
        self._investment_cost = pyoe.Var(bounds=(0.0, None))
        model.add_component('{}_investment_cost'.format(self.name), self._investment_cost)

        # peak power [kWp], necessary to install
        self._advised_power=pyoe.Var(bounds=(self.installed_power, self.potential_power))
        model.add_component('{}_advised_power'.format(self.name), self._advised_power)

        self.bilance_variables.input[EnergyType.SOLID_FUEL] = self._input_solid_fuel
        self.bilance_variables.output[EnergyType.THERMAL] = self._output_thermal

        return model

    def _add_constraints(self, model: pyoe.Model, t: pyoe.RangeSet) -> pyoe.Model:

        # calculating total cost, depending on peak power
        self._eq01=pyoe.Constraint(expr=self._annuity == self._investment_cost * self.annuity_factor + self._operational_cost)
        model.add_component('{}_eq01'.format(self.name), self._eq01)

        # calculating thermal power, by applying efficiency to gas input
        self._eq02=pyoe.ConstraintList()
        model.add_component('{}_eq02'.format(self.name), self._eq02)
        for tx in t:
            self._eq02.add(self._input_solid_fuel[tx] * self.eff == self._output_thermal[tx])

        # setting peak power
        self._eq03=pyoe.ConstraintList()
        model.add_component('{}_eq03'.format(self.name), self._eq03)
        for tx in t:
            self._eq03.add(self._output_thermal[tx] <= self._advised_power)

        #calculate the annual running cost
        self._eq04=pyoe.Constraint(expr=self._operational_cost == self._investment_cost * self.opex/100)
        model.add_component('{}_eq04'.format(self.name), self._eq04)

        #calculate the one-time installation cost
        self._eq05=pyoe.Constraint(expr=self._investment_cost == self._advised_power * self.capex)
        model.add_component('{}_eq05'.format(self.name), self._eq05)

        return model