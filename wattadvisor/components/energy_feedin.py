"""Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

import pyomo.environ as pyoe
from pyomo.core.util import sum_product
import pandas as pd
from pydantic import Field, field_validator

import wattadvisor.data_models.enums as enums
from .non_investment_component import NonInvestmentComponent


class EnergyFeedin(NonInvestmentComponent):
    """Component that feeds surplus energy into grid .

    Parameters
    ----------

    energy_price_scalar : float | None, optional
        Scalar price for feeding in per energy unit [€/kWh], by default None
    energy_price_profile : pd.Series | None, optional
        Time series containing hourly variant energy prices for one year, by default None
    """

    energy_price_scalar: float | None = None
    energy_price_profile: pd.Series | None = Field(default=None, exclude=True)

    def __init__(self, **data):
        super().__init__(**data)

        if self.energy_price_profile is None:
            if self.energy_price_scalar is None:
                self.energy_price_scalar = 0

    @field_validator("energy_price_profile")
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

    def _load_params(self, model: pyoe.Model, t: pyoe.RangeSet) -> pyoe.Model:
        """[Function that loads parameters, which are used in the calculation, from a
            default file stored in the directory 'Files'.
            Current default file: Universalmodell_Stunde_Default.xlsx]

        Args:
            t ([list]): [contains the hourly time stamps of the baseline year (2017)]
            active_criteria ([dictionary]): [User input, that contains the information which
                            components are in use and which optimization criteria are active.]
        """

        if self.energy_price_profile is None:
            self._energy_price_dict = {tx: self.energy_price_scalar for tx in t}
        else:
            self._energy_price_dict = self.energy_price_profile.set_axis(t).to_dict()

        self._energy_price_profile = pyoe.Param(t, initialize=self._energy_price_dict)
        model.add_component(
            f"{self.name}_energy_price_profile", self._energy_price_profile
        )

        return model

    def _add_variables(self, model: pyoe.Model, t: pyoe.RangeSet) -> pyoe.Model:

        # (Input) electricity to grid [kWh]
        self._input = pyoe.Var(t, bounds=(0.0, None))
        model.add_component("{}_input".format(self.name), self._input)

        # calculated cost [€], without regard to the optimization criteria, cost<0 --> profit
        self._feedin_income = pyoe.Var()
        model.add_component("{}_feedin_income".format(self.name), self._feedin_income)

        # total cost, which is evaluated in the target function
        self._annuity = pyoe.Var()
        model.add_component("{}_annuity".format(self.name), self._annuity)

        self.bilance_variables.input[self.energy_type] = self._input

        return model

    def _add_constraints(self, model: pyoe.Model, t: pyoe.RangeSet) -> pyoe.Model:

        # calculating the total cost by applying the price to the imported electricity
        self._eq01 = pyoe.Constraint(expr=self._annuity == self._feedin_income)
        model.add_component("{}_eq01".format(self.name), self._eq01)

        self._eq02 = pyoe.Constraint(
            expr=self._feedin_income
            == -1 * sum_product(self._input, self._energy_price_profile, index=t)
        )
        model.add_component("{}_eq02".format(self.name), self._eq02)

        return model
