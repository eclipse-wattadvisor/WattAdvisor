"""Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

import pyomo.environ as pyoe

from .base import Component
import wattadvisor.data_models.enums as enums


class ElectricalEnergyStorage(Component):

    def __init__(self, 
                 name: str, 
                 interest_rate: float, 
                 parameters: dict, 
                 installed_capacity: float, 
                 installed_power: float | None = None, 
                 potential_capacity: float | None = None, 
                 potential_power: float | None = None, 
                 capex_power: float | None = None, 
                 capex_capacity: float | None = None, 
                 opex: float | None = None, 
                 lifespan: float | None = None):
        
        """Component where electrical power can be stored and later taken out again, due to
        efficiency some of the energy is lost.

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

        installed_capacity : float
            Already installed electrical storage capacity of the component [kWh] which acts as a lower bound
        installed_power : float | None, optional
            Already installed electrical power of the component [kW] which acts as a lower bound, by default None
        potential_capacity : float | None, optional
            Maximum installable electrical storage capacity of the component [kWh], by default None
        potential_power : float | None, optional
            Maximum installable electrical power of the component [kW], by default None
        capex_power : float | None, optional
            Capital expenditure cost part of the component per electrical power [€/kW], by default None
        capex_capacity : float | None, optional
            Capital expenditure cost part of the component per electrical energy storage [€/kWh], by default None
        opex : float | None, optional
            Operational expenditure cost of the component per CAPEX per year [%/a], by default None, by default None
        lifespan : float | None, optional
            Expected lifespan of the component [a], by default None
        """

        super().__init__(name, interest_rate, parameters)

        self.installed_power = installed_power
        self.potential_power = potential_power
        self.installed_capacity = installed_capacity
        self.potential_capacity = potential_capacity
        
        if capex_power is not None:
            self.capex_power = capex_power

        if capex_capacity is not None:
            self.capex_capacity = capex_capacity
        
        if opex is not None:
            self.opex = opex
        
        if lifespan is not None:
            self.lifespan = lifespan

    def _add_variables(self, model: pyoe.Model, t: pyoe.RangeSet) -> pyoe.Model:
        #(Input) charging energy [kW]
        self.chg=pyoe.Var(t, bounds=(0.0, None))
        model.add_component('{}_chg'.format(self.name), self.chg)

        #(Output) discharging energy [kW]
        self.dc=pyoe.Var(t, bounds=(0.0, None))
        model.add_component('{}_dc'.format(self.name), self.dc)

        # currently stored energy [kWh]
        self.storage=pyoe.Var(t, bounds=(0.0, None))
        model.add_component('{}_storage'.format(self.name), self.storage)

        # peak capacity [kWh], necessary to install capacity
        self.max_capacity=pyoe.Var(bounds=(self.installed_capacity, self.potential_capacity))
        model.add_component('{}_max_capacity'.format(self.name), self.max_capacity)

        # peak charging/discharging rate [kW], necessary power
        self.max_power=pyoe.Var(bounds=(self.installed_power, self.potential_power))
        model.add_component('{}_max_power'.format(self.name), self.max_power)

        # total cost, which is evaluated in the target function
        self.z=pyoe.Var(bounds=(0.0, None))
        model.add_component('{}_z'.format(self.name), self.z)

        # annual running cost
        self.running_cost=pyoe.Var(bounds=(0.0, None))
        model.add_component('{}_running_cost'.format(self.name), self.running_cost)

        # one-time installation cost
        self.installation_cost = pyoe.Var(bounds=(0.0, None))
        model.add_component('{}_installation_cost'.format(self.name), self.installation_cost)

        # charging/discharging balance; input - output
        self.balance=pyoe.Var(t)
        model.add_component('{}_balance'.format(self.name), self.balance)

        # losses of stored energy over time
        self.losses=pyoe.Var(t, bounds=(0.0, None))
        model.add_component('{}_losses'.format(self.name), self.losses)

        self.bilance_variables.input[enums.EnergyType.ELECTRICAL] = self.balance

        return model

    def _add_constraints(self, model: pyoe.Model, t: pyoe.RangeSet) -> pyoe.Model:

        # calculating total cost, depending on peak capacity and chg/dc rate
        self.eq01=pyoe.Constraint(expr=self.z == self.installation_cost * self.annuity_factor + self.running_cost)
        model.add_component('{}_eq01'.format(self.name), self.eq01)

        # calculating chg/dc balance
        self.eq02=pyoe.ConstraintList()
        model.add_component('{}_eq02'.format(self.name), self.eq02)
        for tx in t:
            self.eq02.add(self.balance[tx] == self.chg[tx] - self.dc[tx] * self.eff)

        # calculating the current amount of energy stored
        self.eq03=pyoe.ConstraintList()
        model.add_component('{}_eq03'.format(self.name), self.eq03)
        for tx in t:
            if tx == 1:
                self.eq03.add(self.storage[tx] == self.max_capacity)
            else:
                self.eq03.add(self.storage[tx] == self.storage[tx-1] + self.chg[tx] - self.dc[tx] - self.losses[tx])

        # set peak rate for charging and discharging to receive necessary to install power
        self.eq07=pyoe.ConstraintList()
        model.add_component('{}_eq07'.format(self.name), self.eq07)
        for tx in t:
            self.eq07.add(self.dc[tx] <= self.max_power)
        
        self.eq08=pyoe.ConstraintList()
        model.add_component('{}_eq08'.format(self.name), self.eq08)
        for tx in t:
            self.eq08.add(self.chg[tx] <= self.max_power)

        # restrict the size of the storage unit to get the necessary capacity to install
        self.eq09=pyoe.ConstraintList()
        model.add_component('{}_eq09'.format(self.name), self.eq09)
        for tx in t:
            self.eq09.add(self.storage[tx] <= self.max_capacity)

        #calculate the annual running cost
        self.eq10=pyoe.Constraint(expr=self.running_cost == self.installation_cost * self.opex/100)
        model.add_component('{}_eq10'.format(self.name), self.eq10)

        #calculate the one-time installation cost
        self.eq11=pyoe.Constraint(expr=self.installation_cost == self.max_capacity * self.capex_capacity + self.max_power * self.capex_power)
        model.add_component('{}_eq11'.format(self.name), self.eq11)
        
        # calculate the losses of stored energy over time
        self.eq12=pyoe.ConstraintList()
        model.add_component('{}_eq12'.format(self.name), self.eq12)
        for tx in t:
            if tx == 1:
                self.eq12.add(self.losses[tx] == 0)
            else:
                self.eq12.add(self.losses[tx] == self.relative_losses * self.storage[tx-1])

        return model