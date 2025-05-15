"""Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

from __future__ import annotations
from datetime import datetime
from typing import List, TYPE_CHECKING
import logging
from pathlib import Path

import pandas as pd
import pyomo.core.base.param
import pyomo.core.base.var
from pyomo.core.base.PyomoModel import Model

from ..data_models.enums import OptimizationStatus
from ..data_models.enums import SupportedSolver
from ..data_models.optimization_results_model import OptimizationResults
from ..data_models.optimization_results_scenario_kpis import \
    OptimizationResultsScenarioKpis
from ..data_models.optimization_results_scenario import \
    OptimizationResultsScenario
from ..data_models.optimization_results_status import OptimizationResultsStatus
from ..components.component import Component
from ..components.investment_component import InvestmentComponent
if TYPE_CHECKING:
    from wattadvisor.opt_model import OptModel


logger = logging.getLogger()


def _generate_scenario_kpis(pyomo_model: Model, components_list: List[Component]) -> OptimizationResultsScenarioKpis:
    """Creates an `OptimizationResultsScenarioObject` for one scenario (target or current) which is returned as part of the response of the WattAdvisor.

    Parameters
    ----------
    pyomo_model : Model
        Pyomo optimization model containing all parameters, variables and constraints aswell as the objective function. 
    components_list : List[Component]
        List of all optimization components added to the optimiziation model

    Returns
    -------
    OptimizationResultsScenarioKpis
        Object containing the resulting total KPIs for one scenario (target or current)
    """

    total_co2_emissions = sum([component.co2_emissions for component in components_list if component.co2_emissions is not None])
    total_investment_cost = sum([component.investment_cost for component in components_list if component.investment_cost is not None])
    total_operational_cost = sum([component.operational_cost for component in components_list if component.operational_cost is not None])
    total_purchase_cost = sum([component.purchase_cost for component in components_list if component.purchase_cost is not None])
    total_income = -sum([component.feedin_income for component in components_list if component.feedin_income is not None])
    total_annuities = pyomo_model.Objective.expr()


    kpis = OptimizationResultsScenarioKpis(
        total_co2_emissions=total_co2_emissions,
        total_investment_cost=total_investment_cost,
        total_operational_cost=total_operational_cost,
        total_purchase_cost=total_purchase_cost,
        total_income=total_income,
        total_annuities=total_annuities
    )

    return kpis

def _generate_current_scenario_results(opt_model_object: OptModel, components_list: List[Component], use_solver: SupportedSolver, solver_executable: str | None = None) -> tuple[None | OptimizationResultsScenarioKpis, None | list[Component]]:
    """Determines the cost resulting for the fulfilment of the energy demands by the components already installed (current scenario). 

    Parameters
    ----------
    opt_model_object : OptModel
        Object of the optimization model
    components_list : List[Component]
        List of all optimization components added to the optimiziation model
    use_solver : SupportedSolver
        Solver to be used for the optimization for the current scenario
    solver_executable : str | None, optional
        Path of the solver's executable, by default None

    Returns
    -------
    tuple[None | OptimizationResultsScenarioKpis, None | list[Component]]
        If optimization of current scenario was feasible: Object containing the resulting total KPIs of the current scenario 
        and a list of all components used for the current scenario
        If optimization of current scenario was not feasible: tuple containing None and None is returned 
    """

    for component in components_list:
        if all(hasattr(component, attr) for attr in ["potential_power", "installed_power", "potential_capacity", "installed_capacity"]):
            # storage component
            variable = opt_model_object.pyomo_model.find_component(f"{component.name}_advised_capacity")
            if variable is not None:
                variable.fix(component.installed_capacity)

            if component.installed_power is not None:
                variable = opt_model_object.pyomo_model.find_component(f"{component.name}_advised_power")
                if variable is not None:
                    variable.fix(component.installed_power)
        
        elif all(hasattr(component, attr) for attr in ["potential_power", "installed_power"]):
            # power component
            variable = opt_model_object.pyomo_model.find_component(f"{component.name}_advised_power")
            if variable is not None:
                variable.fix(component.installed_power)   

        elif all(hasattr(component, attr) for attr in ["potential_area", "installed_area"]):
            # area component
            variable = opt_model_object.pyomo_model.find_component(f"{component.name}_advised_area")
            if variable is not None:
                variable.fix(component.installed_area)

    try:
        status, time = opt_model_object._optimize(solver=use_solver, solver_executable=solver_executable)

    except RuntimeError:
        logger.warning("Could not determine current scenario results. Probably given energy demand cannot be fulfilled by the existing components and tariffs.")
        return None, None
    
    if status != OptimizationStatus.SUCCESS:
        logger.warning("Could not determine current scenario results. Probably given energy demand cannot be fulfilled by the existing components and tariffs.")
        return None, None

    return _generate_scenario_kpis(opt_model_object.pyomo_model, components_list), components_list

def write_detailed_results(pyomo_model: Model, components_list: List[Component], calculation_time: float, filename: Path | None = None):
    """Creates a DataFrame with all optimization time series data and writes it to a excel file.

    Parameters
    ----------
    pyomo_model : Model
        Pyomo optimization model containing all parameters, variables and constraints aswell as the objective function. 
    components_list : List[Component]
        List of all optimization components added to the optimiziation model
    calculation_time : float
        Time in seconds it took for the solver to solve the optimization model
    filename : Path or None
        name of the Excel file to export, by default None
    """

    if filename is None:
        dt = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{dt}_results.xlsx"

    scalar_results = pd.Series()
    indexed_results = pd.DataFrame()

    scalar_results["Objective"] = pyomo_model.Objective.expr()
    scalar_results["total installation cost"] = sum([component.investment_cost for component in components_list if isinstance(component, InvestmentComponent)])
    scalar_results["total annual running cost"] = sum([component.operational_cost for component in components_list if isinstance(component, InvestmentComponent)])
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

def generate_results_object(opt_model_object: OptModel, components_list: List[Component], status: OptimizationStatus, use_solver: SupportedSolver, solver_executable: str | None = None) -> OptimizationResults:
    """Creates the complete `OptimizationResultsModel` which is returned as the response of the WattAdvisor.

    Returns
    -------
    OptimizationResultsModel
        Object which contains all optimization results (cost, produced energy, power) for the WattAdvisor response

    Parameters
    ----------
    opt_model_object : OptModel
        Object of the optimization model
    components_list : List[Component]
        List of all optimization components added to the optimiziation model
    status : OptimizationStatus
        Status of the completed optimization
    use_solver : SupportedSolver
        Solver to be used for the optimization for the current scenario
    solver_executable : str | None, optional
        Path of the solver's executable, by default None

    Returns
    -------
    OptimizationResults
        Object that contains all relevant results of current and target scenario optimization
    """    

    if status == OptimizationStatus.SUCCESS:

        kpis_target_scenario = _generate_scenario_kpis(opt_model_object.pyomo_model, components_list)

        target_scenario = OptimizationResultsScenario(
            components=[x.model_dump(exclude_none=True) for x in components_list],
            kpis=kpis_target_scenario
        )

        kpis_current_scenario, components_results_current_scenario = _generate_current_scenario_results(opt_model_object, components_list, use_solver, solver_executable)

        if kpis_current_scenario is None or components_results_current_scenario is None:
            results = OptimizationResults(
                status=OptimizationResultsStatus(status=status),
                target_scenario=target_scenario)
            
        else:
            current_scenario = OptimizationResultsScenario(
                components=[x.model_dump(exclude_none=True) for x in components_results_current_scenario],
                kpis=kpis_current_scenario
            )

            results =  OptimizationResults(
                status=OptimizationResultsStatus(status=status),
                current_scenario=current_scenario,
                target_scenario=target_scenario)

    else:
        results = OptimizationResults(status=OptimizationResultsStatus(status=status))

    return results