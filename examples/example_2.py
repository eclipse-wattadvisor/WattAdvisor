"""This module runs a single WattAdvisor 
optimization by using a static JSON file as input.
Results are exported as JSON file containing the response body
and as an Excel file containing all detailed time series data.

Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

from pprint import pprint

import sys
sys.path.append("../wattadvisor")

import pandas as pd

from wattadvisor.optimization_model import run_optimization
from wattadvisor.data_models.input_model import InputModel
from wattadvisor.data_models.input_model_location import InputModelLocation
from wattadvisor.data_models.input_model_demand_object import InputModelDemandObject
from wattadvisor.data_models.input_model_energy_tariffs import InputModelEnergyTariffs
from wattadvisor.data_models.input_model_component_object import InputModelComponentPower
from wattadvisor.data_models.input_model_component_normed_production_object import NormedProduction
from wattadvisor.data_models.input_model_single_tariff_object import InputModelSingleTariffObject
from wattadvisor.data_models.input_model_single_tariff_energy_object import InputModelSingleTariffEnergyObject
from wattadvisor.data_models.enums import EnergyType, Resolution, EnergyUnit, PowerUnitComponent, EnergyPriceUnit

if __name__ == "__main__": 

    location = InputModelLocation(
        longitude=10,
        latitude=50
    )

    energy_demands = [
        InputModelDemandObject(
            demand_values = [10000],
            resolution=Resolution.R1Y,
            unit=EnergyUnit.KWH,
            energy_type=EnergyType.ELECTRICAL
        )
    ]

    energy_components = [
        InputModelComponentPower(
            component_type=PowerUnitComponent.PHOTOVOLTAIK_ROOF,
            installed_power=0,
            potential_power=20,
            normed_production=NormedProduction(
                resolution=Resolution.R1H,
                unit=EnergyUnit.WH,
                production_values=pd.read_csv(
                    'examples/normed_production_pv.csv',
                    index_col=0,
                    date_format="%Y%m%d:%H%M",
                    nrows=8760,
                    usecols=[0, 1]).squeeze().to_list()  
            )
        )
    ]

    electrical_energy_purchase = InputModelSingleTariffObject(
        energy=InputModelSingleTariffEnergyObject(
            price_values=[0.35],
            resolution=Resolution.R1Y,
            unit=EnergyPriceUnit.EUR_PER_KWH
        )
    )

    energy_tariffs = InputModelEnergyTariffs(
        electrical_energy_purchase=electrical_energy_purchase
    )

    new_input = InputModel(
        location=location,
        energy_demands=energy_demands,
        energy_components=energy_components,
        energy_tariffs=energy_tariffs
    )


    # use 'export=True' to create an Excel file of detailed results and time series to inspect
    results = run_optimization.run(new_input, export_detailed_results=True)

    pprint(results.dict())

    pprint(results.results.target_scenario.components)

    with open("results.json", "w") as file:
        file.write(results.json(exclude_none=True, indent=4))
