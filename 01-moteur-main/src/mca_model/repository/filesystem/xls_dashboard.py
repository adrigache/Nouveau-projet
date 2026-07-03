
import pandas as pd
from functools import partial

from . import xls_utils
from .xls_utils import (
    get_int,
    )


FIELDS = [
    ( get_int,'DASHBOARD_SENSITIVITY' ),
    ( partial(get_int, validate=[1,2]), 'DASHBOARD_SCENARIO') ,
    ]

def load(df:pd.DataFrame, model:dict, **kwargs):
    """load all data"""

    raw = { k: f(df, k, **kwargs) for f,k in FIELDS }

    # exit - just get raw data
    if kwargs['return_field_name']:
        return raw
    
    return {
        'sensitivity': raw['DASHBOARD_SENSITIVITY'],
        'scenario':  raw['DASHBOARD_SCENARIO']
        }





