
import pandas as pd
from pprint import pprint
from pathlib import Path

from mca_model import Model, Asset
from mca_model.config import rc

from mca_model.repository.filesystem import utils, read_xls
from mca_model.plumbing import build
from mca_model.service import tagging, computing
from mca_model.explore import process as explore




def exploring(fname:Path, debug:bool=False) -> Model:
    """explore raw file"""

    explore.process(fname, debug)



def tag(fname:Path, debug:bool=False) -> Model:
    """auto tag file"""

    # 
    model_ref = tagging.load_reference()
    tagged = tagging.process(fname, model_ref, debug) # this is a dict

    # reinject as data extracted from XLS
    ex = read_xls.load_model(tagged, debug=debug)
    return build.make_model(ex, debug=debug)



def compute(fname:Path, debug:bool=False):
    """compute everything, asset wise"""
    
    model = utils.load_model(fname, debug=debug)
    print(model)
    
    # compute all values - results by asset
    results = {
        'cash flow': computing.cash_flow(model)}
    
    return model, results




def aggregate(m:Model, results:dict[Asset,pd.Series], debug:bool=False):
    """aggregate results, model wise"""

    rc.header('results', 'model wise')
    
    for k, v in results.items():
        rc.squared(k)
        for field,value in v.items():
            if value != 0:
                my = computing.aggregate_over_assets(value)
                
                rc.number(field.rjust(40), f'{my/1000:.0f} M€')
