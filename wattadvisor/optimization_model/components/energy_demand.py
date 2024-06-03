"""Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

import pyomo.environ as pyoe
import pandas as pd

from .base import Component
from ..utils.demand_tools import generate_electrical_demand_profile, generate_heat_demand_profile
import wattadvisor.data_models.enums as enums


class EnergyDemand(Component):
    def __init__(self, 
                 name: str, 
                 energy_type: 
                 enums.EnergyType, 
                 demand_profile: pd.Series | None = None, 
                 demand_sum: float | None = None, 
                 profile_type: str | None = None, 
                 weather_temp_air_data: pd.Series | None = None):
        """Component which consumes energy of a certain ``EnergyType`` to fulfill an energy demand.

        Parameters
        ----------
        name : str
            Name of the component
        energy_type : enums.EnergyType
            Energy type which is consumed
        demand_profile : pd.Series | None, optional
            Time series representing an hourly demand profile for one year, by default None
        demand_sum : float | None, optional
            Sum of energy demanded per year, by default None
        profile_type : str | None, optional
            Type of energy demand profile to generate a profile for if ``demand_profile`` not provided, by default None.
            See parameter ``demand_group`` of functions ``..utils.demand_tools.generate_electrical_demand_profile()`` 
            and ``..utils.demand_tools.generate_heat_demand_profile()`` for more information.
        weather_temp_air_data : pd.Series | None, optional
            Time series of hourly air temperature values, by default None.
            Only required if ``energy_type`` is ``THERMAL`` or ``NATURAL_GAS`` and ``demand_profile`` is ``None``

        Raises
        ------
        ValueError
            If no ``demand_profile`` and no `demand_sum` or no `profile_type` given
        ValueError
            If no ``demand_profile`` and no `weather_temp_air_data` given and `energy_type` is `THERMAL` or `NATURAL_GAS`
        """
        
        super().__init__(name)

        self.energy_type = energy_type
        self.demand_profile = demand_profile
        self.demand_sum = demand_sum
        self.profile_type = profile_type
        self.weather_temp_air_data = weather_temp_air_data

        if self.demand_profile is None:
            if self.demand_sum is None or self.profile_type is None:
                raise ValueError("If no profile given, both demand sum and profile type must be given!")
            
            elif self.energy_type in [enums.EnergyType.THERMAL, enums.EnergyType.NATURAL_GAS] and self.weather_temp_air_data is None:
                raise ValueError("To generate thermal or gas demand profile, profile of air temperature must be provided!")

    def _load_params(self, model: pyoe.Model, t: pyoe.RangeSet) -> pyoe.Model:

        if self.demand_profile is None:
            if self.energy_type == enums.EnergyType.ELECTRICAL:
                self.demand_profile = generate_electrical_demand_profile(self.demand_sum, self.profile_type, 2022)

            elif self.energy_type in [enums.EnergyType.THERMAL, enums.EnergyType.NATURAL_GAS]:
                self.demand_profile = generate_heat_demand_profile(self.demand_sum, self.profile_type, 2022, self.weather_temp_air_data)

        self.demand_profile = self.demand_profile.set_axis(t).to_dict()

        self.load = pyoe.Param(t, initialize=self.demand_profile)
        model.add_component(f'{self.name}_load', self.load)

        self.bilance_variables.input[self.energy_type] = self.load

        return model