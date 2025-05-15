"""Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

import pyomo.environ as pyoe
import pandas as pd
from pydantic import Field, field_validator

from .investment_component import InvestmentComponent
from ..data_models.enums import EnergyType
from ..data_models.weather_data import WeatherDataHeightUnspecific


class SolarthermalEnergy(InvestmentComponent):
    """Component to generate thermal energy from solar energy.

        Parameters
        ----------
        capex : float, optional
            Capital expenditure cost of the component per area [€/qm], by default 0
        opex : float, optional
            Operational expenditure cost of the component per CAPEX per year [%/a], by default 0
        ghi : WeatherDataHeightUnspecific | None, optional
            Object containing weather data describing the global horizontal irradiance at a location, by default None
            Must be given if `normed_production` is None.
        installed_area : float, optional
            Already installed area of the component [qm] which acts as a lower bound, by default 0
        potential_power : float | None, optional
            Maximum installable area of the component [qm], by default None
        normed_production : pd.Series | None, optional
            Determinated normed energy production series which can be given as an input. If given,
            calculation of normed production by the usage of `ghi` is skipped.
            By default None
        eff : float | None, optional
            Efficiency grade of the solar thermal plant [-], by default None.
            Must be given if `normed_production` is None.
    """
    
    capex: float = Field(ge=0, default=0)
    opex: float = Field(ge=0, default=0)
    ghi: WeatherDataHeightUnspecific | None = Field(default=None, exclude=True)
    installed_area: float = Field(ge=0, default=0)
    potential_area: float | None = Field(ge=0, default=None)
    normed_production: pd.Series | None = Field(default=None, exclude=True)
    eff: float | None = Field(ge=0, default=None)

    def __init__(self, **data):
        super().__init__(**data)
        
        if self.normed_production is None:

            if self.ghi is None:
                raise ValueError("If no normed production profile given, weather data must be given!")
            
            if self.eff is None:
                raise ValueError("If no normed production profile given, plant efficiency must be given!")        

            self.normed_production = self.ghi.series / 1000 * self.eff

    @field_validator('normed_production')
    @classmethod
    def check_time_series_length(cls, value: pd.Series | None) -> pd.Series | None:
        if value is not None and len(value) != 8760:
            raise ValueError("Covered time span by weather data is not 8760 hours.")
        
        return value

    def _load_params(self, model: pyoe.Model, t: pyoe.RangeSet) -> pyoe.Model:
        self._normed_production = pyoe.Param(t, initialize=self.normed_production.set_axis(t).to_dict())
        model.add_component(f'{self.name}_normed_production', self._normed_production)

        return model
        
    def _add_variables(self, model: pyoe.Model, t: pyoe.RangeSet) -> pyoe.Model:

        #(Output) thermal power in kWh
        self._output_thermal=pyoe.Var(t, bounds=(0.0, None))
        model.add_component('{}_output_thermal'.format(self.name), self._output_thermal)

        # total cost, which is evaluated in the target function
        self._annuity=pyoe.Var(bounds=(0.0, None))
        model.add_component('{}_annuity'.format(self.name), self._annuity)

        # annual running cost
        self._operational_cost=pyoe.Var(bounds=(0.0, None))
        model.add_component('{}_operational_cost'.format(self.name), self._operational_cost)

        # one-time installation cost
        self._investment_cost = pyoe.Var(bounds=(0.0, None))
        model.add_component('{}_investment_cost'.format(self.name), self._investment_cost)

        # collector size [m²] that has to be installed at maximum
        self._advised_area=pyoe.Var(bounds=(self.installed_area, self.potential_area))
        model.add_component('{}_advised_area'.format(self.name), self._advised_area)

        self.bilance_variables.output[EnergyType.THERMAL] = self._output_thermal

        return model

    def _add_constraints(self, model: pyoe.Model, t: pyoe.RangeSet) -> pyoe.Model:

        # calculating total cost, costs depending on peak power and eventually co2 emissions
        self._eq01=pyoe.Constraint(expr=self._annuity == self._investment_cost * self.annuity_factor + self._operational_cost)
        model.add_component('{}_eq01'.format(self.name), self._eq01)

        # calculating thermal output by applying the peak power to the standard profile
        self._eq02=pyoe.ConstraintList()
        model.add_component('{}_eq02'.format(self.name), self._eq02)
        for tx in t:
            self._eq02.add(self._output_thermal[tx] == self._advised_area * self.eff * self._normed_production[tx])

        #calculate the annual running cost
        self._eq04=pyoe.Constraint(expr=self._operational_cost == self._investment_cost * self.opex/100)
        model.add_component('{}_eq04'.format(self.name), self._eq04)

        #calculate the one-time installation cost
        self._eq05=pyoe.Constraint(expr=self._investment_cost == self._advised_area * self.capex)
        model.add_component('{}_eq05'.format(self.name), self._eq05)

        return model