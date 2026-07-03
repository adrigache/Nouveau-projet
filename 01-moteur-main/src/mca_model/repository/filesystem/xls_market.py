import pandas as pd
import numpy as np
from functools import partial

from .xls_utils import (
    # get_date,
    get_str,
    get_int,
    get_number,
    get_column,
    get_column_between
    # get_bool,
    # get_year,
    # get_number_with_unit    
    )


OFFSET_YEARS = 1
OFFSET_IPC = 4


FIELDS = [
    (partial(get_str, offset=4), 'MARKET_IPC_SCENARIO'),
    (partial(get_number, offset=5), 'MARKET_IPC_PERCENTAGES'),
    (partial(get_int, offset=OFFSET_YEARS), 'MARKET_IPC_YEAR_START'),
    (partial(get_int, offset=OFFSET_YEARS), 'MARKET_IPC_YEAR_STOP'),
    (partial(get_str, offset=12), 'MARKET_PRICE_SCENARIO'),  # not use but keep for autotag
    # (partial(get_number, offset=12), 'MARKET_PRICE_SCENARIO_VALUES'), # not use ...
    ]


def load(df:pd.DataFrame, model:dict,  **kwargs):
    """load all data"""

    params = dict(first=False, **kwargs)
    
    raw = { k: f(df, k, **params) for f,k in FIELDS }
    if kwargs['return_field_name']:
        return raw
    
    return {
        **read_inflation(df, raw, **kwargs),
        **read_market_prices(df, raw, **kwargs),
        }
    

def read_inflation(df:pd.DataFrame, raw:dict, **kwargs):
    """IPC"""

    # get inflation increments
    ex = raw['MARKET_IPC_SCENARIO']
    
    pos = [ i for i,x in enumerate(ex) if x=='Index']
    scenario = ex[pos[0]+1:pos[1]]
    assert(scenario[0] == 'IPC')
    
    # ipc = get_number(df, key='MARKET_IPC_PERCENTAGES', offset=5, first=False)
    ipc = raw['MARKET_IPC_PERCENTAGES']
    assert(all([x>0 and x<1 for x in ipc]))
    ipc.insert(0, 1.)  
        
    # get base values
    cols = ['MARKET_IPC_YEAR_START', 'MARKET_IPC_YEAR_STOP']
    (y0, i), (y1, j) = get_column_between(df, cols, OFFSET_YEARS, target_type=int)

    between = [i, j]
    years = get_column(df, between, offset=OFFSET_YEARS, target_type=int) 
    rates = get_column(df, between, offset=OFFSET_IPC, target_type=float) 

    assert((years[0] == y0) and (years[-1] == y1))
    assert(all([x>=0 and x<1 for x in rates]))
       
    return {
        'ipc_years': years,
        'ipc_base_rate': rates,
        'ipc_percentage': ipc,
        'ipc_scenario': scenario
        }




def read_market_prices(df:pd.DataFrame, raw:dict, **kwargs):
    """IPC"""

    # -- extract bloc
    i0 = df.index.get_loc('MARKET_PRICE_SCENARIO')
    j0 = df.iloc[i0].values.tolist().index('Market price scenario')

    # get block width
    width = 5
    dj = 0
    while j0+dj < min(50, df.columns.size-width):
        if df.iloc[i0, j0+dj:j0+dj+width].count()==0:
            break
        dj += 1
        
    block = df.iloc[i0:,j0:j0+dj]

    # get block height
    min_height = 10
    for i, (_,row) in enumerate(block.iloc[min_height:].iterrows()):
        if row.count() == 0:
            
            break
         
    # now drop empty columns
    block = block.iloc[:min_height+i,:]
    block.dropna(axis=1, inplace=True, how='all')
    block.columns = block.iloc[0]
    block = block.iloc[1:].dropna(axis=0, how='all')

    #
    years = block.loc[:,'Market price scenario'].values.tolist()

    out = {}
    for name, col in block.items():
        if name != 'Market price scenario' and not pd.isnull(name) and col.count(): 
            assert(name not in out)
            out[name] = col.values.tolist()

    # now clean
    ind = [ i for i,x in enumerate(years) if isinstance(x, int) and x > 1900]  # year is > 1900

    f_restrict = lambda x:list(np.array(x)[ind])
    years = f_restrict(years)
    out = { k:f_restrict(v) for k,v in out.items()}

    assert( all([ len(v) == len(years) for v in out.values()]))

    return {
        'market_price_years': years,
        'market_price_scenario': out}
        
