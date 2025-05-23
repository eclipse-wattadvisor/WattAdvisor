"""Contains the definition of a pydantic model
representing the status of an optimization.

Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

from pydantic import Field

from ..data_models.base_model import BaseModelCustom
from .enums import OptimizationStatus


class OptimizationResultsStatus(BaseModelCustom):
    status: OptimizationStatus
    error_message: None | str = Field(default=None)
