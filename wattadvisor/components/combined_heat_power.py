"""Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

import pyomo.environ as pyoe
from pydantic import Field

from .investment_component import InvestmentComponent
from ..data_models.enums import EnergyType


class CombinedHeatPower(InvestmentComponent):
    """Component to turn an energy carrying medium like gas into electric and thermal power.
        2 different kinds of capacities have to be implemented for this, but since the
        production of electric power takes precedent the cost in the target function depends
        only on that

        Parameters
        ----------
        capex : float, optional
            Capital expenditure cost of the component per electrical power [€/kW], by default 0
        opex : float, optional
            Operational expenditure cost of the component per CAPEX per year [%/a], by default 0
        eff_elt : float
            electrical efficiency of the plant [kW electricity per kW gas] 
        eff_heat : float
            thermal efficiency of the plant [kW heat per kW gas] 
        installed_power : float, optional
            Already installed electrical power of the component [kW] which acts as a lower bound, by default 0
        potential_power : float | None, optional
            Maximum installable electrical power of the component [kW], by default None

    """

    capex: float = Field(ge=0, default=0)
    opex: float = Field(ge=0, default=0)
    eff_elt: float = Field(ge=0)
    eff_heat: float = Field(ge=0)
    installed_power: float = Field(ge=0, default=0)
    potential_power: float | None = Field(ge=0, default=None)

    def _add_variables(self, model: pyoe.Model, t: pyoe.RangeSet) -> pyoe.Model:

        #(Output) electrical power [kW]
        self._output_electrical=pyoe.Var(t, bounds=(0.0, None))
        model.add_component('{}_output_electrical'.format(self.name), self._output_electrical)

        # peak electrical power [kWp]
        self._advised_power=pyoe.Var(bounds=(self.installed_power, self.potential_power))
        model.add_component('{}_advised_power'.format(self.name), self._advised_power)

        #(Output) thermal power [kW]
        self._output_thermal=pyoe.Var(t, bounds=(0.0, None))
        model.add_component('{}_output_thermal'.format(self.name), self._output_thermal)

        # peak thermal power [kWp]
        self._maxhp=pyoe.Var(bounds=(0.0, None))
        model.add_component('{}_maxhp'.format(self.name), self._maxhp)

        #(Input) Energy in form of gas [kW]
        self._input_gas=pyoe.Var(t, bounds=(0.0, None))
        model.add_component('{}_input_gas'.format(self.name), self._input_gas)

        # total cost, which is evaluated in the target function
        self._annuity=pyoe.Var(bounds=(0.0, None))
        model.add_component('{}_annuity'.format(self.name), self._annuity)

        # annual running cost
        self._operational_cost=pyoe.Var(bounds=(0.0, None))
        model.add_component('{}_operational_cost'.format(self.name), self._operational_cost)

        # one-time installation cost
        self._investment_cost = pyoe.Var(bounds=(0.0, None))
        model.add_component('{}_investment_cost'.format(self.name), self._investment_cost)

        self.bilance_variables.output[EnergyType.ELECTRICAL] = self._output_electrical
        self.bilance_variables.output[EnergyType.THERMAL] = self._output_thermal
        self.bilance_variables.input[EnergyType.NATURAL_GAS] = self._input_gas

        return model

    def _add_constraints(self, model: pyoe.Model, t: pyoe.RangeSet) -> pyoe.Model:
        # calculating total cost, depends on peak(installed) electrical power
        self._eq01=pyoe.Constraint(expr=self._annuity == self._investment_cost * self.annuity_factor + self._operational_cost)
        model.add_component('{}_eq01'.format(self.name), self._eq01)

        # calculating electrical output
        self._eq02=pyoe.ConstraintList()
        model.add_component('{}_eq02'.format(self.name), self._eq02)
        for tx in t:
            self._eq02.add(self._output_electrical[tx] == self._input_gas[tx] * self.eff_elt)
        
        # calculating thermal output
        self._eq03=pyoe.ConstraintList()
        model.add_component('{}_eq03'.format(self.name), self._eq03)
        for tx in t:
            self._eq03.add(self._output_thermal[tx] == self._input_gas[tx] * self.eff_heat)

        # restraining electrical output / calculating necessary installed electrical power
        self._eq04=pyoe.ConstraintList()
        model.add_component('{}_eq04'.format(self.name), self._eq04)
        for tx in t:
            self._eq04.add(self._output_electrical[tx] <= self._advised_power)

        # restraining thermal output / calculating necessary installed thermal power
        self._eq05=pyoe.ConstraintList()
        model.add_component('{}_eq05'.format(self.name), self._eq05)
        for tx in t:
            self._eq05.add(self._output_thermal[tx]<= self._maxhp)

        # calculate annual running cost
        self._eq06=pyoe.Constraint(expr=self._operational_cost == self._investment_cost * self.opex/100)
        model.add_component('{}_eq06'.format(self.name), self._eq06)

        # calculate one-time installation cost
        self._eq07=pyoe.Constraint(expr=self._investment_cost == self._advised_power * self.capex)
        model.add_component('{}_eq07'.format(self.name), self._eq07)

        return model