"""Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

from pathlib import Path

import pandas as pd
import xarray as xr
from feedinlib import era5

from ...data_models.enums import WeatherDataSource, WeatherDataLib
from ...data_models.config_model import ConfigModelWeatherDataPathCsv, ConfigModelWeatherDataPathNetcdf

def get_weather_data(source: WeatherDataSource, 
                     path: ConfigModelWeatherDataPathCsv | ConfigModelWeatherDataPathNetcdf, 
                     longitude: None | float = None, 
                     latitude: None | float = None) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:

    if source == WeatherDataSource.ERA5_NETCDF:
        if not isinstance(path, ConfigModelWeatherDataPathNetcdf): 
            raise ValueError("Make sure to specify path to NETCDF file containing weather data in config file under 'weather_data' -> 'path' -> 'netcdf'")

        if longitude is None or latitude is None:
            raise ValueError("If weather data should be extracted from era5 file, location coordinates longitude and latitude are necessary and must not be None")

        location = [longitude, latitude]

        path = path.netcdf

        return (
            _get_weather_data_from_era5_file(path, location, WeatherDataLib.PVLIB),
            _get_weather_data_from_era5_file(path, location, WeatherDataLib.WINDPOWERLIB),
            _get_weather_data_from_era5_file(path, location, WeatherDataLib.TEMPERATURE)
        )
    elif source == WeatherDataSource.CUSTOM_CSV:
        if not isinstance(path, ConfigModelWeatherDataPathCsv): 
            raise ValueError("Make sure to specify path to CSV files containing weather data in config file under 'weather_data' -> 'path' -> 'csv_wind', 'csv_solar' and 'csv_temperature'")

        return (
            _get_weather_data_from_custom_csv_file(path.csv_solar, WeatherDataLib.PVLIB),
            _get_weather_data_from_custom_csv_file(path.csv_wind, WeatherDataLib.WINDPOWERLIB),
            _get_weather_data_from_custom_csv_file(path.csv_temperature, WeatherDataLib.TEMPERATURE)
        )

    else:
        raise ValueError(f"{source.value} is an unknown weather data source")
    
def _check_required_columns(required_columns: list[str], df: pd.DataFrame, path_df: Path) -> None:
    for required_column in required_columns:
        if isinstance(df.columns, pd.MultiIndex):
            if required_column not in df.columns.get_level_values(0):
                raise ValueError(f"Required column {required_column} missing in weather data from {path_df}.")
        else:
            if required_column not in df.columns:
                raise ValueError(f"Required column {required_column} missing in weather data from {path_df}.")

def _check_csv_length(df: pd.DataFrame, path_df: Path) -> None:
    if len(df) != 8760:
        raise ValueError(f"Covered time span by weather data from {path_df} is lower than 8760 hours.")
        
def _get_weather_data_from_custom_csv_file(file_path: Path, lib: WeatherDataLib) -> pd.DataFrame:
    """Reads weather data from a raw weather data NETCDF file obtained from ERA5 Climate Data Store. 

    Parameters
    ----------
    file_path : Path
        Path to the NETCDF file containing raw weather data from ERA5 Climate Data Store
    lib : WeatherDataLib
        Library to obtain weather data for

    Returns
    -------
    pd.DataFrame
        Weather data
    """

    if lib == WeatherDataLib.WINDPOWERLIB:
        header = [0, 1]
        required_columns = ["wind_speed", "roughness_length"]

    elif lib == WeatherDataLib.PVLIB:
        header = 0
        required_columns = ["ghi", "dhi"]

    elif lib == WeatherDataLib.TEMPERATURE:
        header = 0
        required_columns = ["t2m", "stl4"]

    weather_data = pd.read_csv(file_path, index_col=0, header=header, date_format="ISO8601")

    _check_required_columns(required_columns, weather_data, file_path)
    _check_csv_length(weather_data, file_path)

    return weather_data

def _get_weather_data_from_era5_file(file_path: Path, location: tuple[float, float], lib: WeatherDataLib) -> pd.DataFrame:
    """Reads weather data from a raw weather data NETCDF file obtained from ERA5 Climate Data Store. 

    Parameters
    ----------
    file_path : Path
        Path to the NETCDF file containing raw weather data from ERA5 Climate Data Store
    location : float
        location in the form (longitude, latitude) to obtain weather data for
    lib : WeatherDataLib
        Library to obtain weather data for

    Returns
    -------
    pd.DataFrame
        Weather data
    """

    if lib == WeatherDataLib.TEMPERATURE:
        ds = xr.open_dataset(file_path, engine="scipy")   

        ds = era5.select_area(ds, *location)


        weather_data = ds.to_dataframe().reset_index()  

        weather_data["time"] = weather_data.time - pd.Timedelta(minutes=60)
        weather_data.set_index(["time", "latitude", "longitude"], inplace=True)
        weather_data.index = weather_data.index.droplevel(level=[1, 2])
        weather_data.sort_index(inplace=True)
        weather_data = weather_data.tz_localize("UTC", level=0)
        weather_data = weather_data[["stl4", "t2m"]] - 273.15


    else:
        weather_data = era5.weather_df_from_era5(
            era5_netcdf_filename=file_path,
            lib=lib.value,
            area=location)

    return weather_data