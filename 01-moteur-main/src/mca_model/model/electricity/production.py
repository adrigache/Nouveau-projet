import datetime as dt
import numpy as np
# import QuantLib as qlib
import pandas as pd

from functools import partial, reduce
from dateutil.relativedelta import relativedelta

from mca_model import utils
from mca_model import Asset, Model

from mca_model.config import rc

from mca_model.service.helpers import (
    ONE_DAY, MIDNIGHT)

from mca_model.service.helpers import (
    apply_yearly_rate,
    )

from mca_model.model.utils import (
    zeros,
    log_number,
    log_str,
    log_header
    )

get_human_name = partial(utils.get_human_name, field='revenues')

    
def f_installed_capacity(m:Model, a:Asset) -> float:
    """expressed in kW"""
    value, unit = a.installed_capacity

    assert(unit == 'kWc')
    return value




def f_capacity_degradation(m:Model, a:Asset) -> pd.Series:
    """"R1023: Capacity degradation"""

    base_rate = utils.get_param(a, 'capacity_degradation_rate', m.scenario)
    start = a.capacity_degradation_start_date

    assert(base_rate<0.1) # 10%
    
    
    rate = apply_yearly_rate(m.time, start, 1-base_rate)
    
    log_number('degradation rate', f'{1-rate.max():.1%} to {1-rate.min():.1%}')

    return rate


def f_production_yield(m:Model, a:Asset) -> float:
    """Yield excl availability: number of hours of production per year
    ...
    portofolio 2555-> ... (sensibility)"""

    
    # key = get_param(a, 'yield', m.scenario){'sponsor':a.yield_sponsor, 'lender':a.yield_lenders}[m.scenario].lower() #P90 or P50
    key = utils.get_param(a, 'yield', m.scenario).lower() #P90 or P50
    value = getattr(a, f'yield_excl_capacity_{key}') 

    year_to_month = 1/12 
    if key == 'p90':
        return year_to_month * value*(1+a.yield_portofolio_effect)
    if key == 'p50':
        return year_to_month * value
    raise Exception(f"{key} should be 'p50' or 'p90'")



def f_production_availability(m:Model, a:Asset) -> float:
    """"portofolio 2555-> ... (sensibility)"""

    return utils.get_param(a, 'production_availability', m.scenario)
     

     
        
# def price_contracted_period(m:Model, a:Asset):
#     """FiT (PPA/CfD) - incl inflation
#     = guaranteed electricity price under a long-term contract that adjusts for inflation.
    
#     $Portfolio.R$3565:$Portfolio.R$4064)"""



#  #    =IF(
# #     AND($D3565=TRUE(), $F3565<>TRUE()),
# #     LET(
# #         _xlpm.variable, AN2555,
# #         _xlpm.production_threshold_activation, $I3565,
# #         _xlpm.reference_tarif, $H3565,
# #         _xlpm.production_threshold, $N3565,
# #         LET(
# #             _xlpm.check, _xlpm.production_threshold_activation=TRUE(),
# #             (
# #                 _xlpm.reference_tarif * (_xlpm.production_threshold_activation<>TRUE()) 
# #                 + _xlpm.reference_tarif * (
# #                     IF(
# #                         _xlpm.variable=0,
# #                         0,
# #                         MIN(_xlpm.variable, _xlpm.production_threshold) / _xlpm.variable
# #                     )
# #                 ) * _xlpm.check
# #             ) * AN2049
# #             + $O3565 * IF(
# #                 _xlpm.variable=0,
# #                 0,
# #                 (MAX(_xlpm.variable-_xlpm.production_threshold,0) / _xlpm.variable * _xlpm.check)
# #             )
# #         )
# #         + (
# #             $L3565 * ($K3565<>TRUE()) 
# #             + $M3565 * ($K3565=TRUE())
# #         )
# #     ),
# #     0
# # )
    
#     return 1


# def self_consumption_contracted_period(m:Model, a:Asset):
#     """Self-consumption

#     $Portfolio.R$4069:R$4568"""
#     return 1

    
    
# # def electricity_price(p:Params):
# #     """
# #     So FiT (PPA/CfD) – incl inflation refers to the agreed electricity price under a long-term contract that accounts for inflation adjustments.
# #     FiT: Feed-in Tariff. It is a guaranteed price paid for electricity generated from renewable sources.
# #     PPA: Power Purchase Agreement, and CfD is Contract for Difference. Both are mechanisms to set or stabilize the price of electricity over 
# #     """
    
# #     #     =
# #     # SI(ET($D3565=VRAI;$F3565<>VRAI);
# #     #   LET(variable; S2555; production_threshold_activation; $I3565; reference_tarif; $H3565; production_threshold; $N3565;
# #     #      LET(check; production_threshold_activation = VRAI;
# #     #         (
# #     #         reference_tarif * (production_threshold_activation<>VRAI) + reference_tarif * (SI( variable = 0; 0; MIN(variable; production_threshold) / (variable)) ) * check
# #     #         )*S2049
# #     #         + $O3565 * SI( variable = 0; 0; ( MAX(variable - production_threshold;0) / (variable) * check))
# #     #      )
# #     #   ) +
# #     # ($L3565*($K3565<>VRAI)+$M3565*($K3565=VRAI));0)


# #     return pd.DataFrame()

    
# # def electricity_self_consumption(p):
# #     """
# #     =IF(AND($D4069,$F4069),$K4069*Q$4067*Q17,0)
# #     """

# #     return pd.DataFrame()

    

# # def electicity_production_merchand_period(p:Params):
# #     """"""

# #     # = SUMPRODUCT(
# #     #   ( ($Portfolio.$F$17:$F$516)=$G$3)         -> le bon indice du SPV
# #     #   * $Portfolio.Q$3058:$Portfolio.Q$3557,    -> production =IF($D3058,R520*$G2555*R1023*$I2555*$K2555*10^-3,0)
# #     #    $Portfolio.Q$4589:Q$5088)                -> Merchant price - incl inflation
# #     #   *10^-3*Q$24

    
# #     return pd.DataFrame()

