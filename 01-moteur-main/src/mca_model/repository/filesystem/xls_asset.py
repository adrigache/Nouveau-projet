import pandas as pd
from functools import partial
from typing import List

from pprint import pprint

from mca_model.config import rc, XLS_RIGHT_PANE_OFFSET

from .xls_asset_opex import extract as extract_opex

from .xls_utils import (
    keep_only_activated_assets,
    get_date,
    get_str,
    get_number,
    get_bool,
    get_year,
    get_number_with_unit    
    )


FIELDS = [
    (get_str, 'ASSET_CODE'), 
    (get_str, 'ASSET_NAME'), 
    (get_str, 'ASSET_TYPE'), 
    (get_str, 'ASSET_TYPOLOGY'),
    (get_bool, 'ASSET_MASTER_ACTIVATION'), 
    (get_date, 'ASSET_CONSTRUCTION_START'),
    (get_date, 'ASSET_CONSTRUCTION_END'), 
    (get_date, 'ASSET_MERCHANT_PRE_CONTRACT_START'),
    (get_date, 'ASSET_MERCHANT_PRE_CONTRACT_END'),
    (get_date, 'ASSET_MERCHANT_POST_CONTRACT_START'),
    (get_date, 'ASSET_MERCHANT_POST_CONTRACT_END'),
    (get_date, 'ASSET_OPERATION_CONTRACT_START'),
    (get_date, 'ASSET_OPERATION_CONTRACT_END'), 
    (get_number_with_unit, 'ASSET_INSTALLED_CAPACITY'), 
    (get_str, 'ASSET_REVENUES_INFLATION'),
(get_number, 'ASSET_CAPACITY_DEGRADATION_RATE_LENDERS'), 
    (get_number, 'ASSET_CAPACITY_DEGRADATION_RATE_SPONSOR'),
    (get_date, 'ASSET_CAPACITY_DEGRADATION_START_DATE'), 
    (get_number, 'ASSET_PRODUCTION_AVAILABILITY_LENDERS'),
    (get_number, 'ASSET_PRODUCTION_AVAILABILITY_SPONSOR'),
    (partial(get_str, validate=['P50', 'P90']), 'ASSET_YIELD_LENDERS'),
    (partial(get_str, validate=['P50', 'P90']), 'ASSET_YIELD_SPONSOR'),
    (get_number, 'ASSET_YIELD_PORTOFOLIO_EFFECT'),
    (get_number, 'ASSET_YIELD_EXCL_CAPACITY_P50'),
    (get_number, 'ASSET_YIELD_EXCL_CAPACITY_P90'),
    (get_bool, 'ASSET_SELF_CONSUMPTION'), 
    (get_number, 'ASSET_SELF_CONSUMPTION_ANNUAL_FEE'), 
    (get_number_with_unit, 'ASSET_CONTRACTED_REVENUES_REF_TARIFF'), 
    (get_number_with_unit, 'ASSET_CONTRACTED_REVENUES_BONUS_TARIFF'),
    (get_number_with_unit, 'ASSET_CONTRACTED_REVENUES_MALUS_TARIFF'),
    (get_bool, 'ASSET_CONTRACTED_REVENUES_MALUS_ACTIVATION'), 
    (get_bool,'ASSET_CONTRACTED_REVENUES_YIELD_THRESHOLD_ACTIVATION'),
    (get_str, 'ASSET_REVENUES_MERCHANT_PRICE_SCENARIO'),
    (get_str, 'ASSET_OPEX'),         # keep it for tagging
    (get_str, 'ASSET_LOCAL_TAXES'),  # keep it for tagging and OPEX 
    ]



def get_code_from_name(s:str):
    """transform XLS code to inner py name"""
    return s.split('ASSET_', 1)[1].lower()


    
def load(df:pd.DataFrame, model:dict, **kwargs):
    """load all data"""

    # initial filtering - keep activated assets
    df = keep_only_activated_assets(df, 'ASSET_MASTER_ACTIVATION', XLS_RIGHT_PANE_OFFSET)
    if kwargs.get('debug', False):
        rc.debug(f'[asset] activation: {df.columns.size} columns kept')

    # common params
    params = dict(
        offset=XLS_RIGHT_PANE_OFFSET,
        first=False,
        raise_error=False,
        ** kwargs
        )
  
    # class fields
    raw = { k: f(df, k, **params) for f,k in FIELDS }

    # exit - just get raw data
    if kwargs['return_field_name']:
        return raw

    # read raw data
    raw = [ (get_code_from_name(k), v) for k,v in raw.items()]

    # ETL on raw data
    create_and_register_assets(model, raw, params['debug'])

    # specific fields
    add_asset_contracted_revenues_yield(df, model, params['debug'])  
    extract_opex(df, model, params['debug'])



    
class Line:
    """might look overkill as a lambda i,j:data[j][i] should suffice, but I need to deal with different output values"""
    def __init__(self, data:List, i:int, expected_size:int, debug:bool=False):

        self.debug = debug
        self._data = data
        self._expected_size = expected_size
        self._asset = i
        self._pos = -1

        # # check for case where output_unit=True
        # assert(self._expected_size>2)

    # get value or fill with zero
    def get_value(self, code:str, data:list):
        """"""
        if len(data)>self._asset:
            return data[self._asset]
        
        rc.debug(f'{code}: fill with zeros', debug=self.debug)
        return 0

        
    def next(self):
        self._pos += 1

        if self._pos == len(self._data):
            return None, None

        code, values = self._data[self._pos]
        
        # depends on type
        if isinstance(values, tuple):
            _values, unit = values
            assert(isinstance(_values, list)) # fail fast
            return code, (self.get_value(code, _values), unit)  # (value, unit)
        
        # common case
        if isinstance(values, list):
            return code, self.get_value(code, values)
                    
        # you should not be here
        raise Exception(f'{code} wrong size: {len(values)} found, should be {self._expected_size}')
    

        
def create_and_register_assets(model:dict, data:List, debug:bool):
    """"""
    n_assets = len(data[0][1])
    rc.debug(f'.assets detected: {n_assets}', debug=debug)

    # fill
    for i in range(n_assets):
        line = Line(data, i, n_assets, debug)
        _, spv_name = line.next()
        _, asset_name = line.next()

        spv = model['vehicle'][spv_name]
        if 'assets' not in spv:
            spv['assets'] = {}

        _data = {}
        while True:
            name, value = line.next()
            if name is None:
                break

            rc.debug(f'.write |{name}|: {value}', debug=debug)
            assert(name not in _data)
            _data[name] = value
            
        spv['assets'][asset_name] = _data
        
        if debug:
            rc.check(f'.SPV {spv_name} add asset {asset_name}')


    # fill SPV with no assets
    for k,obj in model['vehicle'].items():
        if obj['type'] == 'SPV' and 'assets' not in obj:
            obj['assets'] = {}
           
           



def add_asset_contracted_revenues_yield(df:pd.DataFrame, m:dict, debug:bool):
    """specific"""

    i0 = df.index.get_loc('ASSET_CONTRACTED_REVENUES_YIELD_THRESHOLD_ACTIVATION')
    j0, j1 = 4,9

    ex = df.iloc[i0:i0+3, j0:j1]
    assert(ex.iloc[:, -1].isnull().all()) # last column must be empty

    unit = ex.iloc[-1,0]
    params = {}
    for _,col in ex.iloc[:, :-1].items():
        params[col.values[0]] = col.values[1:]

    for vname, node in m['vehicle'].items():
        if node['type'] == 'SPV':
            for k, a in node['assets'].items():
                threshold, price = params[a['typology']]
                a['contracted_revenues_yield_threshold'] = threshold
                a['contracted_revenues_yield_tariff_above_threshold'] = (price, unit)


