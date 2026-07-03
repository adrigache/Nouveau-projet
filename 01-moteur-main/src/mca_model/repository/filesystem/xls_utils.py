import re
import pandas as pd
import numpy as np
from typing import Type, Any, cast
import datetime as dt
from functools import partial

from mca_model.config import (
    rc,
    XLS_DEFAULT_FIELD_NAME,
    XLS_DEFAULT_OFFSET,
    ALLOW_UNITS_NUMBER)

from typing import List

log = lambda a,b:rc.check(f'[parameters] {a}: {b}')


def get_str(df:pd.DataFrame, key:str, **kwargs):
    return get_type(df, key, str, **kwargs)


def get_number(df:pd.DataFrame, key:str, **kwargs):
    return get_type(df, key, np.float64, **kwargs)


def get_int(df:pd.DataFrame, key:str, **kwargs):
    return get_type(df, key, int, **kwargs)

def get_bool(df:pd.DataFrame, key:str, **kwargs):
    return get_type(df, key, bool, **kwargs)


def get_date(df:pd.DataFrame, key:str, **kwargs):
    out = get_type(df, key, dt.date, **kwargs)
    return out


def get_year(df:pd.DataFrame, key:str, **kwargs):
    # kwargs.update( {'output_unit':False})
    
    out = get_type(df, key, int, **kwargs)

    if kwargs['return_field_name']:
        year, name, pos = out
        return dt.date(year,1,1), name, pos
    else:
        return dt.date(out,1,1)


# compounded
get_number_with_unit = partial(get_number, output_unit=True)


def look_for_bool(x:Any):
    """"""
    if isinstance(x, bool):
        return x
    
    if isinstance(x, int):
        match x:
            case 1:
                return True
            case 0:
                return True
            case _:
                pass

    if isinstance(x, str):
        if x.lower() in ['vrai', 'true', 'oui', 'yes', 'y']:
            return True
        if x.lower() in ['faux', 'false', 'non', 'no', 'n']:
            return False
    return None
          

    
def look_for_number(x:Any, target_type:Type):
    """"""
    match target_type:
        case t if issubclass(t, (np.floating, float)):
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
    

def look_for_date(x:Any):
    """"""
    if isinstance(x, dt.datetime):
        return x.date()
    if isinstance(x, dt.date):
        return x

    # print(x)
    # assert(False)
    try:
        return x.date()
    except Exception:
        try:
            return dt.datetime.strptime(x, '%d/%m/%Y').date()
        except Exception:
            pass
    # print('> OUTPUT', None)
    return None


def look_for_str(x:Any):
    """"""
    if x.strip().strip('#') != '':
        return x
    
    return None

    
def walk(data:list, target_type:Type, validate:List, first:bool):
    """"""
    out = []
    first_position_found = None

    def keep_value(value:Any):
        if (validate == []) or (value in validate):
            out.append(value)

    # ---
    for pos, x in enumerate(data):
        if pd.isnull(x):
            continue

        # float or similar
        # if np.issubdtype(type(x), np.number):
        if np.issubdtype(target_type, np.number):
            if (found := look_for_number(x, target_type)) is not None:
                keep_value(found)

                                
        # Handle datetime
        elif (target_type == dt.date):
            if (found := look_for_date(x)) is not None:
                # print(f'found: `{found}` as {type(found)}')
                keep_value(found)
                
        # boolean
        elif target_type is bool:
            if (found := look_for_bool(x)) is not None:
                keep_value(found)


        # Handle string
        elif np.issubdtype(target_type, str) and isinstance(x, str):
            if (found := look_for_str(x)) is not None:
                # _print(f'`{key}` found: `{found}` as {type(found)}')
                keep_value(found)
            
        # exit ?
        if len(out)>0 :
            if first_position_found is None:
                first_position_found = pos
            if first:
                out = out[0]
                break
    #
    # print('FOUND', out, first_position_found)

    return out, first_position_found


def try_to_detect_type(values:List, target_type:Type|None):
    """"""
    if values == [] or target_type is None:
        return None

    for s in values[::-1]:
        if not isinstance(s, str) or s == '':
            continue

        if np.issubdtype(target_type, dt.date):
            if re.search(r'date|year', s):
                return s
            break
        
        if np.issubdtype(target_type, np.number):
            if s in ['list', '#'] + ALLOW_UNITS_NUMBER:
                return s
            break

        if np.issubdtype(target_type, bool):
            if s in ['VRAI/FAUX']:
                return 'bool'

        if np.issubdtype(target_type, str):
            return s

    #
    return None
        






def find_value_from_line(data:List, offset:int|None, target_type:Type, validate:List, first:bool=False, debug:bool=False):
    """"""

    ex = data[offset:]
    found, i = walk(ex, target_type, validate, first)

    stype = None
    if i is not None:
        _data = data[offset+i-2:offset+i]
        stype = try_to_detect_type(_data, target_type)    

    return found, stype

    
def get_type(
    df:pd.DataFrame,
    key:str,
    target_type:Type,
    offset:int|None=XLS_DEFAULT_OFFSET,
    validate:List=[],
    first:bool=True,
    output_unit:bool=False,
    debug:bool=False,
    return_field_name:bool=False,
    return_field_name_offset:int=0,
    raise_error:bool=True
    ):
    """entry point"""

    if key not in df.index:
        raise KeyError(f"Index `{key}` not found")

    # get line
    iname = df.index.get_loc(key)
    data = df.iloc[iname].values.tolist() # in line

    # print(data)
    
    # get name & position
    name = data[XLS_DEFAULT_FIELD_NAME+return_field_name_offset]
    name = '(unset)' if pd.isnull(name) else name

    # extract data
    found, stype = find_value_from_line(data, offset, target_type, validate, first, debug)

    
    if debug:
        if found:
            n = len(found) if isinstance(found, list) else 1
            rc.squared('xls', f"{name} -> {key}/{target_type.__name__}, {n} values found, type {stype}", check=True)
        else:
            rc.squared('xls', f"{name} -> {key}/{target_type.__name__}, nothing found", check=True)
            
    if found == []:
        if raise_error:
            raise Exception(f"Value not found for: `{key}`. Unsupported target_type: {target_type}")

    # output
    if return_field_name:
        return  found, name, iname
    
    if output_unit:
        return found, stype
    return found



   

def get_column_between(df:pd.DataFrame, between:List[str], offset:int=0, target_type:Type=str):
    """"""

    i = df.index.get_loc(between[0])
    value0 = df.iloc[i, offset]
    j = df.index.get_loc(between[1])
    value1 = df.iloc[j, offset]


    return \
        (target_type(value0), i), \
        (target_type(value1), j)


    
def get_column(df:pd.DataFrame, between:[int,int], offset:int=0, target_type:Type=str):
    """"""

    ex = df.iloc[between[0]:between[1]+1, offset]

    return list(map(target_type, ex))





def keep_only_activated_assets(df:pd.DataFrame, key:str, offset:int):
    """filter on raw data"""

    left, right = df.iloc[:,:offset], df.iloc[:, offset:]

    # 
    values = right.loc[key].values
    allowed = [True, 1, 'vrai', 'true']
    icols = \
        [ i for i,x in enumerate(values) if x in allowed] +\
        [ i for i,x in enumerate(values) if isinstance(x, str) and x.lower() in allowed]

    cols = right.columns[icols]
    return pd.concat([left, right.loc[:,cols]], axis=1)
    
    
