import pandas as pd
from pprint import pprint
from pathlib import Path

from typing import List

from mca_model.config import rc
from mca_model.config import (
    FNAME_MODEL_TAG,
    MODEL_SHEETS,
    XLS_DEFAULT_FIELD_NAME, XLS_MARKET_FIELD_NAME)


from mca_model.repository.filesystem import read_xls 
from mca_model.plumbing import build


def load_reference(as_model:bool=False):
    """"""

    if not as_model:
        return read_xls.load_model(FNAME_MODEL_TAG, debug=False, output='raw')

    # keep ?
    return read_xls.load_model(FNAME_MODEL_TAG, debug=False, output='model')

    
    

def load_sheet(fname:Path, sheetname:str, debug:bool) -> pd.DataFrame:
    """"""
    inner = MODEL_SHEETS[sheetname]

    if debug:
        rc.shift(f'reading xls ({sheetname}|{inner})', 2)
        
    raw = pd.read_excel(fname, inner)

    if debug:
        rc.shift(f'preparing {raw.index.size} x {len(raw.columns)} ', 2)
        
    raw = raw.drop(columns=raw.columns[:1])
    raw.insert(0, '__code', '')

    return raw, inner







def identify_position_of_label(values:List, label:str, ref_pos:int)  -> bool:
    """"""
    
    many = [ i for i,x in enumerate(values) if x == label]
    for i in many:
        if abs(i-ref_pos) < 2:
            return True, i
        
    return False, None


def look_for_tag_with_offset(candidates:List, reference:dict, debug:bool):
    """"""
    skipped =  ['MARKET_IPC_PERCENTAGES', 'MARKET_PRICE_SCENARIO']
    
    out = {}
    for xls_code, data in reference.items():
        _, xls_txt, xls_pos = data
        _key = f'{xls_code}'.upper()

        is_found = False
        if xls_txt in candidates:
            is_found, line_number = identify_position_of_label(candidates, xls_txt, xls_pos)
            if is_found:
                out[_key] = line_number
                rc.debug(f'.{_key} found at line {line_number} with label= {xls_txt}', debug=debug)

        if not is_found:
            if _key not in skipped:
                rc.fail(f'.!! {_key} not found !!')
               
    #
    return out



def look_for_tags(raw:pd.DataFrame, reference:dict, sheetname:str, debug:bool):
    """"""

    # first pass - basic offset (=column selection)
    offsets = [
        XLS_DEFAULT_FIELD_NAME + (2 if sheetname == 'dashboard' else 1),
        # XLS_MARKET_FIELD_NAME,
        ]

    for offset in offsets:
        candidates = raw.iloc[:, offset].tolist()
        found = look_for_tag_with_offset(candidates, reference, debug)
        f_already_written = lambda x:x in raw.iloc[:,0].values
        
        for xls_key, pos in found.items():
            if not f_already_written(xls_key):
                raw.iloc[pos,0] = xls_key
                assert( f_already_written(xls_key))

    
    if debug:
        rc.shift(f'values found: {len(found)}/{len(reference)}' )



def apply_tweaks(data:dict, reference:dict):
    """stuff I have to set manually"""
    
    _,_, i = reference['market']['MARKET_IPC_SCENARIO']
    data['ass_Market'].iloc[i+1,0] =  'MARKET_IPC_PERCENTAGES'

    _,_, i = reference['market']['MARKET_PRICE_SCENARIO']
    data['ass_Market'].iloc[i,0] =  'MARKET_PRICE_SCENARIO'

    
    # prepare for reinjection
    data = {k.strip('ass_').lower():v.set_index('__code') for k,v in data.items()}
    return data

    
def process(fname:Path, reference:dict, debug:bool=False) -> dict[str, pd.DataFrame]:
    """"""

    rc.squared(f"tagging file: {fname.name}")
    rc.step(f"reference loaded: {sum([ len(x.keys()) for x in reference.values()])} tags detected")

    tagged = {}
    for name, _reference in reference.items():
        if debug:
            rc.step(f'processing {name}')

        # read new
        raw, inner_name = load_sheet(fname, name, debug)

        # results
        look_for_tags(raw, _reference, name, debug)
        tagged[inner_name] = raw
    #

    return apply_tweaks(tagged, reference)

 
