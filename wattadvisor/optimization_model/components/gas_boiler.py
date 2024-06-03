import pyomo.environ as pyoe

from .base import Component
import wattadvisor.data_models.enums as enums


class GasBoiler(Component):

    def __init__(self, 
                 name: str, 
                 interest_rate: float, 
                 parameters: dict, 
                 installed_power: float, 
                 potential_power: float | None = None, 
                 capex: float | None = None, 
                 opex: float | None = None, 
                 lifespan: float | None = None):
        
        """Component to turn an energy carrying medium like gas into thermal power.

        Parameters
        ----------
        name : str
            Name of the component
        interest_rate : float
            Interest rate to determine annuity factor for investment calculation of the component, by default None 
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

        installed_power : float
            Already installed thermal power of the component [kW] which acts as a lower bound
        potential_power : float | None, optional
            Maximum installable thermal power of the component [kW], by default None
        capex : float | None, optional
            Capital expenditure cost of the component per thermal power [€/kW], by default None
        opex : float | None, optional
            Operational expenditure cost of the component per CAPEX per year [%/a], by default None
        lifespan : float | None, optional
            Expected lifespan of the component [a], by default None
        """

        super().__init__(name, interest_rate, parameters)

        self.installed_power = installed_power
        self.potential_power = potential_power
        
        if capex is not None:
            self.capex = capex
        
        if opex is not None:
            self.opex = opex
        
        if lifespan is not None:
            self.lifespan = lifespan

    def _add_variables(self, model: pyoe.Model, t: pyoe.RangeSet) -> pyoe.Model:

        #(Output) thermal power [kW]
        self.heat=pyoe.Var(t, bounds=(0.0, None))
        model.add_component('{}_heat'.format(self.name), self.heat)

        #(Input) gas consumption [kW]
        self.gas=pyoe.Var(t, bounds=(0.0, None))
        model.add_component('{}_gas'.format(self.name), self.gas)

        # total cost, which is evaluated in the target function
        self.z=pyoe.Var(bounds=(0.0, None))
        model.add_component('{}_z'.format(self.name), self.z)

        # annual running cost
        self.running_cost=pyoe.Var(bounds=(0.0, None))
        model.add_component('{}_running_cost'.format(self.name), self.running_cost)

        # one-time installation cost
        self.installation_cost = pyoe.Var(bounds=(0.0, None))
        model.add_component('{}_installation_cost'.format(self.name), self.installation_cost)

        # peak power [kWp], necessary to install
        self.max_power=pyoe.Var(bounds=(self.installed_power, self.potential_power))
        model.add_component('{}_max_power'.format(self.name), self.max_power)

        self.bilance_variables.input[enums.EnergyType.NATURAL_GAS] = self.gas
        self.bilance_variables.output[enums.EnergyType.THERMAL] = self.heat

        return model

    def _add_constraints(self, model: pyoe.Model, t: pyoe.RangeSet) -> pyoe.Model:

        # calculating total cost, depending on peak power
        self.eq01=pyoe.Constraint(expr=self.z == self.installation_cost * self.annuity_factor + self.running_cost)
        model.add_component('{}_eq01'.format(self.name), self.eq01)

        # calculating thermal power, by applying efficiency to gas input
        self.eq02=pyoe.ConstraintList()
        model.add_component('{}_eq02'.format(self.name), self.eq02)
        for tx in t:
            self.eq02.add(self.gas[tx] * self.eff == self.heat[tx])

        # setting peak power
        self.eq03=pyoe.ConstraintList()
        model.add_component('{}_eq03'.format(self.name), self.eq03)
        for tx in t:
            self.eq03.add(self.heat[tx] <= self.max_power)

        #calculate the annual running cost
        self.eq04=pyoe.Constraint(expr=self.running_cost == self.installation_cost * self.opex/100)
        model.add_component('{}_eq04'.format(self.name), self.eq04)

        #calculate the one-time installation cost
        self.eq05=pyoe.Constraint(expr=self.installation_cost == self.max_power * self.capex)
        model.add_component('{}_eq05'.format(self.name), self.eq05)

        return model