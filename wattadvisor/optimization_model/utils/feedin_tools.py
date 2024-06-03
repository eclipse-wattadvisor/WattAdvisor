"""Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

import warnings
from datetime import datetime
from typing import Literal

import cdsapi
import pvlib
import requests
from feedinlib import Photovoltaic, WindPowerPlant, era5
import pandas as pd


warnings.filterwarnings("ignore")


def _download_era5_weather(
    latitude: float,
    longitude: float,
    start_date: datetime,
    end_date: datetime,
    cds_api_key: str,
    variable: Literal["feedinlib", "pvlib", "windpowerlib"],
) -> str:
    """Downloads weather data from ERA5 Climate Data Store source

    Parameters
    ----------
    latitude : float
        latitude of the location point for which weather data should be obtained
    longitude : float
        longitude of the location point for which weather data should be obtained
    start_date : datetime
        datetime of the first time interval of the time range for which weather data should be obtained
    end_date : datetime
        datetime of the last time interval of the time range for which weather data should be obtained
    cds_api_key : str
        key to access the ERA5 Climate Data Store, more information [here](https://cds.climate.copernicus.eu/api-how-to)
    variable : Literal["feedinlib", "pvlib", "windpowerlib"]
        defines for which type of power plant weather data should be obtained

    Returns
    -------
    str
        path to netCDF file containing raw weather data
    """
    # download weather data

    fmt = "%Y-%m-%d"

    start_date_str = start_date.strftime(fmt)
    end_date_str = end_date.strftime(fmt)

    path_era5_file = f"era5_weather_{start_date}_{end_date}_{latitude}_{longitude}"

    cds_client = cdsapi.api.Client(
        url="https://cds.climate.copernicus.eu/api/v2", key=cds_api_key
    )

    era5.get_era5_data_from_datespan_and_position(
        start_date_str,
        end_date_str,
        path_era5_file,
        variable=variable,
        latitude=latitude,
        longitude=longitude,
        cds_client=cds_client,
    )

    return path_era5_file


def _calculate_pv_feedin(
    weather_data_df: pd.DataFrame,
    latitude: float,
    longitude: float,
    azimuth: float,
    tilt: float,
    surface_type: Literal["urban", "grass", "fresh grass", "soil", "sand", "snow", "fresh snow", "asphalt", "concrete", "aluminum", "copper", "fresh steel", "dirty steel", "sea"],
    normalized: bool = True,
    elevation: float | None = None,
) -> pd.Series:
    """Calculates the power generation profile of a photovoltaic plant at the given location using the given weather data DataFrame acquired before.

    Parameters
    ----------
    weather_data_df : pd.DataFrame
        DataFrame with weather data time series to calculate the power output. 
    Use `_download_era5_weather(latitude, longitude, start_date, end_date, cds_api_key, variable="pvlib")` to aqcuire these
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

    surface_type : Literal["urban", "grass", "fresh grass", "soil", "sand", "snow", "fresh snow", "asphalt", "concrete", "aluminum", "copper", "fresh steel", "dirty steel", "sea"]
        surface type of the surroundings of the photovoltaic plant where the power will be generated.
    normalized : bool, optional
        whether resulting power values should be normalized to installed power, by default True
    elevation : float | None, optional
        elevation of the location of the photovoltaic plant above sea level [m], by default None

    Returns
    -------
    pd.Series
        time series of power generation values for given weather data time series in `weather_data_df`
    """

    if elevation is None:
        # call separate api to get elevation (height) of location
        url = (
            f"https://api.opentopodata.org/v1/eudem25m?locations={latitude},{longitude}"
        )

        response = requests.get(url)
        elevation = response.json()["results"][0]["elevation"]

    solpos = pvlib.solarposition.get_solarposition(
        weather_data_df.index, latitude, longitude, elevation
    )

    weather_data_df["dni"] = pvlib.irradiance.dni(
        weather_data_df["ghi"], weather_data_df["dhi"], solpos["zenith"]
    )

    system_data = {
        "module_name": "SolarWorld_Sunmodule_250_Poly__2013_",
        "inverter_name": "LG_Electronics_Inc___LG300A1C_B3__240V_",
        "azimuth": azimuth,
        "tilt": tilt,
        "surface_type": surface_type,  # The ground surface type
        "module_type": "glass_glass",  # Describes the module's construction. Valid strings are 'glass_polymer' and 'glass_glass'. Used for cell and module temperature calculations.
        "racking_model": "insulated_back",
    }  # Valid strings are 'open_rack', 'close_mount', and 'insulated_back'. Used to identify a parameter set for the SAPM cell temperature model.

    pv_system = Photovoltaic(**system_data)

    feedin = pv_system.feedin(weather=weather_data_df, location=(latitude, longitude))

    feedin = feedin.fillna(0)

    if normalized == True:
        return feedin / pv_system.peak_power

    else:
        return feedin


def pv_normed_feedin_from_era5(
    latitude: float,
    longitude: float,
    azimuth: float,
    tilt: float,
    surface_type: Literal["urban", "grass", "fresh grass", "soil", "sand", "snow", "fresh snow", "asphalt", "concrete", "aluminum", "copper", "fresh steel", "dirty steel", "sea"],
    start_date: datetime,
    end_date: datetime,
    cds_api_key: str | None = None,
    path_era5_file: str | None = None,
    pvlib_df: pd.DataFrame | None = None,
    path_export_csv: str | None = None,
    normalized: bool = True,
    elevation: float | None = None,
) -> pd.Series:
    
    """Calculates photovoltaic power plant generation profile for a certain location and time range by
    using weather data from ERA5 Climate Data Store, either downloaded by this function or downloaded before

    Parameters
    ----------
    latitude : float
        latitude of the location point for which the wind power generation should be calculated
    longitude : float
        longitude of the location point for which the wind power generation should be calculated
    azimuth : float
        azimuth orientation [°] of the photovoltaic plant where the power will be generated
        * North=0
        * East=90
        * South=180
        * West=270

    tilt : float
        tilt orientation [°] of the photovoltaic plant where the power will be generated
        * Up=0
        * horizon=90

    surface_type : Literal["urban", "grass", "fresh grass", "soil", "sand", "snow", "fresh snow", "asphalt", "concrete", "aluminum", "copper", "fresh steel", "dirty steel", "sea"]
        surface type of the surroundings of the photovoltaic plant where the power will be generated.

    start_date : datetime
        datetime of the first time interval of the time range for which the photovoltaic power generation should be calculated
    end_date : datetime
        datetime of the last time interval of the time range for which the photovoltaic power generation should be calculated
    cds_api_key : str | None, optional
        key to access the ERA5 Climate Data Store, more information [here](https://cds.climate.copernicus.eu/api-how-to), by default None
    path_era5_file : str | None, optional
        path to a file with raw weather data from the climate data store, if already downloaded before, by default None
    pvlib_df : pd.DataFrame | None, optional
        DataFrame with already generated weather data for photovoltaic power generation from raw weather data from the climate data store, if already downloaded before, by default None
    path_export_csv : str | None, optional
        path to CSV file to write the resulted generation time series to, by default None
    normalized : bool, optional
        whether resulting power values should be normalized to installed power, by default True
    elevation : float | None, optional
        elevation of the location of the photovoltaic plant above sea level [m], by default None

    Returns
    -------
    pd.Series
       time series of power generation values for each hourly time interval in the range between `start_date` and `end_date`

    Raises
    ------
    ValueError
        if `pvlib_df`, `path_era5_file` and key for climate date store `cds_api_key` are not provided
    """

    if pvlib_df is None:
        if path_era5_file is None:
            if cds_api_key is None:
                raise Exception("Key to download ERA5 weather must be provided!")
            else:
                path_era5_file = _download_era5_weather(
                    latitude, longitude, start_date, end_date, cds_api_key, "pvlib"
                )

        single_location = [longitude, latitude]

        # get weather data in windpowerlib format for all locations in netcdf file
        pvlib_df = era5.weather_df_from_era5(
            era5_netcdf_filename=path_era5_file, lib="pvlib", area=single_location
        )

    feedin_norm = _calculate_pv_feedin(
        pvlib_df,
        latitude,
        longitude,
        azimuth,
        tilt,
        surface_type,
        normalized,
        elevation=elevation,
    )

    if path_export_csv is not None:
        feedin_norm.to_csv(path_export_csv)

    return feedin_norm


def _calculate_windpower_feedin(
    weather_data_df: pd.DataFrame, latitude: float, longitude: float, hub_height: float, normalized: bool = True
) -> pd.Series:
    """Calculates the power generation profile of a wind power plant at the given location using the given weather data DataFrame acquired before.

    Parameters
    ----------
    weather_data_df : pd.DataFrame
        DataFrame with weather data time series to calculate the power output. 
        Use `_download_era5_weather(latitude, longitude, start_date, end_date, cds_api_key, variable="windpowerlib")` to aqcuire these
    latitude : float
        latitude of the location point for which the wind power generation should be calculated
    longitude : float
        longitude of the location point for which the wind power generation should be calculated
    hub_height : float
        height of the wind power plant hub where the power will be generated [m]
    normalized : bool, optional
        whether resulting power values should be normalized to installed power, by default True

    Returns
    -------
    pd.Series
        time series of power generation values for given weather data time series in `weather_data_df`
    """

    # use default wind power plant model
    turbine_data = {"turbine_type": "E-101/3050", "hub_height": hub_height}
    wind_turbine = WindPowerPlant(**turbine_data)

    feedin = wind_turbine.feedin(
        weather=weather_data_df, location=(latitude, longitude)
    )

    feedin = feedin.fillna(0)

    if normalized == True:
        return feedin / wind_turbine.nominal_power

    else:
        return feedin


def windpower_normed_feedin_from_era5(
    latitude: float,
    longitude: float,
    hub_height: float,
    start_date: datetime,
    end_date: datetime,
    cds_api_key: str | None = None,
    path_era5_file: str | None = None,
    windpowerlib_df: pd.DataFrame | None = None,
    path_export_csv: str | None = None,
    normalized: bool = True,
) -> pd.Series:
    """Calculates wind power plant generation profile for a certain location and time range by
    using weather data from ERA5 Climate Data Store, either downloaded by this function or downloaded before

    Parameters
    ----------
    latitude : float
        latitude of the location point for which the wind power generation should be calculated
    longitude : float
        longitude of the location point for which the wind power generation should be calculated
    hub_height : float
        height of the wind power plant hub where the power will be generated [m]
    start_date : datetime
        datetime of the first time interval of the time range for which the wind power generation should be calculated
    end_date : datetime
        datetime of the last time interval of the time range for which the wind power generation should be calculated
    cds_api_key : str | None, optional
        key to access the ERA5 Climate Data Store, more information [here](https://cds.climate.copernicus.eu/api-how-to), by default None
    path_era5_file : str | None, optional
        path to a file with raw weather data from the climate data store, if already downloaded before, by default None
    windpowerlib_df : pd.DataFrame | None, optional
        DataFrame with already generated weather data for windpower from raw weather data from the climate data store, if already downloaded before, by default None
    path_export_csv : str | None, optional
        path to CSV file to write the resulted generation time series to, by default None
    normalized : bool, optional
        whether resulting power values should be normalized to installed power, by default True

    Returns
    -------
    pd.Series
        time series of power generation values for each hourly time interval in the range between `start_date` and `end_date`

    Raises
    ------
    ValueError
        if `windpowerlib_df`, `path_era5_file` and key for climate date store `cds_api_key` are not provided
    """
    if windpowerlib_df is None:
        if path_era5_file is None:
            if cds_api_key is None:
                raise ValueError("Key to download ERA5 weather must be provided!")
            else:
                path_era5_file = _download_era5_weather(
                    latitude, longitude, start_date, end_date, cds_api_key, "windpowerlib"
                )

        single_location = [longitude, latitude]

        # get weather data in windpowerlib format for all locations in netcdf file
        windpowerlib_df = era5.weather_df_from_era5(
            era5_netcdf_filename=path_era5_file, lib="pvlib", area=single_location
        )

    feedin_norm = _calculate_windpower_feedin(
        windpowerlib_df, latitude, longitude, hub_height, normalized
    )

    if path_export_csv is not None:
        feedin_norm.to_csv(path_export_csv)

    return feedin_norm