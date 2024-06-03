"""Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

import pyomo.environ as pyoe

from .base import Component
import wattadvisor.data_models.enums as enums


class CombinedHeatPower(Component):

    def __init__(self, 
                 name: str, 
                 interest_rate: float, 
                 parameters: dict, 
                 installed_power: float, 
                 potential_power: float | None = None, 
                 capex: float | None = None, 
                 opex: float | None = None, 
                 lifespan: float | None = None):
        
        """Component to turn an energy carrying medium like gas into electric and thermal power.
        2 different kinds of capacities have to be implemented for this, but since the
        production of electric power takes precedent the cost in the target function depends
        only on that

        Parameters
        ----------
        name : str
            Name of the component
        interest_rate : float
            Interest rate to determine annuity factor for investment calculation of the component, by default None 
        parameters : dict
            Dictionary of techno-economic parameters of the component, by default None.
            A dict of the following structure is expeceted. 
            At least one key at first level ("scalars" or "tabs") is required:

            .. code-block:: json

                {
                    "scalars": {
                        "parameter_title": 0
                    },
                    "tabs": {
                        "tab_title": {
                            "key_1": 1,
                            "key_2": 2
                        }
                    }
                }

        installed_power : float
            Already installed electrical power of the component [kW] which acts as a lower bound
        potential_power : float | None, optional
            Maximum installable electrical power of the component [kW], by default None
        capex : float | None, optional
            Capital expenditure cost of the component per electrical power [€/kW], by default None
        opex : float | None, optional
            Operational expenditure cost of the component per CAPEX per year [%/a], by default None
        lifespan : float | None, optional
            Expected lifespan of the component [a], by default None
        """

        super().__init__(name, interest_rate, parameters)

        self.installed_power = installed_power
        self.potential_power = potential_power
        
        if capex is not None:
            self.capex = capex
        
        if opex is not None:
            self.opex = opex
        
        if lifespan is not None:
            self.lifespan = lifespan

    def _add_variables(self, model: pyoe.Model, t: pyoe.RangeSet) -> pyoe.Model:

        #(Output) electrical power [kW]
        self.produced_electrical=pyoe.Var(t, bounds=(0.0, None))
        model.add_component('{}_produced_electrical'.format(self.name), self.produced_electrical)

        # peak electrical power [kWp]
        self.max_power=pyoe.Var(bounds=(self.installed_power, self.potential_power))
        model.add_component('{}_max_power'.format(self.name), self.max_power)

        #(Output) thermal power [kW]
        self.produced_thermal=pyoe.Var(t, bounds=(0.0, None))
        model.add_component('{}_produced_thermal'.format(self.name), self.produced_thermal)

        # peak thermal power [kWp]
        self.maxhp=pyoe.Var(bounds=(0.0, None))
        model.add_component('{}_maxhp'.format(self.name), self.maxhp)

        #(Input) Energy in form of gas [kW]
        self.gas=pyoe.Var(t, bounds=(0.0, None))
        model.add_component('{}_gas'.format(self.name), self.gas)

        # total cost, which is evaluated in the target function
        self.z=pyoe.Var(bounds=(0.0, None))
        model.add_component('{}_z'.format(self.name), self.z)

        # annual running cost
        self.running_cost=pyoe.Var(bounds=(0.0, None))
        model.add_component('{}_running_cost'.format(self.name), self.running_cost)

        # one-time installation cost
        self.installation_cost = pyoe.Var(bounds=(0.0, None))
        model.add_component('{}_installation_cost'.format(self.name), self.installation_cost)

        self.bilance_variables.output[enums.EnergyType.ELECTRICAL] = self.produced_electrical
        self.bilance_variables.output[enums.EnergyType.THERMAL] = self.produced_thermal
        self.bilance_variables.input[enums.EnergyType.NATURAL_GAS] = self.gas

        return model

    def _add_constraints(self, model: pyoe.Model, t: pyoe.RangeSet) -> pyoe.Model:
        # calculating total cost, depends on peak(installed) electrical power
        self.eq01=pyoe.Constraint(expr=self.z == self.installation_cost * self.annuity_factor + self.running_cost)
        model.add_component('{}_eq01'.format(self.name), self.eq01)

        # calculating electrical output
        self.eq02=pyoe.ConstraintList()
        model.add_component('{}_eq02'.format(self.name), self.eq02)
        for tx in t:
            self.eq02.add(self.produced_electrical[tx] == self.gas[tx] * self.effelt)
        
        # calculating thermal output
        self.eq03=pyoe.ConstraintList()
        model.add_component('{}_eq03'.format(self.name), self.eq03)
        for tx in t:
            self.eq03.add(self.produced_thermal[tx] == self.gas[tx] * self.effheat)

        # restraining electrical output / calculating necessary installed electrical power
        self.eq04=pyoe.ConstraintList()
        model.add_component('{}_eq04'.format(self.name), self.eq04)
        for tx in t:
            self.eq04.add(self.produced_electrical[tx] <= self.max_power)

        # restraining thermal output / calculating necessary installed thermal power
        self.eq05=pyoe.ConstraintList()
        model.add_component('{}_eq05'.format(self.name), self.eq05)
        for tx in t:
            self.eq05.add(self.produced_thermal[tx]<= self.maxhp)

        # calculate annual running cost
        self.eq06=pyoe.Constraint(expr=self.running_cost == self.installation_cost * self.opex/100)
        model.add_component('{}_eq06'.format(self.name), self.eq06)

        # calculate one-time installation cost
        self.eq07=pyoe.Constraint(expr=self.installation_cost == self.max_power * self.capex)
        model.add_component('{}_eq07'.format(self.name), self.eq07)

        return model