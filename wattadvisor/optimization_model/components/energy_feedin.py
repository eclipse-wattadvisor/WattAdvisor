"""Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

import pyomo.environ as pyoe
from pyomo.core.util import sum_product
import pandas as pd

import wattadvisor.data_models.enums as enums
from .base import Component


class EnergyFeedin(Component):

    def __init__(self, 
                 name: str, 
                 parameters: dict, 
                 energy_type: enums.EnergyType, 
                 energy_price_scalar: float | None = None, 
                 energy_price_profile: pd.Series | None = None, 
                 power_price: float | None = None):
        
        """Component that feeds surplus energy into grid .

        Parameters
        ----------
        name : str
            Name of the component
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

        energy_type : enums.EnergyType
            Energy type which is fed in
        energy_price_scalar : float | None, optional
            Scalar price for feeding in per energy unit [€/kWh], by default None
        energy_price_profile : pd.Series | None, optional
            Time series containing hourly variant energy prices for one year, by default None
        power_price : float | None, optional
            Price to pay for maximum grid load per year [€/(kW * a)], by default None
        """

        super().__init__(name, parameters=parameters)

        self.energy_type = energy_type
        self.energy_price_profile = energy_price_profile
        self.energy_price_scalar = energy_price_scalar
        self.power_price = power_price

    def _load_params(self, model: pyoe.Model, t: pyoe.RangeSet) -> pyoe.Model:
        """[Function that loads parameters, which are used in the calculation, from a
            default file stored in the directory 'Files'.
            Current default file: Universalmodell_Stunde_Default.xlsx]

        Args:
            t ([list]): [contains the hourly time stamps of the baseline year (2017)]
            active_criteria ([dictionary]): [User input, that contains the information which
                            components are in use and which optimization criteria are active.]
        """

        if self.power_price is None:
            self.power_price = 0

        if self.energy_price_profile is None:
            if self.energy_price_scalar is None:
                self.energy_price_scalar = 0
                
            self.energy_price_profile = {tx: self.energy_price_scalar for tx in t}

        else:
            self.energy_price_profile = self.energy_price_profile.set_axis(t).to_dict()

        self.power_price = pyoe.Param(initialize=self.power_price)
        model.add_component(f'{self.name}_power_price', self.power_price)

        self.energy_price_profile = pyoe.Param(t, initialize=self.energy_price_profile)
        model.add_component(f'{self.name}_energy_price_profile', self.energy_price_profile)

        return model


    def _add_variables(self, model: pyoe.Model, t: pyoe.RangeSet) -> pyoe.Model:

        #(Input) electricity to grid [kWh]
        self.input=pyoe.Var(t, bounds=(0.0, None))
        model.add_component('{}_input'.format(self.name), self.input)
        
        # calculated cost [€], without regard to the optimization criteria, cost<0 --> profit
        self.feedin_income=pyoe.Var()
        model.add_component('{}_feedin_income'.format(self.name), self.feedin_income)
        
        # total cost, which is evaluated in the target function
        self.z=pyoe.Var()
        model.add_component('{}_z'.format(self.name), self.z)

        self.bilance_variables.input[self.energy_type] = self.input

        return model

    def _add_constraints(self, model: pyoe.Model, t: pyoe.RangeSet) -> pyoe.Model:

        # calculating the total cost by applying the price to the imported electricity
        self.eq01=pyoe.Constraint(expr=self.z == self.feedin_income)
        model.add_component('{}_eq01'.format(self.name),self.eq01)

        self.eq02=pyoe.Constraint(expr=self.feedin_income == sum_product(self.input, self.energy_price_profile, index=t))
        model.add_component('{}_eq02'.format(self.name), self.eq02)

        return model
