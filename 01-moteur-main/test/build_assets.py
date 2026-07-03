#!/usr/bin/env python
import tomli_w

from mca_model.repository.filesystem import read_xls
from mca_model.plumbing import build 

from conftest import FNAME_MODEL_XLS, FNAME_MODEL_TOML



def build_model_from_xls():
    model = read_xls.load_model(FNAME_MODEL_XLS, debug=True)

    with open(FNAME_MODEL_TOML, 'wb') as f:    
        tomli_w.dump(model, f)

    build.load(FNAME_MODEL_TOML, debug=False)

        
build_model_from_xls()
