"""Contains the defintion for pydantic models 
representing the WattAdvisor optimization model config.

Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

from pathlib import Path

from pydantic import BaseModel, Field, validator

from .enums import SupportedSolver, WeatherDataSource

class ConfigModelWeatherDataPathCsv(BaseModel):
    csv_solar: str
    csv_temperature: str
    csv_wind: str

    @validator("csv_solar", "csv_temperature", "csv_wind")
    def is_file(cls, v):
        path = Path(v)
        if not path.is_file():
            raise ValueError("Given path leads to no file!")
        return path

class ConfigModelWeatherDataPathNetcdf(BaseModel):
    netcdf: str

    @validator("netcdf")
    def is_file(cls, v):
        path = Path(v)
        if not path.is_file():
            raise ValueError("Given path leads to no file!")
        return path

class ConfigModelWeatherData(BaseModel):
    source: WeatherDataSource
    path: ConfigModelWeatherDataPathNetcdf | ConfigModelWeatherDataPathCsv

class ConfigModelLogging(BaseModel):
    version: int = Field(le=1, ge=1)
    formatters: dict | None
    handlers: dict
    loggers: dict
    root: dict | None

class ConfigModelSolver(BaseModel):
    use_solver: SupportedSolver
    timeout: int
    executable_path: str | None

class ConfigModel(BaseModel):
    solver: ConfigModelSolver
    default_interest_rate: float = Field(ge=0, lt=1)
    weather_data: ConfigModelWeatherData
    parameters_path: str
    logging: ConfigModelLogging | None
