"""Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

from typing import Literal

import pyomo.environ as pyoe
import pandas as pd
from pydantic import Field, field_validator

from ..utils.feedin_tools import calculate_pv_feedin
from .investment_component import InvestmentComponent
from ..data_models.enums import EnergyType
from ..data_models.weather_data import (
    WeatherDataHeightUnspecific,
    WeatherDataHeightSpecific,
)


class Photovoltaik(InvestmentComponent):
    """Component to purchase electrical energy via a PPA from a
    Photovoltaic plant that produces electricity from solar radiation.


    Parameters
    ----------
    capex : float | None, optional
        Capital expenditure cost of the component per electrical power [€/kWp], by default 0
    opex : float | None, optional
        Operational expenditure cost of the component per CAPEX per year [%/a], by default 0
    installed_power : float, optional
        Already installed electrical power of the component [kW] which acts as a lower bound, by default 0
    potential_power : float | None, optional
        Maximum installable electrical power of the component [kW], by default None
    latitude : float
        Latitude of the location of the plant
    longitude : float
        Longitude of the location of the plant
    azimuth : float, optional
        Azimuth orientation [°] of the photovoltaic plant where the power will be generated, by default 180

        - North=0
        - East=90
        - South=180
        - West=270
    tilt : float, optional
        Tilt orientation [°] of the photovoltaic plant where the power will be generated, by default 40

        - Up=0
        - horizon=90
    elevation : float, optional
        elevation of the location of the photovoltaic plant above sea level [m], by default 0
    normed_production : pd.Series | None, optional
        Determinated normed energy production series which can be given as an input. If given,
        calculation of normed production by the usage of 'weather_data' is skipped.
    ghi : WeatherDataHeightUnspecific | None, optional
        Object containing weather data describing the global horizontal irradiance at a location, by default None
    dhi : WeatherDataHeightUnspecific | None, optional
        Object containing weather data describing the diffuse horizontal irradiance at a location, by default None
    surface_type : Literal["urban", "grass", "fresh grass", "soil", "sand", "snow", "fresh snow", "asphalt", "concrete", "aluminum", "copper", "fresh steel", "dirty steel", "sea"], optional
        surface type of the surroundings of the photovoltaic plant where the power will be generated,  by default "urban"
    module_type : Literal["glass_glass", "glass_polymer"], optional
        Describes the module’s construction. Used for cell and module temperature calculations, by default "glass_glass"
    racking_model : Literal["open_rack", "close_mount", "insulated_back"], optional
        Used to identify a parameter set for the SAPM cell temperature model, by default "insulated_back"
    air_temperature : WeatherDataHeightSpecific | None, optional
        Object containing weather data describing the air temperature at a location, by default None
    dni : WeatherDataHeightUnspecific | None, optional
        Object containing weather data describing the direct normal irradiance at a location, by default None
    """

    capex: float = Field(ge=0, default=0)
    opex: float = Field(ge=0, default=0)
    installed_power: float = Field(ge=0, default=0)
    potential_power: float | None = Field(ge=0, default=None)
    latitude: float | None = None
    longitude: float | None = None
    azimuth: float = Field(ge=0, default=180)
    tilt: float = Field(ge=0, le=90, default=40)
    elevation: float = 0
    normed_production: pd.Series | None = Field(default=None, exclude=True)
    ghi: WeatherDataHeightUnspecific | None = Field(default=None, exclude=True)
    dhi: WeatherDataHeightUnspecific | None = Field(default=None, exclude=True)
    surface_type: Literal[
        "urban",
        "grass",
        "fresh grass",
        "soil",
        "sand",
        "snow",
        "fresh snow",
        "asphalt",
        "concrete",
        "aluminum",
        "copper",
        "fresh steel",
        "dirty steel",
        "sea",
    ] = "urban"
    module_type: Literal["glass_glass", "glass_polymer"] = "glass_glass"
    racking_model: Literal["open_rack", "close_mount", "insulated_back"] = (
        "insulated_back"
    )
    air_temperature: WeatherDataHeightSpecific | None = Field(
        default=None, exclude=True
    )
    dni: WeatherDataHeightUnspecific | None = Field(default=None, exclude=True)

    def __init__(self, **data):
        super().__init__(**data)

        if self.normed_production is None:

            if self.latitude is None or self.longitude is None:
                raise ValueError(
                    "If no normed production profile given, latitude and longitude of location must be given!"
                )

            if self.ghi is None or self.dhi is None:
                raise ValueError(
                    "If no normed production profile given, weather data must be given!"
                )

            self.normed_production = calculate_pv_feedin(
                ghi=self.ghi,
                dhi=self.dhi,
                latitude=self.latitude,
                longitude=self.longitude,
                azimuth=self.azimuth,
                tilt=self.tilt,
                surface_type=self.surface_type,
                elevation=self.elevation,
                module_type=self.module_type,
                racking_model=self.racking_model,
                dni=self.dni,
                air_temperature=self.air_temperature,
            )

    @field_validator("normed_production")
    @classmethod
    def check_time_series_length(cls, value: pd.Series | None) -> pd.Series | None:
        if value is not None and len(value) != 8760:
            raise ValueError("Covered time span by weather data is not 8760 hours.")

        return value

    def _load_params(self, model: pyoe.Model, t: pyoe.RangeSet) -> pyoe.Model:

        self._normed_production = pyoe.Param(
            t, initialize=self.normed_production.clip(0).set_axis(t).to_dict()
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

        # calculating total cost, costs depending on peak power and eventually co2 emissions
        self._eq01 = pyoe.Constraint(
            expr=self._annuity
            == self._investment_cost * self.annuity_factor + self._operational_cost
        )
        model.add_component("{}_eq01".format(self.name), self._eq01)

        # calculating electrical output by applying the peak power to the standard profile
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


class PhotovoltaikRoof(Photovoltaik):
    pass


class PhotovoltaikFreeField(Photovoltaik):
    pass
