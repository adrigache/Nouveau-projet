from copy import copy

from mca_model.config import FNAME_MODEL
from mca_model.plumbing.nodes import Asset
from mca_model.plumbing import build
from mca_model.model.model import Model


def load():
    return build.load(FNAME_MODEL)


def build_fake_objects(m:Model, a:Asset, params:dict, dates:dict):
    """"""


    # copy model
    _model = copy(m)
    _model.t_start, _model.t_end = dates['model']

    # copy asset
    _asset = copy(a)

    _asset.construction_start, _asset.construction_end =  dates['construction']
    _asset.operation_contract_start, _asset.operation_contract_end =  dates['operation']
    
    for k,v in params.items():
        if v is None:
            continue
        
        assert(hasattr(_asset, k))

        orig_value = getattr(_asset, k)
        if isinstance(orig_value, list):
            setattr(_asset, k, [v, orig_value[1]])
        else:
            setattr(_asset, k, v)

            
    # restrict to single asset
    matches = [
        (copy(holdco), copy(spv))
        for holdco in _model.TopCo.children
        for spv in holdco.children
        if _asset.name in spv._assets
    ]
    
    assert len(matches) == 1, f"Expected 1 match, found {len(matches)}"

    _holdco, _spv =  matches[0]
    _holdco.clear_children()
    _spv.set_parent(_holdco)
    _spv._assets = {_asset.name:_asset}
    
    _topco = copy(m.TopCo)
    _topco.clear_children()
    _holdco.set_parent(_topco)
    _model.clear_objects()
    _model.add_object('dummy', _topco)

    
    return _model, _asset
