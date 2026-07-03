import pytest
import pandas as pd
from pathlib import Path

from mca_model import Model, Asset
from mca_model.plumbing import build
from mca_model.utils import are_same_month

from mca_model.model.profit_loss import entries as pnl

# import(
#     EBITDA,
#     EBIT,
#     EBT,
#     net_result
#     )


ROOT = Path(__file__).parent

get_model_fname = lambda i:ROOT/f'model{i:02}.toml'


def test_results_structure():
    """test if structure is OK"""
    
    m:Model = build.load(get_model_fname(0))

    # just
    found = m.compute(pnl.net_result)

    assert(isinstance(found, list))
    assert(len(found) == 1)
    
    a, results = found[0]
    assert(isinstance(a, Asset))

    assert(isinstance(results, pd.Series))
    
    assert(are_same_month(results.index[0], m.t_start))
    assert(are_same_month(results.index[-1], m.t_end))

    
    
    
