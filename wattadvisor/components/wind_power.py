"""Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

import pyomo.environ as pyoe
import pandas as pd
from pydantic import Field, field_validator

from ..utils.feedin_tools import calculate_windpower_feedin
from .investment_component import InvestmentComponent
from ..data_models.enums import EnergyType
from ..data_models.weather_data import WeatherDataHeightSpecific


class WindPower(InvestmentComponent):
    """Component to generate electrical energy from wind energy.

    Parameters
    ----------

    installed_power : float, optional
        Already installed electrical power of the component [kW] which acts as a lower bound, by default 0
    potential_power : float | None, optional
        Maximum installable electrical power of the component [kW], by default None
    latitude : float | None, optional
        Latitude of the location of the component, by default None
    longitude : float | None, optional
        Longitude of the location of the component, by default None
    hub_height : float
        height of the wind power plant hub above ground of the plant [m], by default 100
    normed_production : pd.Series | None, optional
        Determinated normed energy production series which can be given as an input. If given,
        calculation of normed production by the usage of weather data is skipped.
    capex : float | None, optional
        Capital expenditure cost of the component per electrical power [€/kW], by default 0
    opex : float | None, optional
        Operational expenditure cost of the component per CAPEX per year [%/a], by default 0
    wind_speed : WeatherDataHeightSpecific | None
        Object containing weather data describing the wind speed at a location, by default None
    roughness_length : WeatherDataHeightSpecific | None
        Object containing weather data describing the rougness length of the surrounding surface of a location, by default None
    air_temperature : WeatherDataHeightSpecific | None, optional
        Object containing weather data describing the air temperature at a location, by default None
    pressure : WeatherDataHeightSpecific | None, optional
        Object containing weather data describing the air pressure at a location, by default None
    density : WeatherDataHeightSpecific | None, optional
        Object containing weather data describing the air density at a location, by default None
    """

    installed_power: float = Field(ge=0, default=0)
    potential_power: float | None = Field(ge=0, default=None)
    latitude: float | None = None
    longitude: float | None = None
    hub_height: float = 100
    normed_production: pd.Series | None = Field(default=None, exclude=True)
    capex: float = Field(ge=0, default=0)
    opex: float = Field(ge=0, default=0)
    wind_speed: WeatherDataHeightSpecific | None = Field(default=None, exclude=True)
    roughness_length: WeatherDataHeightSpecific | None = Field(
        default=None, exclude=True
    )
    air_temperature: WeatherDataHeightSpecific | None = Field(
        default=None, exclude=True
    )
    pressure: WeatherDataHeightSpecific | None = Field(default=None, exclude=True)
    density: WeatherDataHeightSpecific | None = Field(default=None, exclude=True)

    def __init__(self, **data):
        super().__init__(**data)

        if self.normed_production is None:
            if self.latitude is None or self.longitude is None:
                raise ValueError(
                    "If no normed production profile given, latitude and longitude of location must be given!"
                )

            if self.wind_speed is None or self.roughness_length is None:
                raise ValueError(
                    "If no normed production profile given, weather data must be given!"
                )

            self.normed_production = calculate_windpower_feedin(
                self.wind_speed,
                self.roughness_length,
                self.latitude,
                self.longitude,
                self.hub_height,
                self.air_temperature,
                self.pressure,
                self.density,
            )

    @field_validator("normed_production")
    @classmethod
    def check_time_series_length(cls, value: pd.Series | None) -> pd.Series | None:
        if value is not None and len(value) != 8760:
            raise ValueError("Covered time span by weather data is not 8760 hours.")

        return value

    def _load_params(self, model: pyoe.Model, t: pyoe.RangeSet) -> pyoe.Model:

        self._normed_production = pyoe.Param(
            t, initialize=self.normed_production.set_axis(t).to_dict()
        )
        model.add_component(f"{self.name}_normed_production", self._normed_production)

        return model

    def _add_variables(self, model: pyoe.Model, t: pyoe.RangeSet) -> pyoe.Model:

        # (Output) electrical power [kW]
        self._output_electrical = pyoe.Var(t, bounds=(0.0, None))
        model.add_component(
            "{}_output_electrical".format(self.name), self._output_electrical
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

        # peak power [kWp], that needs to be installed
        self._advised_power = pyoe.Var(
            bounds=(self.installed_power, self.potential_power)
        )
        model.add_component("{}_advised_power".format(self.name), self._advised_power)

        self.bilance_variables.output[EnergyType.ELECTRICAL] = self._output_electrical

        return model

    def _add_constraints(self, model: pyoe.Model, t: pyoe.RangeSet) -> pyoe.Model:

        # calculating total cost, costs depending on installed power and eventually co2 emissions
        self._eq01 = pyoe.Constraint(
            expr=self._annuity
            == (self._investment_cost * self.annuity_factor + self._operational_cost)
        )
        model.add_component("{}_eq01".format(self.name), self._eq01)

        # calculating electrical output by applying the installed power to the standard profile
        self._eq02 = pyoe.ConstraintList()
        model.add_component("{}_eq02".format(self.name), self._eq02)
        for tx in t:
            self._eq02.add(
                self._output_electrical[tx]
                == self._advised_power * self._normed_production[tx]
            )

        # calculate the annual running cost
        self._eq04 = pyoe.Constraint(
            expr=self._operational_cost == self._investment_cost * self.opex / 100
        )
        model.add_component("{}_eq04".format(self.name), self._eq04)

        # calculate the one-time installation cost
        self._eq05 = pyoe.Constraint(
            expr=self._investment_cost == self._advised_power * self.capex
        )
        model.add_component("{}_eq05".format(self.name), self._eq05)

        return model
