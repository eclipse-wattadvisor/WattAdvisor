"""Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

import pyomo.environ as pyoe
import pandas as pd
from pydantic import Field, field_validator

from .non_investment_component import NonInvestmentComponent
from ..utils.demand_tools import (
    generate_electrical_demand_profile,
    generate_heat_demand_profile,
)
from ..data_models.enums import EnergyUnit, EnergyType
from ..data_models.weather_data import WeatherDataHeightSpecific


class EnergyDemand(NonInvestmentComponent):
    """Component which consumes energy of a certain ``EnergyType`` to fulfill an energy demand.

    Parameters
    ----------
    demand_profile : pd.Series | None, optional
        Time series representing an hourly demand profile for one year, by default None
    demand_sum : float | None, optional
        Sum of energy demanded per year, by default None
    demand_unit : EnergyUnit | None, optional
        unit of the amount of energy given by `demand_sum`, by default None
    profile_type : str | None, optional
        Type of energy demand profile to generate a profile for if ``demand_profile`` not provided, by default None.
        See parameter ``demand_group`` of functions ``..utils.demand_tools.generate_electrical_demand_profile()``
        and ``..utils.demand_tools.generate_heat_demand_profile()`` for more information.
    temperature_air : WeatherDataHeightSpecific | None, optional
        Object containing weather data with an air temperature series [°C], by default None.
        Only required if ``energy_type`` is ``THERMAL`` or ``NATURAL_GAS`` and ``demand_profile`` is ``None``
    """

    demand_profile: pd.Series | None = Field(default=None, exclude=True)
    demand_sum: float | None = Field(ge=0, default=None)
    demand_unit: EnergyUnit | None = None
    profile_type: str | None = None
    profile_year: int | None = Field(ge=1970, default=None)
    temperature_air: WeatherDataHeightSpecific | None = Field(
        default=None, exclude=True
    )

    @field_validator("demand_profile")
    @classmethod
    def check_time_series_length(cls, series: pd.Series | None) -> pd.Series | None:
        """Checks whether the series given by `series` contains exactly 8760 values.

        Parameters
        ----------
        series : pd.Series | None
            The series which should be checked for correct length

        Returns
        -------
        pd.Series | None
            The checked series

        Raises
        ------
        ValueError
            If given ``series`` does not exactly contain 8760 values.
        """
        if series is not None and len(series) != 8760:
            raise ValueError("Covered time span by weather data is not 8760 hours.")

        return series

    def __init__(self, **data):
        super().__init__(**data)

        """
        Raises
        ------
        ValueError
        If no ``demand_profile`` and no `demand_sum` or no `profile_type` or no `profile_year` given
        ValueError
            If no ``demand_profile`` and no `weather_temp_air_data` given and `energy_type` is `THERMAL` or `NATURAL_GAS`
        """

        if self.demand_profile is None:
            if (
                self.demand_sum is None
                or self.profile_type is None
                or self.demand_unit is None
                or self.profile_year is None
            ):
                raise ValueError(
                    "If no profile given, demand sum, energy unit of the demand sum value, profile type and year to generate profile for must be given!"
                )

            elif (
                self.energy_type in [EnergyType.THERMAL, EnergyType.NATURAL_GAS]
                and self.temperature_air is None
            ):
                raise ValueError(
                    "To generate thermal or gas demand profile, profile of air temperature must be provided!"
                )

            elif self.energy_type in [EnergyType.ELECTRICAL, EnergyType.COOLING]:
                self.demand_profile = generate_electrical_demand_profile(
                    self.demand_sum * self.demand_unit.get_conversion_factor(),
                    self.profile_type,
                    self.profile_year,
                )

            elif self.energy_type in [EnergyType.THERMAL, EnergyType.NATURAL_GAS]:
                self.demand_profile = generate_heat_demand_profile(
                    self.demand_sum * self.demand_unit.get_conversion_factor(),
                    self.profile_type,
                    self.profile_year,
                    self.temperature_air.series[0],
                )

    def _load_params(self, model: pyoe.Model, t: pyoe.RangeSet) -> pyoe.Model:

        self._input = pyoe.Param(
            t, initialize=self.demand_profile.set_axis(t).to_dict()
        )
        model.add_component(f"{self.name}_input", self._input)

        self.bilance_variables.input[self.energy_type] = self._input

        return model
