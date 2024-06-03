"""Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

from __future__ import annotations
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
import logging

import pandas as pd
import pyomo.core.base.constraint
import pyomo.core.base.objective
import pyomo.core.base.param
import pyomo.core.base.set
import pyomo.core.base.var
from pyomo.core.base.PyomoModel import Model
from pyomo.core.util import quicksum

from ...data_models.enums import (AreaUnitComponent, PowerUnitComponent,
                             StorageComponent, OptimizationStatus)
from ...data_models.input_model import InputModel
from ...data_models.optimization_results_component_energy_production_object import \
    OptimizationResultsComponentEnergyProductionObject
from ...data_models.optimization_results_component_object import (
    OptimizationResultsComponentObjectArea,
    OptimizationResultsComponentObjectPower,
    OptimizationResultsComponentObjectPurchaseFeedin,
    OptimizationResultsComponentObjectStorage)
from ...data_models.optimization_results_model import OptimizationResultsModel
from ...data_models.optimization_results_scenario_kpis import \
    OptimizationResultsScenarioKpis
from ...data_models.optimization_results_scenario_object import \
    OptimizationResultsScenarioObject
from ...data_models.optimization_results_scenarios import \
    OptimizationResultsScenarios
from ...data_models.optimization_results_status import OptimizationResultsStatus
from ..components.base import Component
from ..components.energy_demand import EnergyDemand
from ..components.energy_feedin import EnergyFeedin
from ..components.energy_purchase import EnergyPurchase
if TYPE_CHECKING:
    from wattadvisor.optimization_model.opt_model import OptModel


logger = logging.getLogger()


def _generate_scenario_results(pyomo_model: Model, components_list: List[Component]) -> OptimizationResultsScenarioObject:
    """Creates an `OptimizationResultsScenarioObject` for one scenario (target or current) which is returned as part of the response of the WattAdvisor.

    Parameters
    ----------
    pyomo_model : Model
        Pyomo optimization model containing all parameters, variables and constraints aswell as the objective function. 
    components_list : List[Component]
        List of all optimization components added to the optimiziation model

    Returns
    -------
    OptimizationResultsScenarioObject
        Object containing the results (cost, produced energy, power) for one scenario (target or current)
    """

    total_investment_cost = sum([component.installation_cost.value for component in components_list if hasattr(component, "installation_cost")])
    total_operational_cost = sum([component.running_cost.value for component in components_list if hasattr(component, "running_cost")])
    total_purchase_cost = sum([component.purchase_cost.value for component in components_list if hasattr(component, "purchase_cost")])
    total_income = -sum([component.feedin_income.value for component in components_list if hasattr(component, "feedin_income")])
    total_annuities = pyomo_model.Objective.expr()

    components_results = []

    for component in components_list:
        filter_dict_storage_component = {x.get_component_class(): x for x in StorageComponent}
        filter_dict_power_unit_component = {x.get_component_class(): x for x in PowerUnitComponent}
        filter_dict_area_unit_component = {x.get_component_class(): x for x in AreaUnitComponent}

        if type(component) == EnergyPurchase:

            external_component_type = component.energy_type.get_external_purchase_type()

            component_results_object = OptimizationResultsComponentObjectPurchaseFeedin(
                component_type=external_component_type,
                purchase_cost=component.purchase_cost.value,
                annuity=component.z.value,
                produced_energy=_calculate_produced_energy(component)
            )

        elif type(component) == EnergyFeedin:

            external_component_type = component.energy_type.get_external_feedin_type()

            component_results_object = OptimizationResultsComponentObjectPurchaseFeedin(
                component_type=external_component_type,
                purchase_cost=component.feedin_income.value,
                annuity=component.z.value,
                produced_energy=_calculate_feedin_energy(component)
            )

        elif type(component) in filter_dict_power_unit_component and component.max_power.value > 0:

            external_component_type = filter_dict_power_unit_component[type(component)]

            component_results_object = OptimizationResultsComponentObjectPower(
                component_type=external_component_type,
                installed_power=component.max_power.value,
                investment_cost=component.installation_cost.value,
                operational_cost=component.running_cost.value,
                annuity=component.z.value,
                produced_energy=_calculate_produced_energy(component)
            )

        elif type(component) in filter_dict_area_unit_component and component.max_area.value > 0:

            external_component_type = filter_dict_area_unit_component[type(component)]

            component_results_object = OptimizationResultsComponentObjectArea(
                component_type=external_component_type,
                installed_power=component.max_area.value,
                investment_cost=component.installation_cost.value,
                operational_cost=component.running_cost.value,
                annuity=component.z.value,
                produced_energy=_calculate_produced_energy(component)
            )

        elif type(component) in filter_dict_storage_component and component.max_capacity.value > 0:

            external_component_type = filter_dict_storage_component[type(component)]

            component_results_object = OptimizationResultsComponentObjectStorage(
                component_type=external_component_type,
                installed_power=component.max_power.value,
                installed_capacity=component.max_capacity.value,
                investment_cost=component.installation_cost.value,
                operational_cost=component.running_cost.value,
                annuity=component.z.value
            )

        elif type(component) == EnergyDemand:
            continue 

        else:
            continue
        
        components_results.append(component_results_object)


    kpis = OptimizationResultsScenarioKpis(
        total_investment_cost=total_investment_cost,
        total_operational_cost=total_operational_cost,
        total_purchase_cost=total_purchase_cost,
        total_income=total_income,
        total_annuities=total_annuities
    )
    scenario_results = OptimizationResultsScenarioObject(components=components_results, kpis=kpis)

    return scenario_results

def _calculate_produced_energy(component: Component) -> Optional[List[OptimizationResultsComponentEnergyProductionObject]]:
    """Determines the sum of produced energy by one energy producing component ``component``.

    Parameters
    ----------
    component : Component
        Optimization model component which produces energy. 
        Must contain at least one element in `component.bilance_variables.output`

    Returns
    -------
    Optional[List[OptimizationResultsComponentEnergyProductionObject]]
        List of yearly produced energy amounts per `EnergyType`.
    """

    produced_energy = []

    for energy_type in component.bilance_variables.output:
        if component.bilance_variables.output.get(energy_type) is not None:
            produced_energy.append(
                OptimizationResultsComponentEnergyProductionObject(
                    energy_type=energy_type,
                    amount=quicksum(x.value for x in component.bilance_variables.output.get(energy_type).values())
        ))
    
    if len(produced_energy) == 0:
        produced_energy = None

    return produced_energy

def _calculate_feedin_energy(feedin_component: EnergyFeedin) -> Optional[List[OptimizationResultsComponentEnergyProductionObject]]:
    """Determines the sum of feedin energy by one feedin component ``feedin_component``.

    Parameters
    ----------
    feedin_component : EnergyFeedin
        Optimization model component which feeds in energy. 
        Must contain at least one element in `component.bilance_variables.input`

    Returns
    -------
    Optional[List[OptimizationResultsComponentEnergyProductionObject]]
        List of yearly feedin energy amounts per `EnergyType`.
    """

    feedin_energy = []

    for energy_type in feedin_component.bilance_variables.input:
        if feedin_component.bilance_variables.input.get(energy_type) is not None:
            feedin_energy.append(
                OptimizationResultsComponentEnergyProductionObject(
                    energy_type=energy_type,
                    amount=-quicksum(x.value for x in feedin_component.bilance_variables.input.get(energy_type).values())
        ))
    
    if len(feedin_energy) == 0:
        feedin_energy = None

    return feedin_energy

def _generate_current_scenario_results(opt_model_object: OptModel, components_list: List[Component]) -> Optional[OptimizationResultsScenarioObject]:
    """Determines the cost resulting for the fulfilment of the energy demands by the components already installed (current scenario). 

    Parameters
    ----------
    opt_model_object : OptModel
        Object of the optimization model
    components_list : List[Component]
        List of all optimization components added to the optimiziation model

    Returns
    -------
    Optional[OptimizationResultsScenarioObject]
        Object containing the results for the current scenario
    """
    for component in components_list:
        if all(hasattr(component, attr) for attr in ["potential_power", "installed_power", "potential_capacity", "installed_capacity"]):
            # storage component
            variable = opt_model_object.pyomo_model.find_component(f"{component.name}_max_capacity")
            if variable is not None:
                variable.fix(component.installed_capacity)

            if component.installed_power is not None:
                variable = opt_model_object.pyomo_model.find_component(f"{component.name}_max_power")
                if variable is not None:
                    variable.fix(component.installed_power)
        
        elif all(hasattr(component, attr) for attr in ["potential_power", "installed_power"]):
            # power component
            variable = opt_model_object.pyomo_model.find_component(f"{component.name}_max_power")
            if variable is not None:
                variable.fix(component.installed_power)   

        elif all(hasattr(component, attr) for attr in ["potential_area", "installed_area"]):
            # area component
            variable = opt_model_object.pyomo_model.find_component(f"{component.name}_max_area")
            if variable is not None:
                variable.fix(component.installed_area)

    try:
        opt_model_object._optimize()

    except RuntimeError:
        logger.warning("Could not determine current scenario results. Probably given energy demand cannot be fulfilled by the existing components and tariffs.")
        return None

    return _generate_scenario_results(opt_model_object.pyomo_model, components_list)

def write_detailed_results(pyomo_model: Model, components_list: List[Component], calculation_time: float, filename: str=None):
    """Creates a DataFrame with all optimization time series data and writes it to a excel file.

    Parameters
    ----------
    pyomo_model : Model
        Pyomo optimization model containing all parameters, variables and constraints aswell as the objective function. 
    components_list : List[Component]
        List of all optimization components added to the optimiziation model
    calculation_time : float
        Time in seconds it took for the solver to solve the optimization model
    filename : str, optional
        name of the Excel file to export, by default None
    """

    if filename is None:
        dt = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{dt}_results.xlsx"

    scalar_results = pd.Series()
    indexed_results = pd.DataFrame()

    scalar_results["Objective"] = pyomo_model.Objective.expr()
    scalar_results["total installation cost"] = sum([component.installation_cost.value for component in components_list if hasattr(component, "installation_cost")])
    scalar_results["total annual running cost"] = sum([component.running_cost.value for component in components_list if hasattr(component, "running_cost")])
    scalar_results["calculation_time"] = calculation_time

    for model_object in pyomo_model.component_objects():
        cname = model_object.getname()
        ctype = type(model_object)

        if ctype in [pyomo.core.base.var.ScalarVar, pyomo.core.base.param.ScalarParam]:
            scalar_results[cname] = model_object.value

        elif ctype in [pyomo.core.base.param.IndexedParam, pyomo.core.base.var.IndexedVar]:
            values = pd.Series(model_object.extract_values())
            indexed_results[cname] = values

    with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
        scalar_results.to_excel(writer, sheet_name="Scalars")
        indexed_results.to_excel(writer, sheet_name="Indexed")

def generate_results_object(opt_model_object: OptModel, input: InputModel, components_list: List[Component], status: OptimizationStatus) -> OptimizationResultsModel:
    """Creates the complete `OptimizationResultsModel` which is returned as the response of the WattAdvisor.

    Parameters
    ----------
    opt_model_object : OptModel
        Object of the optimization model
    input : InputModel
        Input request given to the WattAdvisor
    components_list : List[Component]
        List of all optimization components added to the optimiziation model
    status : OptimizationStatus
        Status of the completed optimization

    Returns
    -------
    OptimizationResultsModel
        Object which contains all optimization results (cost, produced energy, power) for the WattAdvisor response
    """

    if status == OptimizationStatus.SUCCESS:

        target_scenario = _generate_scenario_results(opt_model_object.pyomo_model, components_list)
        current_scenario = _generate_current_scenario_results(opt_model_object, components_list)

        scenario_results = OptimizationResultsScenarios(
            target_scenario=target_scenario,
            current_scenario=current_scenario
        )

    else:
        scenario_results = None

    opt_results = OptimizationResultsModel(
        status=OptimizationResultsStatus(status=status),
        requested_input=input,
        results=scenario_results
    )

    return opt_results