"""Contains the definition of a pydantic model which defines a structure of input and output variables/parameters
and their EnergyType of an optimization component of WattAdvisor

Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

from pydantic import Field, field_serializer

from ..data_models.enums import EnergyType
from ..data_models.base_model import BaseModelCustom
from pyomo.core.base import indexed_component


class BilanceVariables(BaseModelCustom):

    input: dict[EnergyType, indexed_component.IndexedComponent] = Field(
        default_factory=dict
    )
    output: dict[EnergyType, indexed_component.IndexedComponent] = Field(
        default_factory=dict
    )

    @field_serializer("input", "output")
    def _serialize(
        self, value: dict[EnergyType, indexed_component.IndexedComponent]
    ) -> dict[EnergyType, str]:
        return {key: x.name for key, x in value.items()}
