"""Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

import logging

from pyomo.core import Model, RangeSet

from wattadvisor.data_models import bilance_variables


logger = logging.getLogger()


class Component:
    def __init__(self, name: str, interest_rate: None | float = None, parameters: None | dict = None):
        """Parent base class for all optimization energy components. 
        Contains empty methods which are overidden by child classes.
        
        Parameters
        ----------
        name : str
            Name of the component
        interest_rate : None | float, optional
            Interest rate to determine annuity factor for investment calculation of the component, by default None
        parameters : None | dict, optional
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

        Raises
        ----------
        ValueError
            If values of ``interest_rate`` and ``lifespan`` (from ``parameters``) are ``None``.

        """

        self.name = name
        self.interest_rate = interest_rate
        self.annuity_factor = None
        self.lifespan = None

        self.bilance_variables = bilance_variables.BilanceVariables()

        # create component attributes based on parameter dict of the component
        if parameters is not None:
            if "scalars" in parameters:
                for scalar in parameters["scalars"]:
                    setattr(self, scalar, parameters["scalars"][scalar])
                
                if "lifespan" in parameters["scalars"]:
                    # annuity factor to convert CAPEX into annual costs [%/year]
                    if self.interest_rate is None or self.lifespan is None:
                        raise ValueError(f"Missing interest rate and/or lifespan parameter in parameter file for component {self.name} to calculate annuity factor.")
                    else:
                        self.annuity_factor = self._calculate_annuity_factor(self.interest_rate, self.lifespan)
                    
            if "tabs" in parameters:
                for tab in parameters["tabs"]:
                    setattr(self, tab, parameters["tabs"][tab])
            
        logger.debug(f"Component '{self.name}' initialized via Class '{self.__class__.__name__}'")

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

    def _calculate_annuity_factor(self, i: float, n: int) -> float:
        """Calculates the annuity factor for investment calculation of the component.

        Parameters
        ----------
        i : float
            interest rate as decimal value
        n : int
            expected life span of the component

        Returns
        -------
        float
            calculated annuity factor for the component
        """

        if i > 0 and n > 0:
            return ((1+i)**n * i) / ((1+i)**n - 1)

        else:
            return 0