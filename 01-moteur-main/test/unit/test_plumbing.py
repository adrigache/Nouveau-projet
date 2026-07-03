import pytest
import datetime as dt

from mca_model.plumbing.nodes import SPV



def test_iterate_over_spv(model):

    assert(len(model.spv)==3)
    for spv in model.spv:
        assert(spv.name.startswith('SPV_'))
        assert(isinstance(spv, SPV))

        
def test_spv_apply_on_assets(model):    
    f = lambda m,a:None
    for spv in model.spv:
        found = [ x for _,x in spv.apply_on_assets(f, model=model)]
        assert(all([ x is None for x in found]))
        

    f = lambda m,a:a.name
    for spv in model.spv:
        found = [ x for _,x in spv.apply_on_assets(f, model=model)]
        assert(all([ x.startswith('Actif_') for x in found]))

    def f(m, a, ref):
        return (a.construction_start-ref).days
    
    for spv in model.spv:
        found = [ x for _,x in spv.apply_on_assets(f, ref=dt.date(2024,4,3), model=model)]
        assert(all([ (x>100 and x<1000) for x in found]))

        
def test_model_compute(model):    

    f = lambda m,a:a.name
    found = model.compute(f)
    
    assert( len(found) == 3)
    assert( len(found[0]) == 2)
    assert( [ x.startswith('Actif_') for _,x in found])

    # go deeper
    found = model.TopCo.children[0].apply(f, model=model)

    assert( len(found) == 3)
    found = model.TopCo.children[1].apply(f, model=model)
    assert( len(found) == 0)
    
    def f(m, a, b):
        return a.installed_capacity[0]/b
    
    found = model.TopCo.apply(f, b=1000, model=model)
    target = (159.705 + 31.05 + 31.05)/1000
    assert( pytest.approx(sum( [x for _,x in found]), abs=0.01)==target)
