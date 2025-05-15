"""Contains the base pydantic model all self-defined pydantic models are inherited from.

Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

from pydantic import BaseModel, ConfigDict


class BaseModelCustom(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )