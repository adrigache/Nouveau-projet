import pandas as pd
import numpy as np
import re
import datetime as dt
from functools import partial, reduce

from mca_model import Asset, Model
from mca_model import utils
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

from . import production
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
    """
    Revenu contracte (FiT/PPA/CfD) EXACT, replique de l'Excel (Portfolio r3565).

    L'Excel calcule le revenu contracte en ANNUEL (par annee civile) : le seuil de
    rendement s'applique sur la production reelle de l'annee (MWh), seule la part sous
    le seuil est indexee sur l'inflation, et l'inflation bascule a la date anniversaire
    (COD). On reproduit ce calcul annuel a l'identique, puis on le repartit sur les mois
    au prorata de la production mensuelle (les totaux annuels restent exacts au centime).

    Sortie: serie mensuelle en euros, alignee sur m.time.
    """

    if a.self_consumption:
        log_str('self consumption', 'yes')
        return f_no_price(m, a)

    log_header(a, 'compute contracted revenues (exact annual replication)')
    annual = annual_revenue_euros(m, a)
    return _distribute_annual_to_monthly(m, a, annual)


# ---------------------------------------------------------------------------
# Replication ANNUELLE exacte de l'Excel (onglet Portfolio)
# ---------------------------------------------------------------------------

def _annual_inflation_index(m:Model, a:Asset, y:int) -> float:
    """
    Index d'inflation annuel FiT (Excel Portfolio r1546): =1 l'annee du COD,
    puis compose (1 + taux_ipc * modificateur) chaque annee suivante.
    """
    rates = {yy: r for yy, r in zip(m.ipc_years, m.ipc_base_rate)}
    modifier = inflation.get_rate(m, a)
    anniv_year = a.operation_contract_start.year
    idx = 1.0
    for yy in range(anniv_year + 1, y + 1):
        r = rates.get(yy, rates[max(rates)])
        idx *= (1 + r * modifier)
    return idx


def _fit_inflation_year(m:Model, a:Asset, y:int) -> float:
    """
    Inflation FiT "exacte" appliquee au revenu (Excel Portfolio r2049): bascule
    ponderee par les jours a la date anniversaire (COD).
    """
    anniv = a.operation_contract_start
    ye = dt.date(y, 12, 31)

    # tant qu'on n'a pas depasse COD + 12 mois -> index = 1
    anniv_plus_12m = dt.date(anniv.year + 1, anniv.month, anniv.day)
    if anniv_plus_12m > ye:
        return 1.0

    prev = _annual_inflation_index(m, a, y - 1)
    cur = _annual_inflation_index(m, a, y)
    if prev == cur:
        return cur

    try:
        anniv_y = dt.date(y, anniv.month, anniv.day)
    except ValueError:  # 29 fev sur annee non bissextile
        anniv_y = dt.date(y, anniv.month, 28)
    ys = dt.date(y, 1, 1)
    before = (anniv_y - ys).days               # Jan 1 .. veille de l'anniversaire
    after = (ye - anniv_y).days + 1            # anniversaire .. 31 dec (inclus)
    return (before * prev + after * cur) / production.days_in_year(y)


def annual_production_MWh(m:Model, a:Asset) -> dict[int, float]:
    """
    Production contractee par annee civile (MWh), replique exacte de l'Excel
    (Portfolio r2555): fenetre = periode de contrat.
    """
    if a.self_consumption:
        return {}
    windows = [(a.operation_contract_start, a.operation_contract_end)]
    return production.annual_production_MWh(m, a, windows)


def annual_revenue_euros(m:Model, a:Asset) -> dict[int, float]:
    """
    Revenu contracte par annee civile (euros), replique exacte de l'Excel
    (Portfolio r3565):
        rev(y) = ref * MIN(prod, seuil) * inflation(y)
               + above * MAX(prod - seuil, 0)          [tarif au-dessus du seuil, NON indexe]
               + bonus/malus * prod
    ou seuil (MWh) = seuil_rendement(h) * capacite(kW) * 1e-3.
    """
    prod = annual_production_MWh(m, a)
    ref = a.contracted_revenues_ref_tariff[0]
    check_unit.price_of_electricity(a.contracted_revenues_ref_tariff[1])

    if a.contracted_revenues_yield_threshold_activation:
        above = a.contracted_revenues_yield_tariff_above_threshold[0]
        check_unit.price_of_electricity(a.contracted_revenues_yield_tariff_above_threshold[1])
        threshold = a.contracted_revenues_yield_threshold * f_installed_capacity(m, a) * 1e-3
    else:
        above = 0.0
        threshold = float('inf')

    bonus = f_bonus_or_malus(a)

    out = {}
    for y, p in prod.items():
        if p <= 0:
            out[y] = 0.0
            continue
        infl = _fit_inflation_year(m, a, y)
        out[y] = ref * min(p, threshold) * infl + above * max(p - threshold, 0.0) + bonus * p
    return out


def _distribute_annual_to_monthly(m:Model, a:Asset, annual:dict[int, float]) -> pd.Series:
    """
    Repartit chaque total annuel (euros) sur les mois de l'annee au prorata de la
    production mensuelle du moteur. Les totaux annuels restent exacts.
    """
    prod_m = in_MWh(m, a)
    vals = np.asarray(prod_m.to_numpy(), dtype=float)
    yrs = np.asarray(prod_m.index.year)
    out = np.zeros(len(prod_m), dtype=float)
    for y, total in annual.items():
        if not total:
            continue
        mask = yrs == y
        if not mask.any():
            continue
        ws = float(vals[mask].sum())
        if ws > 0:
            out[mask] = vals[mask] / ws * total
        else:
            out[mask] = total / int(mask.sum())
    return pd.Series(out, index=prod_m.index)

    

def _yield_excl_availability(a:Asset, scenario:str) -> float:
    """
    Rendement annuel en heures HORS disponibilite (M78 de l'Excel):
        INDEX(P90/P50) * (1 + effet_portefeuille si P90)
    P90 inclut l'effet de portefeuille, comme dans production.f_production_yield.
    """
    key = utils.get_param(a, 'yield', scenario).lower()  # 'p90' | 'p50'
    value = getattr(a, f'yield_excl_capacity_{key}')
    if key == 'p90':
        return value * (1 + a.yield_portofolio_effect)
    return value


def _threshold_variable(a:Asset, scenario:str) -> float:
    """
    Variable de repartition du seuil de rendement (Excel: M78 * M83) =
    rendement hors disponibilite * disponibilite. C'est le rendement annuel EFFECTIF
    (heures) delivre, qui determine la fraction de production payee au tarif de reference.
    """
    availability = utils.get_param(a, 'production_availability', scenario)
    return _yield_excl_availability(a, scenario) * availability


def f_price_FiT(m:Model, a:Asset, p:pd.Series):
    """
    gain, à partir du tarif de rachat (FiT) avec seuil de rendement.

    FiT: feed-in Tariff. It is a guaranteed price paid for electricity generated from renewable sources.

    prod en MWh et prix en euro/MWh.

    Reproduit la formule Excel (Portfolio, cf. production.py):
        prix = ref * MIN(yield, seuil)/yield  +  above * MAX(yield-seuil, 0)/yield
    ou `yield` est le rendement annuel en HEURES (pas la production en MWh) : le seuil
    de rendement fixe donc la FRACTION de production payee au tarif de reference, le reste
    etant paye au tarif reduit. On applique ce prix effectif (constant) a la production.
    """

    base_price, unit = a.contracted_revenues_ref_tariff
    check_unit.price_of_electricity(unit)

    if a.contracted_revenues_yield_threshold_activation:
        above_price, unit = a.contracted_revenues_yield_tariff_above_threshold
        check_unit.price_of_electricity(unit)

        threshold = a.contracted_revenues_yield_threshold
        variable = _threshold_variable(a, m.scenario)

        if variable <= 0:
            effective_price = base_price
        else:
            frac_ref = min(variable, threshold) / variable
            frac_above = max(variable - threshold, 0.0) / variable
            effective_price = base_price * frac_ref + above_price * frac_above

        return p * effective_price

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
