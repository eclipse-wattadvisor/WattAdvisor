"""Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

import logging
from functools import cached_property

from pydantic import Field, computed_field

from .component import Component

logger = logging.getLogger()


class InvestmentComponent(Component):
    """Base component from which all components that require an investment
    are inherited from.

    Parameters
    ----------
    lifespan : float
        Expected lifespan of the component [a]

    interest_rate : float
        Interest rate to determine annuity factor for investment calculation of the component

    """ 
       
    lifespan: float = Field(gt=0)
    interest_rate: float = Field(gt=0, default=0.03)

    @computed_field
    @cached_property
    def annuity_factor(self) -> float:
        """Calculates the annuity factor for investment calculation of the component.
        Uses class attributes interest rate and expected life span.

        Returns
        -------
        float
            calculated annuity factor for the component
        """

        return ((1 + self.interest_rate) ** self.lifespan * self.interest_rate) / ((1 + self.interest_rate) ** self.lifespan - 1)