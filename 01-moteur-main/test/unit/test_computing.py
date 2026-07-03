import pytest

from typing import Callable
from mca_model.service import computing


def test_sum_results_by_assets_dummy():

    class M:
        def __init__(self, value):
            self.data = {'a':1+value, 'b':2+value, 'c':3+value}
            
        def compute(self, func:Callable, **kwargs):
            return [ (k, func(v, **kwargs)) for k,v in self.data.items()]

    m = M(0)
    f = lambda x,**kwargs:1
    g = lambda x,**kwargs:x+1
    
    found = computing.sum_results_by_assets(m, [f, g], foo='bar')
    assert( found == {'a':3, 'b':4, 'c':5})

    with pytest.raises(TypeError):
        found = computing.sum_results_by_assets(m, [f, g], 1)


        
def test_sum_results_by_assets_real_model(model):
    """test on real structure"""
    
    def f(m, a, **kwargs):
        return a.installed_capacity[0]
    
    def g(m, a, **kwargs):
        return (m.t_end-m.t_start).days

    #
    found = computing.sum_results_by_assets(model, [f, g])
    ex = { a.name:v for a,v in found.items()}

    days = 13877
    assert(ex['Actif_1'] == 159.705 + days)
    assert( 'Actif_2' not in ex )
    assert(ex['Actif_3'] == 31.05 + days)
    assert(ex['Actif_4'] == 31.05 + days)

    # add arguments
    found = computing.sum_results_by_assets(model, [f, g], foo='bar')

    # fails
    with pytest.raises(TypeError):
        found = computing.sum_results_by_assets(model, [f, g], 1)


    
def test_add_subtotals():

    my = {
        'a':{'x':1, 'y':2},
        'b':{'x':10, 'y':20},
        'c':{'x':100, 'y':200}
        }
    
    assert( computing.add_subtotals(my) == {
        'a':{'x':1, 'y':2},
        'b':{'x':11, 'y':22},
        'c':{'x':111, 'y':222}
        })
