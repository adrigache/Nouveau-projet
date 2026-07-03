import pandas as pd
import datetime as dt

from typing import List

from mca_model import Model, Asset



def get_base_prices(t:pd.DatetimeIndex, years:List[int], prices:List[float]) -> pd.Series:
    """"""
  
    s = pd.Series( [0]*t.size, index=t, dtype=float )
    for y,p in zip(years, prices):
        s.loc[s.index.year==y] = p

    assert( all(~pd.isnull(s)))
    return s


def compute(m:Model, a:Asset):
    """"""
    years = list(map(int, m.market_price_years))
    base = m.market_price_scenario[a.revenues_merchant_price_scenario]

    return get_base_prices(m.time, years, base)

