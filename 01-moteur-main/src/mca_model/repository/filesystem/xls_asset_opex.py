import re
import pytest
import numpy as np
import pandas as pd
import datetime as dt

from pprint import pprint

from typing import List


from mca_model.config import rc, XLS_RIGHT_PANE_OFFSET
from mca_model.check import units as check

DEFAULT_UNIT = 'k€/year'
XLS_OFFSET_BLOC_ID = 0
XLS_OFFSET_UNIT = XLS_RIGHT_PANE_OFFSET-3


def to_float(data:List):
    """"""
    return [0 if pd.isna(x) or x == '' else float(x) for x in data]

def to_date(data:List):
    """"""
    out = []
    for x in data:
        if isinstance(x, dt.datetime):
            out.append(x.date())
        elif isinstance(x, dt.date):
            out.append(x)
        else:
            out.append(None)
    return out


    
def identify_bloc_lines(n:int, df:pd.DataFrame, line_name:str, debug:bool):
    """"""

    out = {}
    details = []
    for i,line in df.iterrows():
        data = line.values.tolist()
        # print('\t', i, data)

        if not isinstance(data[0], str) or pd.isnull(data[0]):
            continue
            
        name = data[0].lower().strip()
        unit = data[XLS_OFFSET_UNIT]

        offset_values = XLS_OFFSET_UNIT+2
        raw_values = data[offset_values:]

        rc.debug(f'. opex line\tvalues: {raw_values}')

        # price
        if name == 'opex':
            values = to_float(raw_values)
            assert(len(values) == n)
            check.price(unit)
            rc.debug(f'. opex line\t|{name}|\t|{unit}|\t{len(values)} values')
            
            out['opex'] = {
                'values':values,
                'unit': unit
                }
            
        # inflation
        elif name == 'index':
            inflation = data[data.index('list')+2]
            rc.debug(f'. opex line\t|{name}|\t|{inflation}|')
            out['inflation'] = inflation

        # dates
        elif name.lower() in ['start date', 'end date']:
            assert('date' in [x.lower() for x in data[3:] if isinstance(x, str)])
            assert(data.index('date') == offset_values-2)
            assert(len(values) == n)
            
            out[name] = to_date(raw_values)
            rc.debug(f'. opex line\t|{name}|')

        # values
        else:
            values = to_float(raw_values)
            assert(len(values) == n)
            if pd.isnull(unit):
                assert( DEFAULT_UNIT.lower() in re.sub(r'\s','', line_name.lower()))
                unit = DEFAULT_UNIT
                
            details.append( [name, unit, values])
            rc.debug(f". opex line\tdetails: |{name}| |{unit}| {len(values)} values")
         #

    # rebuild price
    if details:
        assert(len(set([u for _,u,_ in details]))==1)

        _values = [sum(x) for x in zip(*[v for _,_,v in details])]
        assert( pytest.approx( out['opex']['values'], abs=.001) == _values)
        out['opex'] = {
            'values': _values,
            'unit': details[0][1],
            }

            
        rc.debug(f'. opex line\treplace Opex with details sum')

            
            
    return out
        
        

def identify_opex_blocs(df:pd.DataFrame, n:int, debug:bool):
    """"""

    df = df.reset_index(drop=True)
    idblocks = df.iloc[:,XLS_OFFSET_BLOC_ID].dropna().index
 
    out = {}
    for start, end in zip(idblocks[:-1],idblocks[1:] ):
        my = df.iloc[start:end]

        _id = int(my.iloc[0,0])
        _name = my.iloc[0,1].strip()

        rc.debug(f'. opex bloc identified\t|id: {_id}|\t|{_name}|')
        _lines = identify_bloc_lines(n, my.iloc[1:,1:], _name, debug)
        
        if not all( [x==0 for x in _lines['opex']['values']]):
            assert( _id not in out)
            out[_id] = {'name':_name, **_lines}
    #

    rc.header(f"OPEX", "processed, {len(out)} lines identified", status=True)
    if out:
        for i,op in out.items():
            unit = op['opex']['unit']
            if unit == 'k€/year':
                rc.check(f" #{i:02} |{op['name']}| with price {sum(op['opex']['values']):.1f}{unit}")
               
            elif unit == '€/MWh':
                prices = ', '.join( [f'{x:.1f}' for x in op['opex']['values']])
                rc.check(f" #{i:02} |{op['name']}| with price {prices} {unit}")
            else:
                raise NotImplementedError(f'unit: {unit} not implemented')

    return out




def extract(df:pd.DataFrame, m:dict, debug:bool):
    """read raw data from opex"""

   
    i0 = df.index.get_loc('ASSET_OPEX')
    i1 = df.index.get_loc('ASSET_LOCAL_TAXES')

    n_assets = len([a for x in m['vehicle'].values() if x['type'] == 'SPV' for a in x.get('assets',{})])

    blocks = identify_opex_blocs(df.iloc[i0:i1,:], n_assets, debug)

    # pprint(blocks)
    assets = [ a
        for v in m['vehicle'].values() if v['type']=='SPV'
        for a in v.get('assets',{}).values() ]

    # fill assets
    for ia,a in enumerate(assets):

        opex = []
        for i,b in blocks.items():
            _price =  b['opex']['values'][ia]
            if _price != 0:
                opex.append( {
                    'name': b['name'],
                    'index_xls':i,
                    'price': ( _price, b['opex']['unit']),
                    'start date': b['start date'][ia],
                    'end date': b['end date'][ia],
                    'inflation': b['inflation']
                        } )
        #
        a['OPEX'] = opex
        


    # for v in m['vehicle'].values():
    #     if v['type']=='SPV':
    #         for a in v.get('assets',{}).values():
    #             pprint(a['OPEX'])
    
