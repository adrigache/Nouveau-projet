import pandas as pd
from functools import partial

from mca_model.config import rc, XLS_RIGHT_PANE_OFFSET

from .xls_utils import (
    get_date,
    get_year,
    )


FIELDS = [
    (get_date, 'MODEL_TSTART'),
    (get_date, 'MODEL_TEND'),
    (get_year, 'MODEL_INFLATION_START'),
    # ( partial(get_str, validate=['Holdco', 'SPV']), 'VEHICLE_TYPE'), 
    # ( get_str, 'VEHICLE_NAME'),
    # ( get_str, 'VEHICLE_PARENT_NAME'),
    ]


def load(df:pd.DataFrame, model:dict, **kwargs):
    """load all data"""

    params = dict(first=True, offset=XLS_RIGHT_PANE_OFFSET, **kwargs)

    raw = { k: f(df, k, **params) for f,k in FIELDS }

    # exit - just get raw data
    if kwargs['return_field_name']:
        return raw

    return {
        't_start': raw['MODEL_TSTART'],
        't_end': raw['MODEL_TEND'],
        'inflation_start': raw['MODEL_INFLATION_START'],
        }




            
        
        
    
