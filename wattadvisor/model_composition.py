"""Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

import logging

import pyomo.environ as pyoe
from pyomo.core.base.PyomoModel import Model
from pyomo.core.base.set import RangeSet
from pyomo.core.util import quicksum

import wattadvisor.data_models.enums as enums

from .components.component import Component

logger = logging.getLogger()

def compose(input_components: list[Component],
            pyomo_model: Model,
            t: RangeSet) -> Model:
    """Adds all relevant components to the pyomo optimization model `pyomo_model` based on the parameterization of the components in `input_components` and creates the objective.

    Parameters
    ----------
    input_components : list[Component]
        List of components that should be added to the optimization model including their parameterization
    pyomo_model : Model
        Pyomo model to add the components and objective to
    t : RangeSet
        Time set to use for variable, parameter and constraint creation

    Returns
    -------
    Model
        The optimization model with all components added

    Raises
    ------
    ValueError
        If for one energy type a demand but no production component is parameterized, the bilance for this energy type cannot be built
    """
        
    for component in input_components:
        pyomo_model = component.add_to_model(pyomo_model, t)

    for energy_type in enums.EnergyType:

        bilance_vars_input = [x.bilance_variables.input.get(energy_type) for x in input_components if x.has_input(energy_type)]
        bilance_vars_output = [x.bilance_variables.output.get(energy_type) for x in input_components if x.has_output(energy_type)]

        if len(bilance_vars_input) == 0 and len(bilance_vars_output) == 0:
            continue

        elif len(bilance_vars_output) == 0 and len(bilance_vars_input) > 0:
            msg = f"Missing production component to build bilance constraint for energy type {energy_type}. Restrict consumption component(s)."
            # neue Constraint einfügen, die festlegt, dass die Werte der Variablen in bilance_vars_input immer 0 sein müssen
            balance = pyoe.ConstraintList()
            pyomo_model.add_component(f'balance_{energy_type.value}', balance)
            try:
                for tx in t:
                    balance.add(
                        quicksum(var[tx] for var in bilance_vars_input) == 0
                    )
            except ValueError:
                raise ValueError(f"Cannot built bilance for energy type {energy_type} due to missing production component(s) to fulfill the given demand.")
        
        elif len(bilance_vars_output) > 0 and len(bilance_vars_input) == 0:
            msg = f"Missing consumption component for energy type {energy_type}. Build empty bilance."
            # neue Constraint einfügen, die festlegt, dass die Werte der Variablen in bilance_vars_output größer gleich 0 sein können
            balance = pyoe.ConstraintList()
            pyomo_model.add_component(f'balance_{energy_type.value}', balance)
            for tx in t:
                balance.add(
                    quicksum(var[tx] for var in bilance_vars_output) >= 0
                )

        else:
            balance = pyoe.ConstraintList()
            pyomo_model.add_component(f'balance_{energy_type.value}', balance)
            for tx in t:
                if energy_type == enums.EnergyType.ELECTRICAL:
                    equation = quicksum(var[tx] for var in bilance_vars_output) == quicksum(var[tx] for var in bilance_vars_input)
                else:
                    equation = quicksum(var[tx] for var in bilance_vars_output) >= quicksum(var[tx] for var in bilance_vars_input)
                
                balance.add(equation)
            msg = f"Built bilance constraint for energy type {energy_type}."
        
        logger.info(msg)   

    objective_parts = [x._annuity for x in input_components if hasattr(x, '_annuity')]

    pyomo_model.add_component("Objective", pyoe.Objective(expr=
                quicksum(objective_parts),
                sense=pyoe.minimize))

    return pyomo_model