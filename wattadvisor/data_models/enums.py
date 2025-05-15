"""Contains several enum definitions to be used 
by the optimization model of WattAdvisor

Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

import enum

class EnergyType(enum.Enum):
    """Energy types usable by the optimization model
    
    """
    ELECTRICAL = "ELECTRICAL"
    THERMAL = "THERMAL"
    NATURAL_GAS = "NATURAL_GAS"
    COOLING = "COOLING"
    SOLID_FUEL = "SOLID_FUEL"


class Resolution(enum.Enum):
    """Time series resolution as defined by pandas

    """

    R1Y = "1Y"
    R1M = "1M"
    R1W = "1W"
    R1D = "1D"
    R1H = "1h"
    R15T = "15min"
    R1T = "1min"

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

class WeatherDataType(enum.Enum):
    air_temperature_2meters = "AIR_TEMPERATURE_2METERS"
    soil_temperature_level4 = "SOIL_TEMPERATURE_LEVEL4"
    wind_speed_10meters = "WIND_SPEED_10METERS"
    wind_speed_100meters = "WIND_SPEED_100METERS"
    pressure_0meters = "PRESSURE_0METERS"
    roughness_length = "ROUGHNESS_LENGTH"
    global_horizontal_irradiance = "GLOBAL_HORIZONTAL_IRRADIANCE"
    diffuse_horizontal_irradiance = "DIFFUSE_HORIZONTAL_IRRADIANCE"

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