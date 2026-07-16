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


# ---------------------------------------------------------------------------
# Replication ANNUELLE exacte de la production (onglet Portfolio)
# Partagee par contracted (r2555) et merchant (r3058) : memes facteurs,
# seules les fenetres de jours changent.
# ---------------------------------------------------------------------------

def is_leap_year(y:int) -> bool:
    return (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0)


def days_in_year(y:int) -> int:
    return 366 if is_leap_year(y) else 365


def yearfrac_actact(a:dt.date, b:dt.date) -> float:
    """Reproduit Excel YEARFRAC(a, b, base=1) (actual/actual)."""
    if a == b:
        return 0.0
    if a > b:
        a, b = b, a
    if a.year == b.year:
        return (b - a).days / days_in_year(a.year)
    years = b.year - a.year + 1
    span = (dt.date(b.year + 1, 1, 1) - dt.date(a.year, 1, 1)).days
    return (b - a).days / (span / years)


def days_in_window_year(y:int, start:dt.date, end:dt.date) -> int:
    """Jours d'une fenetre [start, end] dans l'annee civile y, bornes INCLUSES (Excel +1)."""
    ys, ye = dt.date(y, 1, 1), dt.date(y, 12, 31)
    lo, hi = max(ys, start), min(ye, end)
    if lo > hi:
        return 0
    return (hi - lo).days + 1


def yield_annual_FLH(m:Model, a:Asset) -> float:
    """Rendement annuel en heures (M78 Excel), effet portefeuille inclus si P90."""
    key = utils.get_param(a, 'yield', m.scenario).lower()
    value = getattr(a, f'yield_excl_capacity_{key}')
    if key == 'p90':
        return value * (1 + a.yield_portofolio_effect)
    if key == 'p50':
        return value
    raise Exception(f"{key} should be 'p50' or 'p90'")


def _active_windows(windows:list[tuple[dt.date, dt.date]]) -> list[tuple[dt.date, dt.date]]:
    return [(s, e) for (s, e) in windows if s <= e]


def annual_production_MWh(m:Model, a:Asset, windows:list[tuple[dt.date, dt.date]]) -> dict[int, float]:
    """
    Production annuelle (MWh) repliquant l'Excel (Portfolio r2555/r3058):
        prod(y) = jours(y) * capacite * rendement * degradation(y) * dispo * 1e-3
    `windows` = liste de fenetres actives (contrat pour contracted ; pre+post pour merchant).
    """
    active = _active_windows(windows)
    if not active or not a.master_activation:
        return {}

    cap = f_installed_capacity(m, a)
    yld = yield_annual_FLH(m, a)
    avail = f_production_availability(m, a)
    rate_deg = utils.get_param(a, 'capacity_degradation_rate', m.scenario)
    deg_start = a.capacity_degradation_start_date

    y0 = min(s.year for s, _ in active)
    y1 = max(e.year for _, e in active)

    out, prev_deg = {}, 1.0
    for y in range(y0, y1 + 1):
        ys, ye = dt.date(y, 1, 1), dt.date(y, 12, 31)
        if deg_start > ye:
            deg = prev_deg
        else:
            f_start = 0.0 if (deg_start >= ys and ye >= deg_start) else yearfrac_actact(deg_start, ys)
            f_end = yearfrac_actact(deg_start, ye)
            deg = (1 - rate_deg) ** ((f_start + f_end) / 2)
        prev_deg = deg
        days = sum(days_in_window_year(y, s, e) for (s, e) in active)
        out[y] = (days / days_in_year(y)) * cap * yld * deg * avail * 1e-3
    return out
     

     
        
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

