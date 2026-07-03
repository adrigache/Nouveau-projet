import pytest

import pandas as pd
import datetime as dt


from mca_model import Model, Asset
from mca_model.model import opex



def test_opex_price_production_intensive(model):
    """"""

    assets = model.list_assets()
    
    found = opex.get_price(model, assets[0])
