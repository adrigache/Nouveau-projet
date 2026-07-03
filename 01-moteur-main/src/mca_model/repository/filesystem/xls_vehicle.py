import pandas as pd
from functools import partial

from mca_model.config import rc, XLS_RIGHT_PANE_OFFSET
from .xls_utils import (
    keep_only_activated_assets,
    get_str,
    # get_int,
    get_number,
    get_bool,
    get_date,
    # get_year,
    get_number_with_unit    
    )


FIELDS = [
    ( partial(get_str, validate=[ 'Holdco', 'SPV']), 'VEHICLE_TYPE'), 
    ( get_str, 'VEHICLE_NAME'),
    ( get_bool, 'VEHICLE_ACTIVATION'),
    ( get_str, 'VEHICLE_PARENT_NAME'),
    ( get_number_with_unit, 'VEHICLE_OPEX'),
    ( get_date, 'VEHICLE_OPEX_START_DATE'),
    ( get_date, 'VEHICLE_OPEX_END_DATE'),
    ( get_str, 'VEHICLE_OPEX_INFLATION'),
    ]



def load(df:pd.DataFrame, model:dict, **kwargs):
    """load all data"""

    # initial filtering - keep activated assets
    df = keep_only_activated_assets(df, 'VEHICLE_ACTIVATION', XLS_RIGHT_PANE_OFFSET)
    if kwargs.get('debug', False):
        rc.debug(f'[vehicle] activation: {df.columns.size} columns kept')

    # get data
    params = dict(offset=XLS_RIGHT_PANE_OFFSET, first=False, **kwargs)
    raw = { k: f(df, k, **params) for f,k in FIELDS }
    
    # exit - just get raw data
    if kwargs['return_field_name']:
        return raw

    # extract
    f_add_unit = lambda x:[ (xs, x[1]) for xs in x[0]]
    _keys = list(raw.keys())
    _values = [ f_add_unit(v) if isinstance(v, tuple) else v for v in raw.values()]
    
    for k,v in zip(_keys,_values):
        rc.debug(f'check\tfor key: {k} I found {len(v)} values')
        assert(len(v) == len(_values[0]))

    out = {}
    for data in zip(*_values):
        (type, name, active), others = data[:3], list(data[3:])

        assert(active is True)
        assert(name not in out)
        assert(type.lower() in ['holdco', 'spv'])
        out[name] = {
            'type': type,
            # others values
            'parent':others.pop(0),
            'opex': others.pop(0),
            'opex_start_date': others.pop(0),
            'opex_end_date': others.pop(0),
            'opex_inflation': others.pop(0),
            }

        assert(others == [])
        if name =='TopCo':
            out[name]['type']= 'TopCo'
            out[name].pop('parent')
            
        rc.debug(f'vehicle created: {name} as {type}')

    return out
