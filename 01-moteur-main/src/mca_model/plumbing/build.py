import tomllib
from pathlib import Path


from .nodes import TopCo, HoldCo, SPV
from mca_model import Model

from mca_model.check.model import check as check_model


def load(fname:Path, debug:bool=False):
    """"""

    assert(fname.suffix == '.toml')
    with open(fname, 'rb') as f:
        params = tomllib.load(f)

    return make_model(params, debug)



def make_model(raw:dict, debug:bool=False):
    """build from raw data"""

    m = Model(raw, debug=debug)
    create_objects(m, raw['vehicle'], debug)
    check_model(m)
    return m

    
def create_objects(m:Model, raw:dict, debug:bool):
    """create SPV/HoldCo etc instances from raw data"""

    objects = []
    for name, data in raw.items():
        _type = data['type']
        _class = {'topco':TopCo, 'holdco':HoldCo, 'spv':SPV}[_type.lower()]
        obj = _class(name, data, debug=debug)
        objects.append(obj)
        m.add_object(name, obj)
        
    # add parents
    m.link_objects()
    




