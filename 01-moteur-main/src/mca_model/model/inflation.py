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
    

def compute(m:Model, a:Asset):
    """FiT (PPA/CfD) inflation, exact, inflation mois par mois"""


    modifier = get_rate(m, a)
    rates = {y:r for y,r in zip(m.ipc_years, m.ipc_base_rate)}
    s = _build(m.time, rates, mod=modifier, start=m.inflation_start)

    log_number(f'inflation (key: {a.revenues_inflation})', f'{s.min()-1:.0%} to {s.max()-1:.0%}')

    # checks
    assert((s.diff()[1:]>=0).all())  # l'inflation n'est pas négative
    
    return s


