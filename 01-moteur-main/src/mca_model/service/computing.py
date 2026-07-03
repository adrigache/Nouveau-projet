import numpy as np
import pandas as pd

from typing import Callable, List
from mca_model import Model, Asset


def sum_results_by_assets(m:Model, functions:List[Callable], **kwargs):
    """"""

    # compute
    by_asset: dict(Any, pd.Series)
    by_asset = {}
    
    for func in functions:

        # computations by assets are made here
        results = m.compute(func, **kwargs)  

        # aggregate
        for asset, values in results:
            if asset not in by_asset:
                by_asset[asset] = []

            by_asset[asset].append(values)
        
        
    # sum
    return {a:sum(v) for a,v in by_asset.items()}



def add_subtotals(data:dict[str, pd.Series]):
    """add each row to the next one"""

    previous = list(data.keys())[:-1]
    target = list(data.keys())[1:]
    for prev, key in zip(previous, target):
        data[key] = { k:v + data[prev][k] for k,v in data[key].items()}
    
    return data


def aggregate_over_assets(data:List[pd.Series]):
    """"""
    return sum(data.values()).sum()
    
    

def cash_flow(m:Model, **kwargs):
    """computations are done asset-wise"""

    fields = [
        cf.operating_cf,
        cf.CFADS,
        cf.CF_available_for_MRA,
        cf.CF_available_for_MDRA,
        cf.CF_available_for_junior_facility,
        cf.CF_available_for_shareholders,
        cf.cash_proceeds_account_EoP,
    ]

    # temporary computations
    my = { func.__name__:func(m, **kwargs) for func in fields }
    
    # now add each subtotal to the next one
    return add_subtotals(my)


    



from mca_model.model.cash_flow import entries as cf
