from pathlib import Path

import pandas as pd
import xarray as xr
from feedinlib import era5

from ...data_models.enums import WeatherDataLib


def get_weather_data_from_file(file_path: Path, longitude: float, latitude: float, lib: WeatherDataLib) -> pd.DataFrame:
    """Reads weather data from a raw weather data NETCDF file obtained from ERA5 Climate Data Store. 

    Parameters
    ----------
    file_path : Path
        Path to the NETCDF file containing raw weather data from ERA5 Climate Data Store
    longitude : float
        longitude of the location to obtain weather data for
    latitude : float
        latitude of the location to obtain weather data for
    lib : WeatherDataLib
        Library to obtain weather data for

    Returns
    -------
    pd.DataFrame
        Weather data
    """

    single_location = [longitude, latitude] 

    if lib == WeatherDataLib.TEMPERATURE:
        ds = xr.open_dataset(file_path, engine="scipy")   

        ds = era5.select_area(ds, longitude, latitude)


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
            area=single_location)

    return weather_data