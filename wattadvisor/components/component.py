"""Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

import logging
from typing import ClassVar

from pyomo.core import Model, RangeSet
import pyomo.environ as pyoe
from pydantic import Field, model_validator, computed_field

from ..data_models.bilance_variables import BilanceVariables
from ..data_models.base_model import BaseModelCustom
from ..data_models.enums import EnergyType
from ..utils.parameters import Parameters


logger = logging.getLogger()


class Component(BaseModelCustom):
    """Parent base class for all optimization energy components. 
        Contains empty methods which are overidden by child classes.
        
        Parameters
        ----------
        name : str | None, optional
            Name of the component. If not given, name is generated automatically based on the 
            class name of the component and an integer counter, default None
        parameters : None | dict, optional
            Dictionary of techno-economic parameters of the component, by default None.
            A dict of the following structure is expected. 
            At least one key at first level is required:

            .. code-block:: json

                {"parameter_title": 0}

        Raises
        ----------
        ValueError
            If values of ``interest_rate`` and ``lifespan`` (from ``parameters``) are ``None``.

    """
    
    names_counter: ClassVar[dict] = {}
    name: str | None = None
    parameters: dict | None = Field(default=None, exclude=True, description="Der Name des Benutzers")
    bilance_variables: BilanceVariables = Field(default_factory=BilanceVariables, exclude=True)

    @computed_field
    @property
    def annuity(self) -> float | None:
        """Returns the annuity of the component
        if the attribute ``_annuity`` exists.

        Returns
        -------
        float | None
            Annuity [€/a]
        """

        if hasattr(self, "_annuity"):
            return self._annuity.value

    @computed_field
    @property
    def operational_cost(self) -> float | None:
        """Returns the operational cost of the component
        if the attribute ``_operational_cost`` exists.

        Returns
        -------
        float | None
            Operational cost [€/a]
        """

        if hasattr(self, "_operational_cost"):
            return self._operational_cost.value
        
    @computed_field
    @property
    def investment_cost(self) -> float | None:
        """Returns the investment cost of the component
        if the attribute ``_investment_cost`` exists.

        Returns
        -------
        float | None
            Investment cost [€]
        """

        if hasattr(self, "_investment_cost"):
            return self._investment_cost.value
        
    @computed_field
    @property
    def advised_power(self) -> float | None:
        """Returns the advised power of the component
        if the attribute ``_advised_power`` exists.

        Returns
        -------
        float | None
            Advised power [kW or kWp]
        """

        if hasattr(self, "_advised_power"):
            return self._advised_power.value
        
    @computed_field
    @property
    def advised_capacity(self) -> float | None:
        """Returns the advised capacity of the component
        if the attribute ``_advised_capacity`` exists.

        Returns
        -------
        float | None
            Advised capacity [kWh]
        """

        if hasattr(self, "_advised_capacity"):
            return self._advised_capacity.value
        
    @computed_field
    @property
    def advised_area(self) -> float | None:
        """Returns the advised area of the component
        if the attribute ``_advised_area`` exists.

        Returns
        -------
        float | None
            Advised area [m²]
        """

        if hasattr(self, "_advised_area"):
            return self._advised_area.value

    @computed_field
    @property
    def output_energy_sum(self) -> dict[EnergyType, float] | None:
        """Returns the sum of energy the component
        puts out per energy type.

        Returns
        -------
        dict[EnergyType, float] | None
            Sum of output energy [kWh] per energy type
        """

        if len(self.bilance_variables.output.keys()) > 0:
            output_energy_sum_dict = {}
            for energy_type, bilance_variable in self.bilance_variables.output.items():
                output_energy_sum_dict[energy_type] = sum(bilance_variable.extract_values().values())

            return output_energy_sum_dict
        

    @computed_field
    @property
    def max_power(self) -> float | None:
        """Returns the maximum amount of power purchased by
        the component if the attribute ``_max_power`` exists.

        Returns
        -------
        float | None
            Maximum purchase power [kW]
        """

        if hasattr(self, "_max_power"):
            return self._max_power.value
        
    @computed_field
    @property
    def purchase_cost(self) -> float | None:
        """Returns the purchase cost of the component
        if the attribute ``_purchase_cost`` exists.

        Returns
        -------
        float | None
            Purchase cost [€/a]
        """

        if hasattr(self, "_purchase_cost"):
            return self._purchase_cost.value
    
    @computed_field
    @property
    def feedin_income(self) -> float | None:
        """Returns the income from energy feedin of the component
        if the attribute ``_feedin_income`` exists.

        Returns
        -------
        float | None
            Feedin income [€/a]
        """

        if hasattr(self, "_feedin_income"):
            return self._feedin_income.value

    @computed_field
    @property
    def co2_emissions(self) -> float | None:
        """Returns the CO2 Emissions produced by the component
        if the attribute ``_co2_intensity`` exists.

        Returns
        -------
        float | None
            CO2 emissions [t]
        """

        if hasattr(self, "co2_intensity"):
            return self.co2_intensity * sum(self._output.extract_values().values()) / 1e6
        
    @computed_field
    @property
    def energy_purchased(self) -> float | None:
        """Returns the sum of energy purchased by the component
        if the attribute ``_purchase_cost`` exists.

        Returns
        -------
        float | None
            Sum of energy purchased [kWh]
        """

        if hasattr(self, "_purchase_cost"):   
            return sum(list(self.bilance_variables.output.values())[0].extract_values().values())

    @model_validator(mode="before")
    @classmethod
    def get_parameters_from_file(cls, data: dict) -> dict:
        class_name = cls.__name__
        
        # load parameters
        for param_name, value in Parameters.get_parameters(class_name).items():
            # set all values from parameter file to data dict
            data[param_name] = value
        
        return data

    def __init__(self, **data):
        super().__init__(**data)

        if self.name is None:
            if self.__class__.__name__ in Component.names_counter:
                Component.names_counter[self.__class__.__name__] += 1
            else:
                Component.names_counter[self.__class__.__name__] = 1
            
            self.name = f"{self.__class__.__name__}_{Component.names_counter[self.__class__.__name__]}"

        logger.debug(f"Component '{self.name}' initialized via Class '{self.__class__.__name__}'")

    def has_input(self, energy_type: EnergyType) -> bool:
        """Checks whether the components ``bilance_variables`` attribute 
        contains an input with the given `energy_type`.

        Parameters
        ----------
        energy_type : EnergyType
            Energy type for which the bilance variables 
            should be checked for an input

        Returns
        -------
        bool
            Returns true if given energy type is in bilance_variables input side,
            else false
        """      

        return energy_type in self.bilance_variables.input
    
    def has_output(self, energy_type: EnergyType) -> bool:
        """Checks whether the components ``bilance_variables`` attribute 
        contains an output with the given `energy_type`.

        Parameters
        ----------
        energy_type : EnergyType
            Energy type for which the bilance variables 
            should be checked for an output

        Returns
        -------
        bool
            Returns true if given energy type is in bilance_variables output side,
            else false
        """  
        
        return energy_type in self.bilance_variables.output

    def _load_params(self, model: Model, t: RangeSet) -> Model:
        """Function to add parameters to the pyomo optimization model in `model`

        Parameters
        ----------
        model : Model
            Pyomo model to which parameters will be added.
        t : RangeSet
            Time set over which time-variant parameters will be added.

        Returns
        -------
        Model
            Pyomo model with the added parameters
        """

        return model

    def _add_variables(self, model: Model, t: RangeSet) -> Model:
        """Function to add variables to the pyomo optimization model in `model`

        Parameters
        ----------
        model : Model
            Pyomo model to which variables will be added.
        t : RangeSet
            Time set over which time-variant variables will be added.

        Returns
        -------
        Model
            Pyomo model with the added variables
        """

        return model

    def _add_constraints(self, model: Model, t: RangeSet) -> Model:
        """Function to add constraints to the pyomo optimization model in `model`

        Parameters
        ----------
        model : Model
            Pyomo model to which constraints will be added.
        t : RangeSet
            Time set over which time-variant constraints will be added.

        Returns
        -------
        Model
            Pyomo model with the added constraints
        """

        return model

    def add_to_model(self, model: Model, t: RangeSet) -> Model:
        """Calls the appropriate functions to add parameters, variables and constraints to the pyomo model given by `model`.

        Parameters
        ----------
        model : Model
            Pyomo model to which the parameters, variables and constraints will be added.
        t : RangeSet
            Time set over which time-variant parameters, variables and constraints will be added.

        Returns
        -------
        Model
            Pyomo model with the added parameters, variables and constraints
        """

        # Call to load the parameters in form of scalars, sets or charts
        model = self._load_params(model, t)
        # Call to add variables to the optimization model
        model = self._add_variables(model, t)
        # Call to add constraints to the optimization model
        model = self._add_constraints(model, t)

        logger.debug(f"Component '{self.name}' added to model.")

        return model