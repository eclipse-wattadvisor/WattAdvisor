"""Contains a dataclass which defines a structure of input and output variables/parameters 
and their EnergyType of an optimization component of WattAdvisor

Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..data_models import enums
    from pyomo.core.base import indexed_component 

@dataclass
class BilanceVariables:
    input: dict[enums.EnergyType, indexed_component.IndexedComponent] = field(default_factory=lambda: {})
    output: dict[enums.EnergyType, indexed_component.IndexedComponent] = field(default_factory=lambda: {})