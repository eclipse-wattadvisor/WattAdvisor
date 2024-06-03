"""Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

from typing import Optional

from pydantic import BaseModel, Field

from .enums import OptimizationStatus


class OptimizationResultsStatus(BaseModel):
    status: OptimizationStatus
    error_message: Optional[str] = Field(default=None)