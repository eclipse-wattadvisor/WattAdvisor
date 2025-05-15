"""Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

import warnings
from typing import Literal

import pvlib
from feedinlib import Photovoltaic, WindPowerPlant
import pandas as pd

from ..data_models.weather_data import (
    WeatherDataHeightUnspecific,
    WeatherDataHeightSpecific,
)


warnings.filterwarnings("ignore")


def calculate_pv_feedin(
    ghi: WeatherDataHeightUnspecific,
    dhi: WeatherDataHeightUnspecific,
    latitude: float,
    longitude: float,
    azimuth: float,
    tilt: float,
    elevation: float,
    surface_type: Literal[
        "urban",
        "grass",
        "fresh grass",
        "soil",
        "sand",
        "snow",
        "fresh snow",
        "asphalt",
        "concrete",
        "aluminum",
        "copper",
        "fresh steel",
        "dirty steel",
        "sea",
    ],
    module_type: Literal["glass_glass", "glass_polymer"] = "glass_glass",
    racking_model: Literal[
        "open_rack", "close_mount", "insulated_back"
    ] = "insulated_back",
    air_temperature: WeatherDataHeightSpecific | None = None,
    dni: WeatherDataHeightUnspecific | None = None,
    normalized: bool = True,
) -> pd.Series:
    """Calculates the power generation profile of a photovoltaic plant at the given location using the given weather data DataFrame acquired before.

    Parameters
    ----------
    ghi : WeatherDataHeightUnspecific
        Object containing weather data describing the global horizontal irradiance at a location
    dhi : WeatherDataHeightUnspecific
        Object containing weather data describing the diffuse horizontal irradiance at a location
    latitude : float
        latitude of the location point for which the wind power generation should be calculated
    longitude : float
        longitude of the location point for which the wind power generation should be calculated
    azimuth : float
        azimuth orientation [°] of the photovoltaic plant where the power will be generated
        - North=0
        - East=90
        - South=180
        - West=270
    tilt : float
        tilt orientation [°] of the photovoltaic plant where the power will be generated
        - Up=0
        - horizon=90
    elevation : float
        elevation of the location of the photovoltaic plant above sea level [m]
    surface_type : Literal["urban", "grass", "fresh grass", "soil", "sand", "snow", "fresh snow", "asphalt", "concrete", "aluminum", "copper", "fresh steel", "dirty steel", "sea"]
        surface type of the surroundings of the photovoltaic plant where the power will be generated
    module_type : Literal["glass_glass", "glass_polymer"], optional
        Describes the module’s construction. Used for cell and module temperature calculations, by default "glass_glass"
    racking_model : Literal["open_rack", "close_mount", "insulated_back"], optional
        Used to identify a parameter set for the SAPM cell temperature model, by default "insulated_back"
    air_temperature : WeatherDataHeightSpecific | None, optional
        Object containing weather data describing the air temperature at a location, by default None
    dni : WeatherDataHeightUnspecific | None, optional
        Object containing weather data describing the direct normal irradiance at a location, by default None    
    normalized : bool, optional
        whether resulting power values should be normalized to installed power, by default True
    

    Returns
    -------
    pd.Series
        time series of power generation values for given weather data time series in `weather_data_df`
    """

    solpos = pvlib.solarposition.get_solarposition(
        ghi.series.index, latitude, longitude, elevation
    )

    if dni is None:
        dni = pvlib.irradiance.dni(ghi.series, dhi.series, solpos["zenith"])
    else:
        dni = dni.series

    system_data = {
        "module_name": "SolarWorld_Sunmodule_250_Poly__2013_",
        "inverter_name": "LG_Electronics_Inc___LG300A1C_B3__240V_",
        "azimuth": azimuth,
        "tilt": tilt,
        "surface_type": surface_type,
        "module_type": module_type,
        "racking_model": racking_model,
    }

    pv_system = Photovoltaic(**system_data)

    df_columns = [ghi.series, dhi.series, dni]
    df_names = ["ghi", "dhi", "dni"]

    if air_temperature is not None:
        df_columns.append(air_temperature.series[0])
        df_names.append("temp_air")

    weather_data_df = pd.concat(df_columns, axis=1, keys=df_names)

    feedin = pv_system.feedin(weather=weather_data_df, location=(latitude, longitude))

    feedin = feedin.fillna(0)

    if normalized:
        return feedin / pv_system.peak_power

    else:
        return feedin


def use_input_weather_data_wind(
    data_input: WeatherDataHeightSpecific | None,
    data_name: str,
    index_tuples: list | None = None,
    data_collected: list | None = None,
) -> tuple[list[tuple], list[pd.Series]]:
    """Transforms and adds a weather data object containing measurements at specific height into
    a tuple structure needed to use for energy generation determination with feedinlib.

    Parameters
    ----------
    data_input : WeatherDataHeightSpecific | None
        object containing weather data which is measured at specific, defined heights above the ground
    data_name : str
        identifier of the type of weather data (e.g., "air_temperature" or "pressure")
    index_tuples : list | None, optional
        list of other weather data to add the generated tuple structure of index values containing the data name and the height the data is measured at into, by default None
    data_collected : list | None, optional
        list of other weather data to add the generated tuple structure of measurement values into, by default None

    Returns
    -------
    tuple[list[tuple], list[pd.Series]]
        List of weather data tuples extended by the given weather data
    """
    if index_tuples is None:
        index_tuples = []

    if data_collected is None:
        data_collected = []

    if isinstance(data_input, WeatherDataHeightSpecific):
        index_tuples.extend(
            [(data_name, height) for height in data_input.height_measured_at]
        )
        data_collected.extend(data_input.series)

    return index_tuples, data_collected


def calculate_windpower_feedin(
    wind_speed: WeatherDataHeightSpecific,
    roughness_length: WeatherDataHeightSpecific,
    latitude: float,
    longitude: float,
    hub_height: float,
    air_temperature: WeatherDataHeightSpecific | None = None,
    pressure: WeatherDataHeightSpecific | None = None,
    density: WeatherDataHeightSpecific | None = None,
    normalized: bool = True,
) -> pd.Series:
    """Calculates the power generation profile of a wind power plant at the given location using the given weather data DataFrame acquired before.

    Parameters
    ----------
    wind_speed : WeatherDataHeightSpecific
        Object containing weather data describing the wind speed at a location
    roughness_length : WeatherDataHeightSpecific
        Object containing weather data describing the rougness length of the surrounding surface of a location
    latitude : float
        latitude of the location point for which the wind power generation should be calculated
    longitude : float
        longitude of the location point for which the wind power generation should be calculated
    hub_height : float
        height of the wind power plant hub where the power will be generated [m]
    air_temperature : WeatherDataHeightSpecific | None, optional
        Object containing weather data describing the air temperature at a location, by default None
    pressure : WeatherDataHeightSpecific | None, optional
        Object containing weather data describing the air pressure at a location, by default None
    density : WeatherDataHeightSpecific | None, optional
        Object containing weather data describing the air density at a location, by default None
    normalized : bool, optional
        whether resulting power values should be normalized to installed power, by default True

    Returns
    -------
    pd.Series
        time series of power generation values for given weather data
    """    

    index_tuples, data = use_input_weather_data_wind(wind_speed, "wind_speed")
    index_tuples, data = use_input_weather_data_wind(
        roughness_length, "roughness_length", index_tuples, data
    )
    index_tuples, data = use_input_weather_data_wind(
        air_temperature, "air_temperature", index_tuples, data
    )
    index_tuples, data = use_input_weather_data_wind(
        pressure, "pressure", index_tuples, data
    )
    index_tuples, data = use_input_weather_data_wind(
        density, "density", index_tuples, data
    )

    # use default wind power plant model
    turbine_data = {"turbine_type": "E-101/3050", "hub_height": hub_height}
    wind_turbine = WindPowerPlant(**turbine_data)

    new_columns = pd.MultiIndex.from_tuples(index_tuples, names=["variable", "height"])

    weather_data_df = pd.concat(data, axis=1)
    weather_data_df.columns = new_columns

    feedin = wind_turbine.feedin(
        weather=weather_data_df, location=(latitude, longitude)
    )

    feedin = feedin.fillna(0)

    if normalized == True:
        return feedin / wind_turbine.nominal_power

    else:
        return feedin
