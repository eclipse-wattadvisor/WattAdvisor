import pyomo.environ as pyoe
from pyomo.core.util import sum_product
import pandas as pd

from .base import Component
import wattadvisor.data_models.enums as enums


class EnergyPurchase(Component):

    def __init__(self, 
                 name: str, 
                 parameters: dict, 
                 energy_type: enums.EnergyType, 
                 energy_price_scalar: float | None = None, 
                 energy_price_profile: pd.Series | None = None, 
                 power_price: float | None = None):
        
        """Component that simulates the import and obtaining of energy from external sources 
        in different forms like gas, oil, electricity or heat.
        This component imports electric power and applies a cost for the amount imported as
        well as a monthly base rate depending on the consumption.

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
            Energy type which is purchased
        energy_price_scalar : float | None, optional
            Scalar price for purchasement per energy unit [€/kWh], by default None
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

        #(Output) obtained electrical energy [kW]
        self.output=pyoe.Var(t, bounds=(0.0, None))
        model.add_component('{}_output'.format(self.name), self.output)

        # peak power [kW] purchased
        self.max_power=pyoe.Var(bounds=(0.0, None))
        model.add_component('{}_max_power'.format(self.name), self.max_power)

        # calculated cost [€], without regard to the optimization criteria
        self.purchase_cost=pyoe.Var()
        model.add_component('{}_purchase_cost'.format(self.name), self.purchase_cost)

        # calculated amount of co2 emissions [grams]
        self.co2=pyoe.Var(t, bounds=(0.0, None))
        model.add_component('{}_co2'.format(self.name), self.co2)

        # total cost, which is evaluated in the target function
        self.z=pyoe.Var()
        model.add_component('{}_z'.format(self.name), self.z)

        self.bilance_variables.output[self.energy_type] = self.output

        return model

    def _add_constraints(self, model: pyoe.Model, t: pyoe.RangeSet) -> pyoe.Model:

        # calculating the total cost by applying the price to the imported electricity
        self.eq01=pyoe.Constraint(expr=self.z == self.purchase_cost)
        model.add_component('{}_eq01'.format(self.name),self.eq01)

        self.eq02=pyoe.Constraint(expr=self.purchase_cost == sum_product(self.output, self.energy_price_profile, index=t) + self.max_power * self.power_price)
        model.add_component('{}_eq02'.format(self.name), self.eq02)
        
        self.eq03=pyoe.ConstraintList()
        model.add_component('{}_eq03'.format(self.name), self.eq03)
        for tx in t:
            self.eq03.add(self.co2[tx] == self.output[tx] * self.co2_intensity)

        # calculate peak power
        self.eq04=pyoe.ConstraintList()
        model.add_component('{}_eq04'.format(self.name), self.eq04)
        for tx in t:
            self.eq04.add(self.output[tx] <= self.max_power)

        return model