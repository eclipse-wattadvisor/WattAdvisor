"""Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

import pyomo.environ as pyoe
import pandas as pd
from pydantic import Field

from .investment_component import InvestmentComponent
from ..utils.calc_cops import calc_cops
from ..data_models.enums import EnergyType
from ..data_models.weather_data import (
    WeatherDataHeightUnspecific,
    WeatherDataHeightSpecific,
)


class HeatPump(InvestmentComponent):
    """Component that uses electrical energy and a low temperature heat source to generate higher temperature heat.

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
    supply_temperature_heat : float, optional
        Supply temperature of heating [°C] used for calculation of the heating cop in combination with temperature of heating source, by default 50°C
    quality_grade : float
        Scale-down factor [-] to be applied on the Carnot efficiency to calculate realistic COP for the heat pump
        Further information can be found [here](https://oemof-thermal.readthedocs.io/en/latest/compression_heat_pumps_and_chillers.html)
    cop_series : list | None, optional
        List of COP values [-] for each hour in one year (8760 values necessary) for the heating process, by default None.
        If given, the COP will not be calculated using weather data. Instead the given COP values are used directly
    source_temperature_series : WeatherDataHeightUnspecific | WeatherDataHeightSpecific | None, optional
        Object containing weather data with a temperature series [°C] of the usable cooling and heating source to calculate COP values, by default None.
        If not given, `cop_series` must be given.
    """

    capex: float = Field(ge=0, default=0)
    opex: float = Field(ge=0, default=0)
    installed_power: float = Field(ge=0, default=0)
    potential_power: float | None = Field(ge=0, default=None)
    supply_temperature_heat: float = Field(ge=0, default=50)
    quality_grade: float = Field(gt=0, lt=1)
    cop_series: list | None = Field(
        min_length=8760, max_length=8760, default=None, exclude=True
    )
    source_temperature_series: (
        WeatherDataHeightUnspecific | WeatherDataHeightSpecific | None
    ) = Field(default=None, exclude=True)

    def __init__(self, **data):
        super().__init__(**data)

        if self.source_temperature_series is None:
            if self.cop_series is None:
                raise ValueError(
                    "To calculate COP of heat pump, profile of source temperature must be provided!"
                )

        else:
            if isinstance(self.source_temperature_series, WeatherDataHeightSpecific):
                source_temperature_series = self.source_temperature_series.series[
                    0
                ].to_list()

            if isinstance(self.source_temperature_series, WeatherDataHeightUnspecific):
                source_temperature_series = (
                    self.source_temperature_series.series.to_list()
                )

            if self.cop_series is None:
                self.cop_series = calc_cops(
                    temp_high=[self.supply_temperature_heat],
                    temp_low=source_temperature_series,
                    quality_grade=self.quality_grade,
                    mode="heat_pump",
                )

    def _load_params(self, model: pyoe.Model, t: pyoe.RangeSet) -> pyoe.Model:

        self._cop_heating = pyoe.Param(
            t, initialize={tx: self.cop_series[tx - 1] for tx in t}
        )
        model.add_component(f"{self.name}_cop_heating", self._cop_heating)

        return model

    def _add_variables(self, model: pyoe.Model, t: pyoe.RangeSet) -> pyoe.Model:

        # (Output) thermal power [kW]
        self._output_thermal = pyoe.Var(t, bounds=(0.0, None))
        model.add_component("{}_output_thermal".format(self.name), self._output_thermal)

        # (Input) electrical consumption [kW]
        self._input_electrical = pyoe.Var(t, bounds=(0.0, None))
        model.add_component(
            "{}_input_electrical".format(self.name), self._input_electrical
        )

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

        # peak thermal power [kWp], necessary to be installed
        self._advised_power = pyoe.Var(
            bounds=(self.installed_power, self.potential_power)
        )
        model.add_component("{}_advised_power".format(self.name), self._advised_power)

        self.bilance_variables.input[EnergyType.ELECTRICAL] = self._input_electrical
        self.bilance_variables.output[EnergyType.THERMAL] = self._output_thermal

        return model

    def _add_constraints(self, model: pyoe.Model, t: pyoe.RangeSet) -> pyoe.Model:

        # calculating total cost, depending on peak thermal power
        self._eq01 = pyoe.Constraint(
            expr=self._annuity
            == self._investment_cost * self.annuity_factor + self._operational_cost
        )
        model.add_component("{}_eq01".format(self.name), self._eq01)

        # calculating the thermal power output from the electrical consumption
        self._eq02 = pyoe.ConstraintList()
        model.add_component("{}_eq02".format(self.name), self._eq02)
        for tx in t:
            self._eq02.add(
                self._output_thermal[tx]
                == self._cop_heating[tx] * self._input_electrical[tx]
            )

        # setting peak thermal power
        self._eq03 = pyoe.ConstraintList()
        model.add_component("{}_eq03".format(self.name), self._eq03)
        for tx in t:
            self._eq03.add(self._output_thermal[tx] <= self._advised_power)

        # calculate the annual running cost
        self._eq05 = pyoe.Constraint(
            expr=self._operational_cost == self._investment_cost * self.opex / 100
        )
        model.add_component("{}_eq05".format(self.name), self._eq05)

        # calculate the one-time installation cost
        self._eq06 = pyoe.Constraint(
            expr=self._investment_cost == self._advised_power * self.capex
        )
        model.add_component("{}_eq06".format(self.name), self._eq06)

        return model


class HeatPumpAir(HeatPump):
    """Air source heat pump

    Parameters
    ----------
    quality_grade : float, optional
        Scale-down factor [-] to be applied on the Carnot efficiency to calculate realistic COP for the primary heat pump, by default 0.4
        Further information can be found [here](https://oemof-thermal.readthedocs.io/en/latest/compression_heat_pumps_and_chillers.html)
    """

    quality_grade: float = Field(gt=0, lt=1, default=0.4)


class HeatPumpGround(HeatPump):
    """Ground source heat pump

    Parameters
    ----------
    quality_grade : float, optional
        Scale-down factor [-] to be applied on the Carnot efficiency to calculate realistic COP for the primary heat pump, by default 0.55
        Further information can be found [here](https://oemof-thermal.readthedocs.io/en/latest/compression_heat_pumps_and_chillers.html)
    """ 

    quality_grade: float = Field(gt=0, lt=1, default=0.55)
