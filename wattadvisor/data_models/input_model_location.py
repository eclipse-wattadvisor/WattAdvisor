"""Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

from pydantic import BaseModel, Field


class InputModelLocation(BaseModel):
    longitude: float = Field(ge=5.86, le=14.86)
    latitude: float = Field(ge=47.27, le=55.02)