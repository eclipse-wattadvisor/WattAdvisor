from typing import Literal

import pandas as pd


def calc_cops(mode: Literal["heat_pump", "chiller"], temp_high: list | pd.Series, temp_low: list | pd.Series, quality_grade: float, temp_threshold_icing: float = 2,
              factor_icing: float | None = None) -> list:

    r"""
    Calculates the Coefficient of Performance (COP) of heat pumps and chillers
    based on the Carnot efficiency (ideal process) and a scale-down factor.
    This function is part of project oemof (github.com/oemof/oemof-thermal). It's copyrighted
    by the contributors recorded in the version control history of the file,
    available from its original location:
    https://github.com/oemof/oemof-thermal/blob/17761c4d9c768d0f3aab023509a72aa27a6bf11c/src/oemof/thermal/compression_heatpumps_and_chillers.py

    SPDX-License-Identifier: MIT

    ``mode`` = "heat_pump":

        :math:`COP = \eta\cdot\frac{T_\mathrm{high}}{T_\mathrm{high}-T_\mathrm{low}}`

        :math:`COP = f_\mathrm{icing}\cdot\eta\cdot\frac{T_\mathrm{high}}{T_\mathrm{high}-T_\mathrm{low}}`

    ``mode`` = "chiller":

        :math:`COP = \eta\cdot\frac{T_\mathrm{low}}{T_\mathrm{high}-T_\mathrm{low}}`

    Note
    ----
    Applications of air-source heat pumps should consider icing
    at the heat exchanger at air-temperatures around 2 [°C].
    Icing causes a reduction of the efficiency.

    Parameters
    ----------
    temp_high : list or pandas.Series of numerical values
        Temperature of the high temperature reservoir [°C]
    temp_low : list or pandas.Series of numerical values
        Temperature of the low temperature reservoir [°C]
    quality_grade : numerical value
        Factor that scales down the efficiency of the real heat pump
        (or chiller) process from the ideal process (Carnot efficiency), where
        a factor of 1 means the real process is equal to the ideal one.
    factor_icing: numerical value
        Sets the relative COP drop caused by icing, where 1 stands for no
        efficiency-drop.
    mode : Literal["heat_pump", "chiller"]
        Two possible modes: "heat_pump" or "chiller"
    t_threshold:
        Temperature [°C] below which icing at heat exchanger
        occurs (default 2)

    Returns
    -------
    cops : list of numerical values
        List of Coefficients of Performance (COPs)


    """
    # Check if input arguments have proper type and length
    if not isinstance(temp_low, (list, pd.Series)):
        raise TypeError("Argument 'temp_low' is not of type list or pd.Series!")

    if not isinstance(temp_high, (list, pd.Series)):
        raise TypeError("Argument 'temp_high' is not of "
                        "type list or pd.Series!")

    if len(temp_high) != len(temp_low):
        if (len(temp_high) != 1) and ((len(temp_low) != 1)):
            raise IndexError("Arguments 'temp_low' and 'temp_high' "
                             "have to be of same length or one has "
                             "to be of length 1 !")

    # if factor_icing is not None and consider_icing is False:
    #     raise ValueError('Argument factor_icing can not be used without '
    #                      'setting consider_icing=True!')
    #
    # if factor_icing is None and consider_icing is True:
    #     raise ValueError('Icing cannot be considered because argument '
    #                      'factor_icing has value None!')

    # Make temp_low and temp_high have the same length and
    # convert unit to Kelvin.
    length = max([len(temp_high), len(temp_low)])
    if len(temp_high) == 1:
        list_temp_high_K = [temp_high[0] + 273.15] * length
    elif len(temp_high) == length:
        list_temp_high_K = [t + 273.15 for t in temp_high]
    if len(temp_low) == 1:
        list_temp_low_K = [temp_low[0] + 273.15] * length
    elif len(temp_low) == length:
        list_temp_low_K = [t + 273.15 for t in temp_low]

    # Calculate COPs depending on selected mode (without icing).
    if factor_icing is None:
        if mode == "heat_pump":
            cops = [quality_grade * t_h / (t_h - t_l) for
                    t_h, t_l in zip(list_temp_high_K, list_temp_low_K)]
        elif mode == "chiller":
            cops = [quality_grade * t_l / (t_h - t_l) for
                    t_h, t_l in zip(list_temp_high_K, list_temp_low_K)]

    # Calculate COPs of a heat pump and lower COP when icing occurs.
    elif factor_icing is not None:
        if mode == "heat_pump":
            cops = []
            for t_h, t_l in zip(list_temp_high_K, list_temp_low_K):
                if t_l < temp_threshold_icing + 273.15:
                    f_icing = factor_icing
                    cops = cops + [f_icing * quality_grade * t_h / (t_h - t_l)]
                if t_l >= temp_threshold_icing + 273.15:
                    cops = cops + [quality_grade * t_h / (t_h - t_l)]
        elif mode == "chiller":
            raise ValueError("Argument 'factor_icing' has "
                             "to be None for mode='chiller'!")
    return cops
