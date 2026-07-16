import pandas as pd
import numpy as np
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


from . import production
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
        # fenetre vide ou desactivee (fin <= debut) => aucune production merchant
        if t0 >= t1:
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



def f_price(m:Model, a:Asset, production:pd.Series=None):
    """
    Prix merchant (marche) - DEJA incl. inflation.

    ATTENTION: le scenario de prix marche extrait de l'Excel (ass_Market) est deja un
    prix NOMINAL incluant l'inflation (Portfolio r4607 = courbe_inflation * scenario).
    Il ne faut donc PAS lui reappliquer inflation.compute (sinon double comptage ~+9%).
    """
    prices = market_price.compute(m, a)

    assert(prices.index[0] == m.time[0])
    assert(prices.index[-1] == m.time[-1])

    return prices


def revenues(m:Model, a:Asset):
    """
    Revenu merchant EXACT, replique de l'Excel (Portfolio r3058 x r4607):
    production merchant (fenetres pre + post contrat) x prix marche (incl inflation),
    calcule en ANNUEL puis reparti sur les mois au prorata de la production.
    """
    log_header(a, 'compute merchant revenues (exact annual replication)')
    annual = annual_revenue_euros(m, a)
    return _distribute_annual_to_monthly(m, a, annual)


def annual_production_MWh(m:Model, a:Asset) -> dict[int, float]:
    """Production merchant annuelle (MWh): fenetres pre-contrat + post-contrat."""
    windows = [
        (a.merchant_pre_contract_start, a.merchant_pre_contract_end),
        (a.merchant_post_contract_start, a.merchant_post_contract_end),
    ]
    return production.annual_production_MWh(m, a, windows)


def annual_revenue_euros(m:Model, a:Asset) -> dict[int, float]:
    """Revenu merchant annuel (euros) = production(y) * prix_marche(y) [incl inflation]."""
    prod = annual_production_MWh(m, a)
    if not prod:
        return {}
    price = market_price.compute(m, a)
    price_by_year = {int(y): float(v) for y, v in price.groupby(price.index.year).first().items()}
    return {y: p * price_by_year.get(y, 0.0) for y, p in prod.items()}


def _distribute_annual_to_monthly(m:Model, a:Asset, annual:dict[int, float]) -> pd.Series:
    """Repartit chaque total annuel sur les mois au prorata de la production merchant mensuelle."""
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

