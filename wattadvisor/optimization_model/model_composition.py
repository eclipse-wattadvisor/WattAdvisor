import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
import pyomo.environ as pyoe
from pyomo.core.base.PyomoModel import Model
from pyomo.core.base.set import RangeSet
from pyomo.core.util import quicksum

import wattadvisor.data_models.enums as enums

from ..data_models.config_model import ConfigModel
from ..data_models.input_model import InputModel
from ..data_models.input_model_single_tariff_object import \
    InputModelSingleTariffObject
from .components.base import Component
from .components.energy_demand import EnergyDemand
from .components.energy_feedin import EnergyFeedin
from .components.energy_purchase import EnergyPurchase
from .utils.weather_data import WeatherDataLib, get_weather_data_from_file

logger = logging.getLogger()

def _generate_time_series(values: list[float], resolution: enums.Resolution) -> pd.Series:
    """Creates a pandas ``Series`` with a ``DateTimeIndex`` of a full year with the temporal resolution given by `resolution` and the values given by `values`.

    Parameters
    ----------
    values : list[float]
        Numerical values which the series should contain 
    resolution : enums.Resolution
        Temporal resolution of the given values

    Returns
    -------
    pd.Series[float]
        Time series containing the ``values`` with the given ``resolution`` for one year.

    Raises
    ------
    ValueError
        If number of values given by `values` is lower than the number of time intervals created by ``resolution`` for one year. 
    """

    index = pd.date_range(start=datetime(2022, 1, 1), end=datetime(2023, 1, 1), freq=resolution.value, inclusive="left")

    if len(values) > len(index):
        values = values[:len(index)]
        logger.debug("Ignored values in time series.")

    elif len(values) < len(index):
        error_msg = "Missing values in time series."
        logger.critical(error_msg)
        raise ValueError(error_msg)
    
    demand_profile = pd.Series(values, index=index)

    return demand_profile
    

def compose(input: InputModel, parameters: dict, config: ConfigModel, pyomo_model: Model, t: RangeSet, model_path: Path) -> tuple[Model, list[Component]]:
    """Adds all relevant components to the pyomo optimization model `pyomo_model` based on the parameterization in the input request `input` and creates the objective.

    Parameters
    ----------
    input : InputModel
        Input request containing the parameterization of the optimization model components
    parameters : dict
        Techno-economic data for the energy components
    config : ConfigModel
        Configuration of the optimization model
    pyomo_model : Model
        Pyomo model to add the components and objective to
    t : RangeSet
        Time set to use for variable, parameter and constraint creation
    model_path : Path
        Path of the model base directory

    Returns
    -------
    tuple[Model, list[Component]]
        The optimization model with all components added and a separate list of all component objects added to the model.

    Raises
    ------
    ValueError
        If for one energy type a demand but no production component is parameterized, the bilance for this energy type cannot be built
    """

    # add a list, for debug purposes, where certain components can be deactivated for the optimization
    # to not use a component set the value in the following dictionary to false

    weather_path = model_path.joinpath(config.data_dependencies.weather)
    weather_data_solar = get_weather_data_from_file(weather_path, input.location.longitude, input.location.latitude, WeatherDataLib.PVLIB)
    weather_data_wind = get_weather_data_from_file(weather_path, input.location.longitude, input.location.latitude, WeatherDataLib.WINDPOWERLIB)
    weather_data_temperature = get_weather_data_from_file(weather_path, input.location.longitude, input.location.latitude, WeatherDataLib.TEMPERATURE)

    if input.interest_rate is None:
        input.interest_rate = config.default_interest_rate
            
    counter_energy_demand_by_type = {x: 1 for x in enums.EnergyType}

    all_components_list = []

    for input_demand in input.energy_demands:

        resolution = input_demand.resolution
        values = input_demand.demand_values
        energy_type = input_demand.energy_type

        weather_temp_air_data = None
        profile_type = None
        demand_sum = None
        
        demand_profile = _generate_time_series(values, resolution)

        if resolution in [enums.Resolution.R15T, enums.Resolution.R1T]:
            demand_profile = demand_profile.resample(enums.Resolution.R1H.value).sum()
        
        elif resolution in [enums.Resolution.R1Y, enums.Resolution.R1M, enums.Resolution.R1W, enums.Resolution.R1D]:
            demand_sum = demand_profile.sum()
            demand_profile = None
            
            if energy_type == enums.EnergyType.ELECTRICAL:
                profile_type = "g0"

            elif energy_type in [enums.EnergyType.THERMAL, enums.EnergyType.NATURAL_GAS]:
                profile_type = "GBD"
                weather_temp_air_data = weather_data_temperature.t2m

        name = f"{energy_type.get_demand_component_title()}_{counter_energy_demand_by_type[energy_type]}" 
        component_instance = EnergyDemand(name, energy_type, demand_profile, demand_sum, profile_type, weather_temp_air_data)
        pyomo_model = component_instance.add_to_model(pyomo_model, t)

        all_components_list.append(component_instance)

        counter_energy_demand_by_type[energy_type] += 1
    
    if input.energy_components is not None:

        counter_energy_component_by_type = {x: 1 for x in [component for enum in [enums.StorageComponent, enums.PowerUnitComponent, enums.AreaUnitComponent] for component in enum]}

        for input_component in input.energy_components:
            
            external_component_type = input_component.component_type

            if external_component_type in enums.PowerUnitComponent and input_component.potential_power == 0:
                continue

            elif external_component_type in enums.AreaUnitComponent and input_component.potential_area == 0:
                continue

            elif external_component_type in enums.StorageComponent and input_component.potential_capacity == 0:
                continue 

            component_class = external_component_type.get_component_class()

            name = f"{external_component_type.value.lower()}_{counter_energy_component_by_type[external_component_type]}" 
            component_parameters = parameters[external_component_type.value]

            if external_component_type in [enums.PowerUnitComponent.PHOTOVOLTAIK_ROOF, enums.PowerUnitComponent.PHOTOVOLTAIK_FREE_FIELD]:
                component_instance = component_class(name, input.interest_rate, component_parameters, input.location.latitude, input.location.longitude, weather_data_solar, input_component.installed_power, input_component.potential_power, input_component.capex, input_component.opex, input_component.lifespan)

            elif external_component_type == enums.PowerUnitComponent.WIND_POWER:
                component_instance = component_class(name, input.interest_rate, component_parameters, input.location.latitude, input.location.longitude, weather_data_wind, input_component.installed_power, input_component.potential_power, input_component.capex, input_component.opex, input_component.lifespan)

            elif external_component_type == enums.PowerUnitComponent.HEAT_PUMP_AIR:
                component_instance = component_class(name, input.interest_rate, component_parameters, weather_data_temperature.t2m, input_component.installed_power, input_component.potential_power, input_component.capex, input_component.opex, input_component.lifespan)

            elif external_component_type == enums.PowerUnitComponent.HEAT_PUMP_GROUND:
                component_instance = component_class(name, input.interest_rate, component_parameters, weather_data_temperature.stl4, input_component.installed_power, input_component.potential_power, input_component.capex, input_component.opex, input_component.lifespan)

            elif external_component_type in enums.StorageComponent:
                component_instance = component_class(name, input.interest_rate, component_parameters, input_component.installed_capacity, input_component.installed_power, input_component.potential_capacity, input_component.potential_power, input_component.capex_power, input_component.capex_capacity, input_component.opex, input_component.lifespan)

            elif external_component_type in enums.AreaUnitComponent:
                component_instance = component_class(name, input.interest_rate, component_parameters, weather_data_solar, input_component.installed_area, input_component.potential_area, input_component.capex, input_component.opex, input_component.lifespan)            

            else:
                component_instance = component_class(name, input.interest_rate, component_parameters, input_component.installed_power, input_component.potential_power, input_component.capex, input_component.opex, input_component.lifespan)

            pyomo_model = component_instance.add_to_model(pyomo_model, t)
            all_components_list.append(component_instance)

            counter_energy_component_by_type[external_component_type] += 1

    if input.energy_tariffs is not None:
        if input.energy_tariffs.electrical_energy_purchase is not None:
            external_component_type = enums.PurchaseComponent.ELECTRICAL_ENERGY_PURCHASE
            pyomo_model, all_components_list = _add_purchase_component(pyomo_model, external_component_type, all_components_list, t, parameters, input.energy_tariffs.electrical_energy_purchase)

        if input.energy_tariffs.thermal_energy_purchase is not None:
            external_component_type = enums.PurchaseComponent.THERMAL_ENERGY_PURCHASE
            pyomo_model, all_components_list = _add_purchase_component(pyomo_model, external_component_type, all_components_list, t, parameters, input.energy_tariffs.thermal_energy_purchase)

        if input.energy_tariffs.natural_gas_purchase is not None:
            external_component_type = enums.PurchaseComponent.NATURAL_GAS_PURCHASE
            pyomo_model, all_components_list = _add_purchase_component(pyomo_model, external_component_type, all_components_list, t, parameters, input.energy_tariffs.natural_gas_purchase)

        if input.energy_tariffs.electrical_energy_feedin is not None:
            external_component_type = enums.FeedinComponent.ELECTRICAL_ENERGY_FEEDIN
            pyomo_model, all_components_list = _add_feedin_component(pyomo_model, external_component_type, all_components_list, t, parameters, input.energy_tariffs.electrical_energy_feedin)
    
    for energy_type in enums.EnergyType:

        bilance_vars_input = [x.bilance_variables.input.get(energy_type) for x in all_components_list if x.bilance_variables.input.get(energy_type) is not None]
        bilance_vars_output = [x.bilance_variables.output.get(energy_type) for x in all_components_list if x.bilance_variables.output.get(energy_type) is not None]

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

    objective_parts = [x.z for x in all_components_list if hasattr(x, 'z')]

    pyomo_model.add_component("Objective", pyoe.Objective(expr=
                quicksum(objective_parts),
                sense=pyoe.minimize))

    return pyomo_model, all_components_list


def _add_purchase_component(model: Model, component_type: enums.PurchaseComponent, all_components_list: list,  t: RangeSet, parameters: dict, purchase_data: InputModelSingleTariffObject) -> tuple[Model, list[Component]]:
    """Adds an energy purchase component to the given pyomo optimization model `model`

    Parameters
    ----------
    model : Model
        Pyomo optimization model the component should be added to
    component_type : enums.PurchaseComponent
        Type of the Purchase component
    all_components_list : list
        List of all components added to the `model` by then
    t : RangeSet
        Time set used by the opimization model
    parameters : dict
        techno-economic parameters for all energy components of the model
    purchase_data : InputModelSingleTariffObject
        Parameterization data for the new purchase component

    Returns
    -------
    tuple[Model, list[Component]]
        Pyomo model with the purchase component added and a list of all components added to the model.
    """
    
    power_price = purchase_data.power

    if purchase_data.energy is None:
        energy_price_profile = None
    else:
        resolution = purchase_data.energy.resolution
        values = purchase_data.energy.price_values

        if resolution == enums.Resolution.R1Y:
            energy_price_profile = None
            energy_price_scalar = values[0]

        else:
            energy_price_scalar = None
            energy_price_profile = _generate_time_series(values, resolution)
        
            if resolution in [enums.Resolution.R15T, enums.Resolution.R1T]:
                energy_price_profile = energy_price_profile.resample("1H").mean()
            
            elif resolution in [enums.Resolution.R1Y, enums.Resolution.R1M, enums.Resolution.R1W, enums.Resolution.R1D]:
                energy_price_profile = energy_price_profile.resample("1H").ffill()

    component_name = component_type.value
    energy_type = component_type.get_energy_type()
    parameters = parameters[component_name]
    component_instance = EnergyPurchase(component_name, parameters, energy_type, energy_price_scalar, energy_price_profile, power_price)
    model = component_instance.add_to_model(model, t)

    all_components_list.append(component_instance)

    
    return model, all_components_list

def _add_feedin_component(model: Model, component_type: enums.FeedinComponent, all_components_list: list, t: RangeSet, parameters: dict, purchase_data: InputModelSingleTariffObject):
    """Adds an energy feedin component to the given pyomo optimization model `model`

    Parameters
    ----------
    model : Model
        Pyomo optimization model the component should be added to
    component_type : enums.FeedinComponent
        Type of the feedin component
    all_components_list : list
        List of all components added to the `model` by then
    t : RangeSet
        Time set used by the opimization model
    parameters : dict
        techno-economic parameters for all energy components of the model
    purchase_data : InputModelSingleTariffObject
        Parameterization data for the new feedin component

    Returns
    -------
    tuple[Model, list[Component]]
        Pyomo model with the feedin component added and a list of all components added to the model.
    """
    
    power_price = purchase_data.power

    if purchase_data.energy is None:
        energy_price_profile = None
    else:
        resolution = purchase_data.energy.resolution
        values = purchase_data.energy.price_values

        if resolution == enums.Resolution.R1Y:
            energy_price_profile = None
            energy_price_scalar = values[0]

        else:
            energy_price_scalar = None
            energy_price_profile = _generate_time_series(values, resolution)
        
            if resolution in [enums.Resolution.R15T, enums.Resolution.R1T]:
                energy_price_profile = energy_price_profile.resample("1H").mean()
            
            elif resolution in [enums.Resolution.R1Y, enums.Resolution.R1M, enums.Resolution.R1W, enums.Resolution.R1D]:
                energy_price_profile = energy_price_profile.resample("1H").ffill()

    component_name = component_type.value
    energy_type = component_type.get_energy_type()
    parameters = parameters[component_name]
    component_instance = EnergyFeedin(component_name, parameters, energy_type, energy_price_scalar, energy_price_profile, power_price)
    model = component_instance.add_to_model(model, t)

    all_components_list.append(component_instance)

    return model, all_components_list