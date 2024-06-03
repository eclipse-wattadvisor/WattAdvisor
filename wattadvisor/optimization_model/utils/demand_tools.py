"""
    Contains functions to generate demand profiles
"""
import datetime
from typing import Literal

import demandlib.bdew as bdew
import holidays
import pandas as pd

from ...data_models.enums import Resolution


def _generate_holiday_calendar(year: int, country: str = "DE") -> dict[datetime.date, str]:
    """Generates a holiday calendar for a certain country and year.

    Parameters
    ----------
    year : int
        Year to generate the calendar for
    country : str, optional
        Country to generate the calendar for, by default "DE".
        See possible values at [holidays documentation](https://python-holidays.readthedocs.io/en/latest/#available-countries).

    Returns
    -------
    dict[datetime.date, str]
        Holiday calendar

    Raises
    ------
    ValueError
        If unknown country code is submitted
    """
    try:
        holidays_dict = holidays.country_holidays(country, years=year)
    except NotImplementedError:
        raise ValueError(f"Wrong Countrycode submitted. Calendar for Country '{country}' not found.")

    holidays_dict = dict(holidays_dict)

    return holidays_dict

def generate_electrical_demand_profile(
        demand_amount: float,
        demand_group: Literal["G0", "G1", "G2", "G3", "G4", "G5", "G6", "G7", "L0", "L1", "L2", "H0", "H0_dyn", "H0/H0_dyn"],
        year: int,
        target_resolution: Resolution=Resolution.R1H) -> pd.Series:
    """Generates an hourly electrical energy demand profile based on a yearly electrical energy demand sum. 

    Parameters
    ----------
    demand_amount : float
        Sum of the yearly electrical energy demand
    demand_group : Literal["G0", "G1", "G2", "G3", "G4", "G5", "G6", "G7", "L0", "L1", "L2", "H0", "H0_dyn", "H0/H0_dyn"]
        Demand group to generate the profile for. See [demandlib documention](https://demandlib.readthedocs.io/en/latest/bdew.html#id3) for an explanation of all possible values.
    year : int
        Year to generate the profile for
    target_resolution : Resolution, optional
        Time step resolution of the profile to be generated, by default Resolution.R1H

    Returns
    -------
    pd.Series
        Hourly electrical energy demand profile
    """
    
    demands = {
        demand_group: demand_amount
    }

    holidays = _generate_holiday_calendar(year)

    slp = bdew.ElecSlp(year, holidays=holidays)

    demand_profile = slp.get_profile(demands)[demand_group]

    demand_profile = demand_profile.resample(target_resolution.value).mean()

    return demand_profile


def generate_heat_demand_profile(
        demand_amount: float,
        demand_group: Literal["EFH", "MFH", "GMK", "GHA", "GKO", "GBD", "GGA", "GBH", "GWA", "GGB", "GBA", "GPD", "GMF", "GHD"],
        year: int,
        temperature_series: pd.Series,
        building_class: int = 0,
        wind_class: int = 0) -> pd.Series:
    """Generates an hourly heat demand profile based on a yearly heat demand sum.

    Parameters
    ----------
    demand_amount : float
        Sum of the yearly heat demand
    demand_group : Literal["EFH", "MFH", "GMK", "GHA", "GKO", "GBD", "GGA", "GBH", "GWA", "GGB", "GBA", "GPD", "GMF", "GHD"]
        Demand group to generate the profile for. See [demandlib documention](https://demandlib.readthedocs.io/en/latest/bdew.html#description) for an explanation of all possible values.
    year : int
        Year to generate the profile for
    temperature_series : pd.Series
        Base air temperature series [°C] for the location
    building_class : int, optional
        The parameter building_class (German: Baualtersklasse) can assume values in the range 1-11, by default 0
    wind_class : int, optional
        Influence of wind, by default 0

    Returns
    -------
    pd.Series
        hourly heat demand profile
    """
    holidays = _generate_holiday_calendar(year)

    index = pd.date_range(
        datetime.datetime(year, 1, 1, 0), datetime.datetime(year, 12, 31, 23), freq="H"
    )

    demand_profile = bdew.HeatBuilding(
        index,
        holidays=holidays,
        temperature=temperature_series,
        shlp_type=demand_group,
        wind_class=wind_class,
        annual_heat_demand=demand_amount,
        ww_incl=True,
        building_class=building_class
    ).get_bdew_profile()

    return demand_profile