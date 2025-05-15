"""Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

import logging

from ..data_models.enums import EnergyType
from .component import Component


logger = logging.getLogger()


class NonInvestmentComponent(Component):
    """Base component from which all components that do not require
    an investment are inherited from.

    Parameters
    ----------
    energy_type: EnergyType 
        Energy type the component produces or consumes

    """ 

    energy_type: EnergyType 