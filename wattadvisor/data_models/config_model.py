"""Contains the defintion for pydantic models 
representing the WattAdvisor optimization model config.
"""

from pathlib import Path

from pydantic import BaseModel, Field, validator

from .enums import SupportedSolver


class ConfigModelDataDependencies(BaseModel):
    weather: str
    parameters: str

    @validator("weather", "parameters")
    def is_file(cls, v):
        path = Path(__file__).parent.parent.joinpath("optimization_model").joinpath(v)
        if not path.is_file():
            raise ValueError("Given path leads to no file!")
        return path


class ConfigModelLogging(BaseModel):
    version: int = Field(le=1, ge=1)
    formatters: dict | None
    handlers: dict
    loggers: dict
    root: dict | None


class ConfigModel(BaseModel):
    solver: SupportedSolver
    solver_timeout: int
    default_interest_rate: float = Field(ge=0, lt=1)
    data_dependencies: ConfigModelDataDependencies
    logging: ConfigModelLogging | None
