import pytest
import pandas as pd

    
def test_read_vehicle(model_xls):
    my = model_xls['vehicle']

    assert(my['SPV_1']['parent'] == 'Holdco_1')
    assert(my['SPV_2']['parent'] == 'Holdco_2')
    assert(my['SPV_3']['parent'] == 'Holdco_1')
    _parents = set([x['parent'] for x in my.values() if 'parent' in x])
    _vehicles = set(my.keys())

    print(_parents)
    
    assert(_parents.issubset(_vehicles))

    assert(len(my['SPV_2']['assets'])==0 )
    assert(len(my['SPV_3']['assets'])==2 )
    _assets = [x for k,spv in my.items() if 'spv' in k.lower() for x in spv.get('assets')]
    assert(len(_assets)==3)

    
