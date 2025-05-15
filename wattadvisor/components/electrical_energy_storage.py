"""Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

import pyomo.environ as pyoe
from pydantic import Field

from .investment_component import InvestmentComponent
from ..data_models.enums import EnergyType


class ElectricalEnergyStorage(InvestmentComponent):
    """Component where electrical power can be stored and later taken out again, due to
    efficiency a part of the energy is lost.

    Parameters
    ----------
    installed_capacity : float, optional
        Already installed thermal storage capacity of the component [kWh] which acts as a lower bound, by default 0
    installed_power : float, optional
        Already installed thermal power of the component [kW] which acts as a lower bound, by default 0
    potential_capacity : float | None, optional
        Maximum installable thermal storage capacity of the component [kWh], by default None
    potential_power : float | None, optional
        Maximum installable thermal power of the component [kW], by default None
    capex_power : float, optional
        Capital expenditure cost part of the component per thermal power [€/kW], by default 1e-5
    capex_capacity : float, optional
        Capital expenditure cost part of the component per thermal energy storage [€/kWh], by default 0
    initial_soc : float, optional
        SOC of the storage [%]  at first timestep of the optimization, by default 0%
    opex : float | None, optional
        Operational expenditure cost of the component per CAPEX per year [%/a], by default None, by default None
    eff : float
        Storage efficiency [-]
    relative_losses : float
        Losses of stored energy over time [% of the stored energy per hour]
    """

    installed_capacity: float = Field(ge=0, default=0)
    installed_power: float = Field(ge=0, default=0)
    potential_capacity: float | None = Field(ge=0, default=None)
    potential_power: float | None = Field(ge=0, default=None)
    capex_power: float = Field(ge=0, default=1e-5)
    capex_capacity: float = Field(ge=0, default=0)
    initial_soc: float = Field(ge=0, le=1, default=0)
    opex: float = Field(ge=0, default=0)
    eff: float = Field(ge=0)
    relative_losses: float = Field(ge=0)

    def _add_variables(self, model: pyoe.Model, t: pyoe.RangeSet) -> pyoe.Model:
        # (Input) charging energy [kW]
        self._chg = pyoe.Var(t, bounds=(0.0, None))
        model.add_component("{}_chg".format(self.name), self._chg)

        # (Output) discharging energy [kW]
        self._dc = pyoe.Var(t, bounds=(0.0, None))
        model.add_component("{}_dc".format(self.name), self._dc)

        # currently stored energy [kWh]
        self._storage = pyoe.Var(t, bounds=(0.0, None))
        model.add_component("{}_storage".format(self.name), self._storage)

        # peak capacity [kWh], necessary to install capacity
        self._advised_capacity = pyoe.Var(
            bounds=(self.installed_capacity, self.potential_capacity)
        )
        model.add_component(
            "{}_advised_capacity".format(self.name), self._advised_capacity
        )

        # peak charging/discharging rate [kW], necessary power
        self._advised_power = pyoe.Var(
            bounds=(self.installed_power, self.potential_power)
        )
        model.add_component("{}_advised_power".format(self.name), self._advised_power)

        # total cost, which is evaluated in the target function
        self._annuity = pyoe.Var(bounds=(0.0, None))
        model.add_component("{}_annuity".format(self.name), self._annuity)

        # annual running cost
        self._operational_cost = pyoe.Var(bounds=(0.0, None))
        model.add_component(
            "{}_operational_cost".format(self.name), self._operational_cost
        )

        # one-time installation cost
        self._investment_cost = pyoe.Var(bounds=(0.0, None))
        model.add_component(
            "{}_investment_cost".format(self.name), self._investment_cost
        )

        # charging/discharging balance; input - output
        self._input_electrical = pyoe.Var(t)
        model.add_component(
            "{}_input_electrical".format(self.name), self._input_electrical
        )

        # losses of stored energy over time
        self._losses = pyoe.Var(t, bounds=(0.0, None))
        model.add_component("{}_losses".format(self.name), self._losses)

        self.bilance_variables.input[EnergyType.ELECTRICAL] = self._input_electrical

        return model

    def _add_constraints(self, model: pyoe.Model, t: pyoe.RangeSet) -> pyoe.Model:

        # calculating total cost, depending on peak capacity and chg/dc rate
        self._eq01 = pyoe.Constraint(
            expr=self._annuity
            == self._investment_cost * self.annuity_factor + self._operational_cost
        )
        model.add_component("{}_eq01".format(self.name), self._eq01)

        # calculating chg/dc balance
        self._eq02 = pyoe.ConstraintList()
        model.add_component("{}_eq02".format(self.name), self._eq02)
        for tx in t:
            self._eq02.add(
                self._input_electrical[tx] == self._chg[tx] - self._dc[tx] * self.eff
            )

        # calculating the current amount of energy stored
        self._eq03 = pyoe.ConstraintList()
        model.add_component("{}_eq03".format(self.name), self._eq03)
        for tx in t:
            if tx == 1:
                self._eq03.add(
                    self._storage[tx]
                    == self._advised_capacity * self.initial_soc
                    + self._chg[tx]
                    - self._dc[tx]
                    - self._losses[tx]
                )
            else:
                self._eq03.add(
                    self._storage[tx]
                    == self._storage[tx - 1]
                    + self._chg[tx]
                    - self._dc[tx]
                    - self._losses[tx]
                )

        # set peak rate for charging and discharging to receive necessary to install power
        self._eq07 = pyoe.ConstraintList()
        model.add_component("{}_eq07".format(self.name), self._eq07)
        for tx in t:
            self._eq07.add(self._dc[tx] <= self._advised_power)

        self._eq08 = pyoe.ConstraintList()
        model.add_component("{}_eq08".format(self.name), self._eq08)
        for tx in t:
            self._eq08.add(self._chg[tx] <= self._advised_power)

        # restrict the size of the storage unit to get the necessary capacity to install
        self._eq09 = pyoe.ConstraintList()
        model.add_component("{}_eq09".format(self.name), self._eq09)
        for tx in t:
            self._eq09.add(self._storage[tx] <= self._advised_capacity)

        # calculate the annual running cost
        self._eq10 = pyoe.Constraint(
            expr=self._operational_cost == self._investment_cost * self.opex / 100
        )
        model.add_component("{}_eq10".format(self.name), self._eq10)

        # calculate the one-time installation cost
        self._eq11 = pyoe.Constraint(
            expr=self._investment_cost
            == self._advised_capacity * self.capex_capacity
            + self._advised_power * self.capex_power
        )
        model.add_component("{}_eq11".format(self.name), self._eq11)

        # calculate the losses of stored energy over time
        self._eq12 = pyoe.ConstraintList()
        model.add_component("{}_eq12".format(self.name), self._eq12)
        for tx in t:
            if tx == 1:
                self._eq12.add(self._losses[tx] == 0)
            else:
                self._eq12.add(
                    self._losses[tx] == self.relative_losses * self._storage[tx - 1]
                )

        return model
