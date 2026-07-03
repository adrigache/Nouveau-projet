import pytest
from pathlib import Path

import pandas as pd
from mca_model.plumbing import build
from mca_model.repository.filesystem import read_xls

ROOT = Path(__file__).parents[0]
PATH_DATA = ROOT/'assets'

assert(PATH_DATA.exists())

def get_fname(s):
    return PATH_DATA/s

FNAME_MODEL_XLS = get_fname('model_dummy.xlsx')
FNAME_MODEL_TOML = get_fname('model_dummy.toml')
FNAME_MODEL_BASIC_XLS = get_fname('model_basic.xlsx')


@pytest.fixture(scope='session')
def model(request):
    return build.load(FNAME_MODEL_TOML, debug=False)

@pytest.fixture(scope='session')
def model_xls(request):
    return read_xls.load_model(FNAME_MODEL_XLS, debug=False)



class Node:
    time: pd.DatetimeIndex
    
    def __init__(self, d):
        for k,v in d.items():
            setattr(self, k, v)
            
    def __repr__(self):
        t = [f'class: {self.__class__.__name__}']
        for k,v in self.__dict__.items():
            if isinstance(v, (int, float, str, dt.date)):
                t.append(f'.{k}: {v}')
            else:
                t.append(f'.{k}: set')
        return '\n'.join(t)
    
