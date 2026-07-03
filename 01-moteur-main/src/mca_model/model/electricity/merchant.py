import pandas as pd
import datetime as dt
from functools import partial, reduce

from mca_model import Asset, Model

from mca_model.service.helpers import (
    # monthfrac,
    days_in_range_per_month,
    # multiply_based_on_cumsum_threshold
    )

from mca_model.model.utils import (
    f_activation,
    zeros,
    log_number,
    log_header,
    )

from mca_model.model import market_price
from mca_model.model import inflation


from .production import (
    f_installed_capacity,
    f_capacity_degradation,
    f_production_yield,
    f_production_availability,
)



f_no_price = zeros
f_no_production = zeros


def f_days_of_electricity(m:Model, a:Asset) -> pd.Series:
    """same as in contracted but with two phases"""

    n_months = (m.t_end - m.t_start).days/30 # average

    def f_days_in_range(t0:dt.date, t1:dt.date):
        if t0 == t1:
            return zeros(m, a)
        
        out = days_in_range_per_month(m.time, t0, t1)
        
        # first & last  day of contract is included
        assert(out[t0:].iloc[0]>0)
        assert(out[t1:].iloc[0]>0)
        return out

    pre_contracted = f_days_in_range(
        a.merchant_pre_contract_start,
        a.merchant_pre_contract_end)
    
    post_contracted = f_days_in_range(
        a.merchant_post_contract_start,
        a.merchant_post_contract_end)
    
    log_number('days of electricity (pre)', f'{pre_contracted.sum()/n_months:.0%}')
    log_number('days of electricity (post)', f'{post_contracted.sum()/n_months:.0%}')

    return pre_contracted + post_contracted
    


def in_MWh(m:Model, a:Asset, **kwargs):
    """two phases : before contracted period and after"""

    functions = [
        f_days_of_electricity,
        f_installed_capacity,
        f_capacity_degradation,
        f_production_yield,
        f_production_availability
        ]
    
    log_header(a, 'compute electricity production (merchant)')
    
    if f_activation(m,a) == 1:
        return 1e-3*reduce(lambda a,b: a*b, (f(m, a, **kwargs) for f in functions))
    else:
        return f_no_production(m, a)



def f_price(m:Model, a:Asset, production:pd.Series):
    """"""
    
    prices = market_price.compute(m, a)

    assert(prices.index[0] == m.time[0])
    assert(prices.index[-1] == m.time[-1])

    return prices

    

def revenues(m:Model, a:Asset):
    """"""

    production = in_MWh(m, a)   # pas la meme que la periode sous contrat
    price = f_price(m, a, production) * inflation.compute(m,a)    

    return price * production

