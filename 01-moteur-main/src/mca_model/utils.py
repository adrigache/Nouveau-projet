import pandas as pd
import datetime as dt
import inspect
from typing import Any

from rich.console import Console

from mca_model.plumbing.nodes import Asset

from dateutil.relativedelta import relativedelta
from .config import FOR_HUMANS

ONE_DAY = relativedelta(days=1)
THIRTY_DAYS = relativedelta(days=30)
ONE_YEAR = relativedelta(years=1)
MIDNIGHT = dt.time(hour=0, minute=0)


def console_to_str(s:Any, end:str='\n'):
    """"""
    console = Console(record=True)
    with console.capture() as capture:
        console.print(s, end=end)

    return capture.get()


def get_human_name(field:str) -> str:
    """"""
    func = None
    for el in inspect.stack()[:10]:
        if el.function not in ['get_human_name', 'f', 'apply', 'apply_on_assets']:
            func = el.function
            break

    return FOR_HUMANS['functions'][field].get(func, 'not set')
    

def first_day_of_month(t:dt.date):
    return t.replace(day=1)


def next_month(t:dt.date):
    return (t + relativedelta(months=1)).replace(day=1)


def are_same_month(t0:dt.date|dt.datetime, t1:dt.date|dt.datetime):
    return (t0.month==t1.month) and (t0.year==t1.year)



def get_param(a:Asset, key:str, mod:str):

    if hasattr(a, f'{key}_{mod}'):
        return getattr(a, f'{key}_{mod}')
        
    if mod == 'lender':
        return getattr(a, f'{key}_lenders')

    raise AttributeError(f'get_param: cannot build a key from |{key}| and |{mod}|')

