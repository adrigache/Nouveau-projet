import pandas as pd
import datetime as dt
import numpy as np

from functools import cache
from typing import List, Callable

from mca_model import Model, Asset

from mca_model.service import  helpers

from mca_model.model.utils import (
    # f_activation,
    # zeros,
    log_number,
    # log_header,
    )

# # decorator function: transform list to tupless
# def list_to_tuple(func: Callable):
#     def wrapper(*args):
#         args = [tuple(x) if isinstance(x, list) else x for x in args]
#         result = func(*args)
#         result = tuple(result) if isinstance(result, list) else result
#         return result
#     return wrapper


# @list_to_tuple
# @cache
def _build(t:pd.DatetimeIndex, rates:dict[int, float], mod:str|float=1., start:dt.date|None=None):
    """
    use formats provided by toml
    make it monthly 
    HYPOTHESE: l'inflation commence en seconde année
    """

    assert(t.freq=='ME')
    assert(t.min().year in rates)
    assert(t.max().year in rates)

    s = pd.Series([None]*t.size, index=t)

    for y,r in rates.items():
        s[s.index.year==y] = helpers.transform_yearly_rate_to_monthly(1+r*mod, degradation=False)

    # no inflation on first year
    s[s.index.year==t.min().year] = 1

    # if start date ?
    if start:
        s[s.index<pd.to_datetime(start)] = 1

    # all values are filled
    assert(not s.isna().any().all())
    
    return s.cumprod()



def get_rate(m:Model, a:Asset):
    """"""
    return m.ipc_percentage[m.ipc_scenario.index(a.revenues_inflation)]


def get_rate_from_tag(m: Model, inflation_tag: str) -> float:
    """"""
    return m.ipc_percentage[m.ipc_scenario.index(inflation_tag)]


def compute_from_tag(m: Model, inflation_tag: str) -> pd.Series:
    """monthly inflation index from an IPC scenario tag (e.g. 'IPC', '20% IPC')"""

    modifier = get_rate_from_tag(m, inflation_tag)
    rates = {y: r for y, r in zip(m.ipc_years, m.ipc_base_rate)}
    return _build(m.time, rates, mod=modifier, start=m.inflation_start)


def _compound_from_year(m: Model) -> int:
    """
    First calendar year for which inflation compounds (index becomes > 1).
    Accepts either a date (dummy convention, e.g. 2026-01-01 -> 2026) or an int
    year in the Excel sense (K1535 = last year with index 1, e.g. 2025 -> 2026).
    Falls back to the second model year (Excel hypothesis: inflation starts year 2).
    """
    s = getattr(m, 'inflation_start', None)
    if s is None:
        return m.time.min().year + 1
    if hasattr(s, 'year'):
        return s.year
    try:
        return int(s) + 1
    except (TypeError, ValueError):
        return m.time.min().year + 1


def _build_annual(t: pd.DatetimeIndex, rates: dict[int, float], mod: float = 1.,
                  compound_from_year: int | None = None) -> pd.Series:
    """
    Annual-step inflation index (constant within each calendar year), matching Excel.
    index = 1 for years < compound_from_year, then compounded once per year by (1 + rate*mod).
    """
    assert t.freq == 'ME'

    if compound_from_year is None:
        compound_from_year = int(t.year.min()) + 1

    last_rate = rates[max(rates)]
    y_min, y_max = min(min(rates), int(t.year.min())), max(max(rates), int(t.year.max()))

    idx, cur = {}, 1.0
    for y in range(y_min, y_max + 1):
        r = rates.get(y, last_rate)
        if y < compound_from_year:
            cur = 1.0
        else:
            cur = cur * (1 + r * mod)
        idx[y] = cur

    values = pd.Series(t.year, index=t).map(idx).astype(float)
    assert not values.isna().any()
    return values


def compute_from_tag_annual(m: Model, inflation_tag: str) -> pd.Series:
    """
    Annual-step inflation index from an IPC scenario tag (e.g. 'IPC', '20% IPC').
    Reproduces the Excel OPEX convention: a single index value per calendar year,
    equal to 1 until inflation starts, then compounded yearly.
    """
    modifier = get_rate_from_tag(m, inflation_tag)
    rates = {y: r for y, r in zip(m.ipc_years, m.ipc_base_rate)}
    return _build_annual(m.time, rates, mod=modifier, compound_from_year=_compound_from_year(m))


def compute(m:Model, a:Asset):
    """FiT (PPA/CfD) inflation, exact, inflation mois par mois"""


    modifier = get_rate(m, a)
    rates = {y:r for y,r in zip(m.ipc_years, m.ipc_base_rate)}
    s = _build(m.time, rates, mod=modifier, start=m.inflation_start)

    log_number(f'inflation (key: {a.revenues_inflation})', f'{s.min()-1:.0%} to {s.max()-1:.0%}')

    # checks
    assert((s.diff()[1:]>=0).all())  # l'inflation n'est pas négative
    
    return s


