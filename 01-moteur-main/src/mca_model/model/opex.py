import pandas as pd
import numpy as np

from mca_model import Model, Asset
from mca_model.service import helpers
from mca_model.model import inflation
from mca_model.model.electricity import contracted, merchant, production


def _opex_period(opex: dict, a: Asset) -> tuple:
    start_date = opex.get('start date')
    if pd.isna(start_date) or start_date is None:
        start_date = a.operation_contract_start

    end_date = opex.get('end date')
    if pd.isna(end_date) or end_date is None:
        end_date = a.operation_contract_end

    return start_date, end_date


def _get_inflation(m: Model, opex: dict) -> pd.Series:
    """
    Inflation index applied to OPEX.
    Excel convention (validated to the cent on SPV_1): the index is an ANNUAL step,
    constant within each calendar year, not compounded month by month.
    """
    inflation_tag = opex.get('inflation')
    if inflation_tag and str(inflation_tag).lower() not in ['none', 'nan', '']:
        return inflation.compute_from_tag_annual(m, inflation_tag)
    return pd.Series(1.0, index=m.time)


def _production_mwh(m: Model, a: Asset) -> pd.Series:
    return contracted.in_MWh(m, a) + merchant.in_MWh(m, a)


def _annual_total_production_MWh(m: Model, a: Asset) -> dict:
    """Production annuelle totale (contractee + merchant), replique exacte Excel (R2555 + R3058)."""
    c = contracted.annual_production_MWh(m, a)
    mk = merchant.annual_production_MWh(m, a)
    years = set(c) | set(mk)
    return {y: c.get(y, 0.0) + mk.get(y, 0.0) for y in years}


def get_price_euros_by_MWh(m: Model, a: Asset, opex: dict) -> pd.Series:
    """
    OPEX variable (indexe sur la production), replique EXACTE de l'Excel (Portfolio, ex r5114):
        opex(y) = -(jours_periode_opex(y)/jours_annee) * prix * prod_annuelle(y) * inflation(y) * 1e-3
    ou prod_annuelle = production contractee + merchant de l'annee (R2555 + R3058).
    Le calcul est ANNUEL (comme l'Excel) puis reparti sur les mois au prorata de la
    production mensuelle (le total annuel reste exact au centime).
    """
    base_price = opex['price'][0]
    start_date, end_date = _opex_period(opex, a)

    prod_annual = _annual_total_production_MWh(m, a)
    inflation_index = _get_inflation(m, opex)
    infl_annual = inflation_index.groupby(inflation_index.index.year).first()

    # cout annuel (k€), signe negatif (sortie de cash)
    annual_cost = {}
    for y, prod in prod_annual.items():
        if prod == 0:
            continue
        dfrac = production.days_in_window_year(y, start_date, end_date) / production.days_in_year(y)
        infl = float(infl_annual.get(y, 1.0))
        annual_cost[y] = -dfrac * base_price * prod * infl * 1e-3

    return _distribute_annual_to_monthly(m, a, annual_cost)


def _distribute_annual_to_monthly(m: Model, a: Asset, annual: dict) -> pd.Series:
    """Repartit un cout annuel sur les mois au prorata de la production mensuelle totale."""
    prod_m = _production_mwh(m, a)
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


def get_price_euros_by_year(m: Model, a: Asset, opex: dict) -> pd.Series:
    """
    Calcule l'OPEX fixe (forfait annuel en k€).

    Convention Excel (validée au centime sur SPV_1) :
        opex_mois = -(jours_actifs_du_mois / jours_de_l_annee_civile) * base * inflation_annuelle
    Le forfait annuel est donc réparti au prorata des JOURS réels (et non 1/12 par mois),
    de sorte que la somme sur une année civile reproduit exactement la ligne Excel.
    La base est supposée déjà dé-indexée à l'année de départ d'inflation (colonne « Index »).
    """
    base_price_keuros = opex['price'][0]

    start_date, end_date = _opex_period(opex, a)

    active_days_frac = helpers.days_in_range_per_month(m.time, start_date, end_date)
    active_days = active_days_frac * m.time.days_in_month.values

    days_in_year = pd.Series(
        [366 if leap else 365 for leap in m.time.is_leap_year],
        index=m.time,
    )

    inflation_index = _get_inflation(m, opex)
    cost_keuros = base_price_keuros * (active_days / days_in_year) * inflation_index

    return -cost_keuros


def get_price(m: Model, a: Asset, **kwargs) -> pd.Series:
    """
    Point d'entrée de l'OPEX pour un Actif.
    Somme tous les contrats OPEX (O&M, Management, etc.) rattachés à cet actif.
    """
    total_opex = pd.Series(0.0, index=m.time)

    if not hasattr(a, 'OPEX') or not a.OPEX:
        return total_opex

    for opex_contract in a.OPEX:
        unit = opex_contract['price'][1]

        if unit == '€/MWh':
            cost = get_price_euros_by_MWh(m, a, opex_contract)
        elif unit == 'k€/year':
            cost = get_price_euros_by_year(m, a, opex_contract)
        else:
            raise NotImplementedError(f"OPEX unit unknown: {unit}")

        total_opex = total_opex.add(cost, fill_value=0)

    return total_opex
