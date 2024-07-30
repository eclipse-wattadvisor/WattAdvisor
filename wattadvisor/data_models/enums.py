"""Contains several enum definitions to be used 
by the optimization model of WattAdvisor

Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

import enum

import wattadvisor.optimization_model.components.combined_heat_power as combined_heat_power
import wattadvisor.optimization_model.components.electrical_energy_storage as electrical_energy_storage
import wattadvisor.optimization_model.components.gas_boiler as gas_boiler
import wattadvisor.optimization_model.components.heat_pump as heat_pump
import wattadvisor.optimization_model.components.photovoltaik as photovoltaik
import wattadvisor.optimization_model.components.solarthemal_energy as solarthemal_energy
import wattadvisor.optimization_model.components.thermal_energy_storage as thermal_energy_storage
import wattadvisor.optimization_model.components.wind_power as wind_power


class EnergyType(enum.Enum):
    """Energy types usable by the optimization model
    
    """
    ELECTRICAL = "ELECTRICAL"
    THERMAL = "THERMAL"
    NATURAL_GAS = "NATURAL_GAS"

    def get_demand_component_title(self) -> str:
        """Returns the title of the energy type demand used in the input request.

        """
        component_titles = {
            EnergyType.ELECTRICAL: "electrical_energy_demand",
            EnergyType.THERMAL: "thermal_energy_demand",
            EnergyType.NATURAL_GAS: "natural_gas_demand"}
        
        return component_titles[self]
    
    def get_external_purchase_type(self):
        """Returns the purchase type of the energy type from the `PurchaseComponent` enum used in the input request.
        
        """
        purchase_types = {
            EnergyType.ELECTRICAL: PurchaseComponent.ELECTRICAL_ENERGY_PURCHASE,
            EnergyType.THERMAL: PurchaseComponent.THERMAL_ENERGY_PURCHASE,
            EnergyType.NATURAL_GAS: PurchaseComponent.NATURAL_GAS_PURCHASE}
        
        return purchase_types[self]
    
    def get_external_feedin_type(self):
        """Returns the feedin type of the energy type from the `FeedinComponent` enum used in the input request.
        
        """
        feedin_types = {
            EnergyType.ELECTRICAL: FeedinComponent.ELECTRICAL_ENERGY_FEEDIN,
            EnergyType.THERMAL: FeedinComponent.THERMAL_ENERGY_FEEDIN,
            EnergyType.NATURAL_GAS: FeedinComponent.NATURAL_GAS_FEEDIN}
        
        return feedin_types[self]


class Resolution(enum.Enum):
    """Time series resolution as defined by pandas

    """

    R1Y = "1Y"
    R1M = "1M"
    R1W = "1W"
    R1D = "1D"
    R1H = "1H"
    R15T = "15T"
    R1T = "1T"

class EnergyUnit(enum.Enum):
    """Accepted energy units

    """

    MWH = "MWH"
    KWH = "KWH"
    WH = "WH"

    def get_conversion_factor(self) -> float | int:
        """Returns the unit conversion factor to convert values into ``EnergyUnit.KWH``
        
        """
        conversion_factors = {
            EnergyUnit.MWH: 1000,
            EnergyUnit.KWH: 1,
            EnergyUnit.WH: 1e-3
        }

        return conversion_factors[self]

class PurchaseComponent(enum.Enum):
    """Purchase components used in the input request.

    """

    ELECTRICAL_ENERGY_PURCHASE = "ELECTRICAL_ENERGY_PURCHASE"
    THERMAL_ENERGY_PURCHASE = "THERMAL_ENERGY_PURCHASE"
    NATURAL_GAS_PURCHASE = "NATURAL_GAS_PURCHASE"

    def get_energy_type(self) -> EnergyType:
        """Returns the corresponding `EnergyType` of the purchase component.
        
        """

        energy_types = {
            PurchaseComponent.ELECTRICAL_ENERGY_PURCHASE: EnergyType.ELECTRICAL,
            PurchaseComponent.THERMAL_ENERGY_PURCHASE: EnergyType.THERMAL,
            PurchaseComponent.NATURAL_GAS_PURCHASE: EnergyType.NATURAL_GAS
            }

        return energy_types[self]

class FeedinComponent(enum.Enum):
    """Feedin components used in the input request.

    """

    ELECTRICAL_ENERGY_FEEDIN = "ELECTRICAL_ENERGY_FEEDIN"
    THERMAL_ENERGY_FEEDIN = "THERMAL_ENERGY_FEEDIN"
    NATURAL_GAS_FEEDIN = "NATURAL_GAS_FEEDIN"

    def get_energy_type(self):
        """Returns the corresponding `EnergyType` of the feedin component.
        
        """

        energy_types = {
            FeedinComponent.ELECTRICAL_ENERGY_FEEDIN: EnergyType.ELECTRICAL,
            FeedinComponent.THERMAL_ENERGY_FEEDIN: EnergyType.THERMAL,
            FeedinComponent.NATURAL_GAS_FEEDIN: EnergyType.NATURAL_GAS
            } 

        return energy_types[self]

class PowerUnitComponent(enum.Enum):
    """Energy components used in the input request which are defined by a 'power' field.

    """

    PHOTOVOLTAIK_ROOF = "PHOTOVOLTAIK_ROOF"
    PHOTOVOLTAIK_FREE_FIELD = "PHOTOVOLTAIK_FREE_FIELD"
    WIND_POWER = "WIND_POWER"
    COMBINED_HEAT_POWER = "COMBINED_HEAT_POWER"
    HEAT_PUMP_AIR = "HEAT_PUMP_AIR"
    HEAT_PUMP_GROUND = "HEAT_PUMP_GROUND"
    GAS_BOILER = "GAS_BOILER"

    def get_component_class(self):
        """Returns the corresponding optimization model component class of the component.
        
        """

        component_classes = {
            PowerUnitComponent.PHOTOVOLTAIK_ROOF: photovoltaik.PhotovoltaikRoof,
            PowerUnitComponent.PHOTOVOLTAIK_FREE_FIELD: photovoltaik.PhotovoltaikFreeField,
            PowerUnitComponent.WIND_POWER: wind_power.WindPower,
            PowerUnitComponent.COMBINED_HEAT_POWER: combined_heat_power.CombinedHeatPower,
            PowerUnitComponent.HEAT_PUMP_AIR: heat_pump.HeatPumpAir,
            PowerUnitComponent.HEAT_PUMP_GROUND: heat_pump.HeatPumpGround,
            PowerUnitComponent.GAS_BOILER: gas_boiler.GasBoiler}
        
        return component_classes[self]

class StorageComponent(enum.Enum):
    """Energy components used in the input request which are defined by a 'capacity' field.

    """

    ELECTRICAL_ENERGY_STORAGE = "ELECTRICAL_ENERGY_STORAGE"
    THERMAL_ENERGY_STORAGE = "THERMAL_ENERGY_STORAGE"

    def get_component_class(self):
        """Returns the corresponding optimization model component class of the component.
        
        """

        component_classes = {
            StorageComponent.ELECTRICAL_ENERGY_STORAGE: electrical_energy_storage.ElectricalEnergyStorage,
            StorageComponent.THERMAL_ENERGY_STORAGE: thermal_energy_storage.ThermalEnergyStorage}
        return component_classes[self]

    def get_energy_type(self) -> EnergyType:
        """Returns the corresponding `EnergyType` of the component.
        
        """

        energy_types = {
            StorageComponent.ELECTRICAL_ENERGY_STORAGE: EnergyType.ELECTRICAL,
            StorageComponent.THERMAL_ENERGY_STORAGE: EnergyType.THERMAL} 

        return energy_types[self]

class AreaUnitComponent(enum.Enum):
    """Energy components used in the input request which are defined by a 'area' field.

    """
    SOLARTHERMAL_ENERGY = "SOLARTHERMAL_ENERGY"

    def get_component_class(self):
        """Returns the corresponding optimization model component class of the component.
        
        """

        component_classes = {
            AreaUnitComponent.SOLARTHERMAL_ENERGY: solarthemal_energy.SolarthermalEnergy}
        
        return component_classes[self]

    def get_energy_type(self) -> EnergyType:
        """Returns the corresponding `EnergyType` of the component.
        
        """

        energy_types = {
            AreaUnitComponent.SOLARTHERMAL_ENERGY: EnergyType.THERMAL}
        
        return energy_types[self]

class EnergyPriceUnit(enum.Enum):
    """Accepted energy price units

    """

    EUR_PER_KWH = "EUR_PER_KWH"

class EnergyPurchaseTitle(enum.Enum):
    """Accepted energy purchase titles in the input request

    """

    ELECTRICAL = "ELECTRICAL_ENERGY_PURCHASE"
    THERMAL = "THERMAL_ENERGY_PURCHASE"
    NATURAL_GAS = "NATURAL_GAS_PURCHASE"

class OptimizationStatus(enum.Enum):
    """Optimization status titles used by the optimization result response

    """

    NEW = "NEW"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    UNBOUNDED = "UNBOUNDED"
    ERROR = "ERROR"

class SupportedSolver(enum.Enum):
    """Supported optimization solvers to be selected in the optimization model config

    """

    CBC = "cbc"
    HIGHS = "highs"
    GUROBI = "gurobi"

class WeatherDataLib(enum.Enum):
    """Supported libraries for weather data acquiring

    """
    PVLIB = "pvlib"
    TEMPERATURE = "temperature"
    WINDPOWERLIB = "windpowerlib"

class WeatherDataSource(enum.Enum):
    """Supported sources for weather data

    """
    CUSTOM_CSV = "custom_csv"
    ERA5_NETCDF = "era5_netcdf"