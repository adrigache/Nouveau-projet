import pandas as pd
import re
import datetime as dt
from functools import partial, reduce

from mca_model import Asset, Model
from mca_model.service.helpers import (
    monthfrac,
    days_in_range_per_month,
    multiply_based_on_cumsum_threshold)

from mca_model.utils import ONE_DAY
from mca_model.check import units as check_unit
from mca_model.model import inflation

from mca_model.model.utils import (
    f_activation,
    zeros,
    log_number,
    log_header,
    log_str,
    )

from .production import (
    f_installed_capacity,
    f_capacity_degradation,
    f_production_yield,
    f_production_availability,
)



f_no_price = zeros
f_no_production = zeros

def debug_default_price(m:Model):
    return pd.Series(42, index=m.time)
    

def f_days_of_electricity(m:Model, a:Asset) -> pd.Series:
    """
    get the fraction of days per month where the SPV can produce electricity,
    according to contract.
    
    ref: portofolio, R17"""

    t0, t1 = a.operation_contract_start, a.operation_contract_end
    out = days_in_range_per_month(m.time, t0, t1)

    # first day of contract is included
    assert(out[t0:].iloc[0]>0)

    # last day of contract is included
    assert(out[t1:].iloc[0]>0)

    n_months = (m.t_end - m.t_start).days/30 # average
    log_number('days of electricity', f'{out.sum()/n_months:.0%}')
    return out 


    
def in_MWh(m:Model, a:Asset, **kwargs):
    """capacity en kW, sortie en MWh"""
    
    functions = [
        f_days_of_electricity,
        f_installed_capacity,
        f_capacity_degradation,
        f_production_yield,
        f_production_availability
        ]

    log_header(a, 'compute electricity production (contracted)')
    
    if f_activation(m,a) == 1:
        return 1e-3*reduce(lambda a,b: a*b, (f(m, a, **kwargs) for f in functions))
    else:
        return f_no_production(m, a)

    

def revenues(m:Model, a:Asset):
    """ computation.Q190 """

    if a.self_consumption:
        log_str('self consumption', 'yes')
        return f_no_price(m, a)
    
    production = in_MWh(m, a)
    # production.loc[production>0] = 10

    # 
    price_FiT = f_price_FiT(m, a, production) * inflation.compute(m,a)
    price_bonus_malus = f_bonus_or_malus(a) * production
    # remove self_consumption(*args) ?
    
    return price_FiT + price_bonus_malus

    

def f_price_FiT(m:Model, a:Asset, p:pd.Series):
    """
    gain, à partir du tarif de rachat (FiT) avec seuil

    FiT: feed-in Tariff. It is a guaranteed price paid for electricity generated from renewable sources.

    prod en MWh et prix en euro/MWh
    """
   
    base_price, unit = a.contracted_revenues_ref_tariff
    check_unit.price_of_electricity(unit)
    
    if a.contracted_revenues_yield_threshold_activation:
        _, unit = a.contracted_revenues_yield_tariff_above_threshold
        check_unit.price_of_electricity(unit)
    
        return multiply_based_on_cumsum_threshold(
            p,
            threshold =  a.contracted_revenues_yield_threshold,
            factor_before = base_price,
            factor_above = a.contracted_revenues_yield_tariff_above_threshold[0],
            )
            
    # no threshold
    else:
        return p * base_price


def f_bonus_or_malus(a:Asset):
    """"""
    if a.contracted_revenues_malus_activation:
        return a.contracted_revenues_malus_tariff[0]
    return a.contracted_revenues_bonus_tariff[0]


def f_self_consumption(*args):
    """dummy"""
    return 0
