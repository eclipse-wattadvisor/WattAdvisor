from typing import Optional

from pydantic import BaseModel, Field

from .enums import OptimizationStatus


class OptimizationResultsStatus(BaseModel):
    status: OptimizationStatus
    error_message: Optional[str] = Field(default=None)