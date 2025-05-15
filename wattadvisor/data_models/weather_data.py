"""Contains the definition of pydantic models
representing weather data.

Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

from pydantic import Field, field_validator
from enum import Enum
import pandas as pd
from ..data_models.enums import WeatherDataSource
from .base_model import BaseModelCustom


class WeatherDataType(Enum):
    WIND_SPEED = "wind_speed"
    ROUGHNESS_LENGTH = "roughness_length"
    PRESSURE = "pressure"
    DENSITY = "density"
    GHI = "ghi"
    DHI = "dhi"
    DNI = "dni"
    AIR_TEMPERATURE = "air_temperature"
    SOIL_TEMPERATURE = "soil_temperature"
    WATER_TEMPERATURE = "water_temperature"


class WeatherDataHeightUnspecific(BaseModelCustom):

    series: pd.Series
    source: WeatherDataSource
    type: WeatherDataType

    @field_validator("series")
    @classmethod
    def check_time_series_length(cls, value: pd.Series) -> pd.Series:
        if len(value) != 8760:
            raise ValueError("Covered time span by weather data is not 8760 hours.")

        return value


class WeatherDataHeightSpecific(BaseModelCustom):

    series: list[pd.Series] = Field(min_length=1)
    source: WeatherDataSource
    height_measured_at: list[float] = Field(min_length=1)
    type: WeatherDataType

    @field_validator("series")
    @classmethod
    def check_time_series_length(cls, value: list[pd.Series]) -> list[pd.Series]:
        for series in value:
            if len(series) != 8760:
                raise ValueError("Covered time span by weather data is not 8760 hours.")

        return value

    def __init__(self, **data):
        super().__init__(**data)


class WeatherDataCollection(BaseModelCustom):

    wind_speed: WeatherDataHeightSpecific | None = None
    roughness_length: WeatherDataHeightSpecific | None = None
    pressure: WeatherDataHeightSpecific | None = None
    density: WeatherDataHeightSpecific | None = None
    ghi: WeatherDataHeightUnspecific | None = None
    dhi: WeatherDataHeightUnspecific | None = None
    dni: WeatherDataHeightUnspecific | None = None
    air_temperature: WeatherDataHeightSpecific | None = None
    soil_temperature: WeatherDataHeightUnspecific | None = None
    water_temperature: WeatherDataHeightUnspecific | None = None
