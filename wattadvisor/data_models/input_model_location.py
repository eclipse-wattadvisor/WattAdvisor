from pydantic import BaseModel, Field


class InputModelLocation(BaseModel):
    longitude: float = Field(ge=5.86, le=14.86)
    latitude: float = Field(ge=47.27, le=55.02)