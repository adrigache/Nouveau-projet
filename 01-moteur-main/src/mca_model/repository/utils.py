import pandas as pd
import numpy as np
from typing import Type, Any
import datetime as dt
from mca_model.config import rc



log = lambda a,b:rc.check(f'[parameters] {a}: {b}')


def get_str(df:pd.DataFrame, key:str, **kwargs):
    return get_type(df, key, str, **kwargs)


def get_num(df:pd.DataFrame, key:str, **kwargs):
    return get_type(df, key, np.float64, **kwargs)


def get_int(df:pd.DataFrame, key:str, **kwargs):
    return get_type(df, key, int, **kwargs)


def get_date(df:pd.DataFrame, key:str, **kwargs):
    return get_type(df, key, dt.datetime, **kwargs)


def get_year(df:pd.DataFrame, key:str, **kwargs):
    year = get_type(df, key, int, **kwargs)
    return dt.datetime(year,1,1)


def look_for_float(x:Any, target_type:Type):
    """"""
    if np.issubdtype(target_type, np.number):
        match target_type:
            case t if issubclass(t, np.floating):
                f = float
            case t if t is int:
                f = lambda x:int(float(x))
            case _:
                f = None
                    
        if f:
            try:
                return f(x)
            except ValueError:
                pass
            
    return None
    

def look_for_date(x:Any, target_type:Type):
    """"""
    _types = (dt.datetime, np.datetime64)
    if target_type in _types:
        if isinstance(x, _types):
            return x
        try:
            pass
            # return dt.datetime.strptime(x, '%d/%m/%Y', tzinfo=None)
        except Exception:
            pass
        
    return None


def look_for_str(x:Any, target_type:Type):
    """"""
    if isinstance(target_type, str):
        if x.strip().strip('#'):
            return x
        
    return None

    
def _walk(data:list, key:str, target_type:Type, first:bool=True, debug:bool=False):
    """"""

    _print = lambda s:(debug and rc.check(s))
    
    out = []
    while data != []:
        x = data.pop(0)

        if pd.isnull(x):
            continue

        # float or similar
        if (found := look_for_float(x, target_type)) is not None:
            _print(f'`{key}` found: `{found}` as {type(found)}')
            out.append(found)

        # Handle datetime
        elif (found := look_for_date(x, target_type)) is not None:
            _print(f'`{key}` found: `{found}` as {type(found)}')
            out.append(found)

        # Handle string
        elif (found := look_for_str(x, target_type)) is not None:
            _print(f'`{key}` found: `{found}` as {type(found)}')
            out.append(found)

        # exit ?
        if first and len(out)>0:
            return out[0]

    #
    if out:
        _print(f'`{key}` found: {len(out)} values found')
    return out



def get_type(
    df:pd.DataFrame,
    key:str,
    target_type:Type,
    pos:int=0,
    first:bool=True,
    debug:bool=False):
    """entry point"""

    values = df.loc[key].values.tolist()[pos:]
    found = _walk(values, key, target_type, first, debug)

    if found == []:
        raise Exception(f"Value not found for: `{key}`. Unsupported target_type: {target_type}")

    return found

