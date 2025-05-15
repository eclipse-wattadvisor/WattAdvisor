"""Contains functions to load weather data from files into the internal format
of WattAdvisor.

Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

from pathlib import Path

import pandas as pd
import xarray as xr

from feedinlib import era5
from ..data_models.enums import WeatherDataSource
from ..data_models.weather_data import (
    WeatherDataCollection,
    WeatherDataHeightUnspecific,
    WeatherDataHeightSpecific,
    WeatherDataType,
)


def get_weather_data_from_era5_netcdf(
    path_netcdf: str | Path, longitude: float, latitude: float
) -> WeatherDataCollection:
    """Loads a NETCDF file aquired from ECMWF Climate Data Store
    into the WattAdvisor internal weather data format.

    Parameters
    ----------
    path_netcdf : str | Path
        Path of the NETCDF file containing weather data from ECMWF Climate Data Store
    longitude : float
        Longitude of the location for which weather data from the file should be extracted
    latitude : float
        Latitude of the location for which weather data from the file should be extracted

    Returns
    -------
    WeatherDataCollection
        Object containing a collection of different weather data variables such as wind speed, air temperature, etc.

    """

    location = [longitude, latitude]

    ds = xr.open_dataset(path_netcdf)
    ds = era5.select_area(ds, *location)

    weather_data_wind = era5.format_windpowerlib(ds)
    weather_data_wind.index = weather_data_wind.index.droplevel(level=[1, 2])
    weather_data_pv = era5.format_pvlib(ds)

    weather_data_pv.index = weather_data_pv.index.droplevel(level=[1, 2])
    weather_data_pv.index = weather_data_pv.index.shift(-30, freq="min")

    weather_data_temperature = ds.to_dataframe().reset_index()
    weather_data_temperature["time"] = weather_data_temperature.time - pd.Timedelta(
        minutes=60
    )
    weather_data_temperature.set_index(["time", "latitude", "longitude"], inplace=True)
    weather_data_temperature.index = weather_data_temperature.index.droplevel(
        level=[1, 2]
    )
    weather_data_temperature.sort_index(inplace=True)
    weather_data_temperature = weather_data_temperature.tz_localize("UTC", level=0)
    weather_data_temperature[["stl4", "t2m"]] = (
        weather_data_temperature[["stl4", "t2m"]] - 273.15
    )

    weather_data_collection = WeatherDataCollection(
        air_temperature=WeatherDataHeightSpecific(
            series=[weather_data_temperature["t2m"]],
            source=WeatherDataSource.ERA5_NETCDF,
            height_measured_at=[2],
            type=WeatherDataType.AIR_TEMPERATURE,
        ),
        soil_temperature=WeatherDataHeightUnspecific(
            series=weather_data_temperature["stl4"],
            source=WeatherDataSource.ERA5_NETCDF,
            type=WeatherDataType.SOIL_TEMPERATURE,
        ),
        wind_speed=WeatherDataHeightSpecific(
            series=[
                weather_data_wind["wind_speed"][height]
                for height in weather_data_wind["wind_speed"].columns
            ],
            source=WeatherDataSource.ERA5_NETCDF,
            height_measured_at=weather_data_wind["wind_speed"].columns.to_list(),
            type=WeatherDataType.WIND_SPEED,
        ),
        pressure=WeatherDataHeightSpecific(
            series=[
                weather_data_wind["pressure"][height]
                for height in weather_data_wind["pressure"].columns
            ],
            source=WeatherDataSource.ERA5_NETCDF,
            height_measured_at=weather_data_wind["pressure"].columns.to_list(),
            type=WeatherDataType.PRESSURE,
        ),
        roughness_length=WeatherDataHeightSpecific(
            series=[
                weather_data_wind["roughness_length"][height]
                for height in weather_data_wind["roughness_length"].columns
            ],
            source=WeatherDataSource.ERA5_NETCDF,
            height_measured_at=weather_data_wind["roughness_length"].columns.to_list(),
            type=WeatherDataType.ROUGHNESS_LENGTH,
        ),
        ghi=WeatherDataHeightUnspecific(
            series=weather_data_pv["ghi"],
            source=WeatherDataSource.ERA5_NETCDF,
            type=WeatherDataType.GHI,
        ),
        dhi=WeatherDataHeightUnspecific(
            series=weather_data_pv["dhi"],
            source=WeatherDataSource.ERA5_NETCDF,
            type=WeatherDataType.DHI,
        ),
    )

    return weather_data_collection


def get_weather_data_from_csv(
    path_wind_speed: str | None = None,
    path_roughness_length: str | None = None,
    path_pressure: str | None = None,
    path_density: str | None = None,
    path_ghi: str | None = None,
    path_dhi: str | None = None,
    path_dni: str | None = None,
    path_air_temperature: str | None = None,
    path_soil_temperature: str | None = None,
    path_water_temperature: str | None = None,
) -> WeatherDataCollection:
    """Loads weather data from CSV files into into the WattAdvisor internal weather data format.

    Parameters
    ----------
    path_wind_speed : str | None, optional
        path of a CSV file that contains wind speed measurements, by default None
    path_roughness_length : str | None, optional
        path of a CSV file that contains surface roughness length measurements, by default None
    path_pressure : str | None, optional
        path of a CSV file that contains air pressure measurements, by default None
    path_density : str | None, optional
        path of a CSV file that contains air density measurements, by default None
    path_ghi : str | None, optional
        path of a CSV file that contains global horizontal irradiance measurements, by default None
    path_dhi : str | None, optional
        path of a CSV file that contains diffuse horizontal irradiance measurements, by default None
    path_dni : str | None, optional
        path of a CSV file that contains direct normal irradiance measurements, by default None
    path_air_temperature : str | None, optional
        path of a CSV file that contains air temperature measurements, by default None
    path_soil_temperature : str | None, optional
        path of a CSV file that contains soil temperature measurements, by default None
    path_water_temperature : str | None, optional
        path of a CSV file that contains water temperature measurements, by default None

    Returns
    -------
    WeatherDataCollection
        Object containing a collection of different weather data variables such as wind speed, air temperature, etc.

    Raises
    ------
    ValueError
        Is raised if every parameter is None
    """

    params = [
        path_air_temperature,
        path_roughness_length,
        path_pressure,
        path_density,
        path_dhi,
        path_ghi,
        path_dni,
        path_soil_temperature,
        path_wind_speed,
    ]

    if all(param is None for param in params):
        raise ValueError(
            "Make sure to specify at least one path for a CSV file containing weather data."
        )

    weather_data_collection = WeatherDataCollection(
        air_temperature=_get_height_specific_weather_data_from_csv_file(
            path_air_temperature, WeatherDataType.AIR_TEMPERATURE
        ),
        soil_temperature=_get_height_unspecific_weather_data_from_csv_file(
            path_soil_temperature, WeatherDataType.SOIL_TEMPERATURE
        ),
        water_temperature=_get_height_unspecific_weather_data_from_csv_file(
            path_water_temperature, WeatherDataType.WATER_TEMPERATURE
        ),
        wind_speed=_get_height_specific_weather_data_from_csv_file(
            path_wind_speed, WeatherDataType.WIND_SPEED
        ),
        pressure=_get_height_specific_weather_data_from_csv_file(
            path_pressure, WeatherDataType.PRESSURE
        ),
        roughness_length=_get_height_specific_weather_data_from_csv_file(
            path_roughness_length, WeatherDataType.ROUGHNESS_LENGTH
        ),
        ghi=_get_height_unspecific_weather_data_from_csv_file(
            path_ghi, WeatherDataType.GHI
        ),
        dhi=_get_height_unspecific_weather_data_from_csv_file(
            path_dhi, WeatherDataType.DHI
        ),
        dni=_get_height_unspecific_weather_data_from_csv_file(
            path_dni, WeatherDataType.DNI
        ),
    )

    return weather_data_collection


def _get_height_specific_weather_data_from_csv_file(
    file_path: str | None, type: WeatherDataType
) -> WeatherDataHeightSpecific | None:
    """Loads weather data measured at a specific height above the ground from a single CSV file.

    Parameters
    ----------
    file_path : str | None
        Path to the CSV file containing weather data
    type : WeatherDataType
        Type of weather data which is contained in the CSV file

    Returns
    -------
    WeatherDataHeightSpecific | None
        Object containing the imported weather data or None if given `file_path` is None
    """

    if file_path is None:
        return None

    else:
        weather_data = pd.read_csv(
            file_path, index_col=0, header=0, date_format="ISO8601"
        )

        weather_data_series = [weather_data[column] for column in weather_data.columns]
        height_measured_at = weather_data.columns.tolist()

        weather_data = WeatherDataHeightSpecific(
            series=weather_data_series,
            source=WeatherDataSource.CUSTOM_CSV,
            height_measured_at=height_measured_at,
            type=type,
        )

        return weather_data


def _get_height_unspecific_weather_data_from_csv_file(
    file_path: str | None, type: WeatherDataType
) -> WeatherDataHeightUnspecific | None:
    """Loads weather data from a single CSV file.

    Parameters
    ----------
    file_path : str | None
        Path to the CSV file containing weather data
    type : WeatherDataType
        Type of weather data which is contained in the CSV file

    Returns
    -------
    WeatherDataHeightUnspecific | None
        Object containing the imported weather data or None if given `file_path` is None
    """

    if file_path is None:
        return None

    else:
        weather_data_series = pd.read_csv(
            file_path, index_col=0, header=0, date_format="ISO8601"
        ).squeeze()

        weather_data = WeatherDataHeightUnspecific(
            series=weather_data_series, source=WeatherDataSource.CUSTOM_CSV, type=type
        )

        return weather_data
