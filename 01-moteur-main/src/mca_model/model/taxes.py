"""
Taxes locales (onglet SPV, ligne "Total local taxes" = r387 = CVAE + IFER + Other).

Replique EXACTE de l'Excel :
  - IFER (Portfolio r9148)   : forfait annuel = capacite_injectee(kW) * taux * inflation,
                               charge chaque annee civile ou l'actif produit et >= date de
                               debut (COD arrondi au 1er janvier). Taux = taux_avant pendant
                               `years` ans depuis le debut, puis taux_apres.
  - Other taxes (r9652)      : forfait k€/an, prorata jours, inflation (identique OPEX k€/an).
  - CVAE (r379, niveau SPV)  : sur la valeur ajoutee (CA - opex hors loyer), plafonnee, x bareme
                               (2022-2029), + taxe CCI ; nulle hors periode du bareme.

Toutes les composantes sont calculees en ANNUEL (comme l'Excel) puis reparties sur les mois
au prorata de la production (le total annuel/par SPV reste exact au centime).
"""
import datetime as dt
from collections import defaultdict

import pandas as pd

from mca_model import Model, Asset
from mca_model.model import inflation, opex
from mca_model.model.electricity import contracted, merchant, production


# ---------------------------------------------------------------------------
# IFER
# ---------------------------------------------------------------------------
def _ifer_start(ref: dt.date) -> dt.date:
    """Excel : COD si deja un 1er janvier, sinon le 1er janvier suivant."""
    if ref.month == 1 and ref.day == 1:
        return dt.date(ref.year, 1, 1)
    return dt.date(ref.year + 1, 1, 1)


def _annual_total_production_MWh(m: Model, a: Asset) -> dict:
    c = contracted.annual_production_MWh(m, a)
    mk = merchant.annual_production_MWh(m, a)
    years = set(c) | set(mk)
    return {y: c.get(y, 0.0) + mk.get(y, 0.0) for y in years}


def ifer(m: Model, a: Asset) -> pd.Series:
    spec = getattr(a, 'IFER', None)
    if not spec or not spec.get('capacity_kW'):
        return pd.Series(0.0, index=m.time)

    cap = float(spec['capacity_kW'])
    rate_before = float(spec['rate_before'])
    rate_after = float(spec['rate_after'])
    years = int(spec['years'])

    start = _ifer_start(a.merchant_pre_contract_start)
    switch = dt.date(start.year + years, start.month, start.day)  # EDATE(H, 12*years)

    infl = inflation.compute_from_tag_annual(m, spec.get('inflation', 'IPC'))
    infl_annual = infl.groupby(infl.index.year).first()

    prod = _annual_total_production_MWh(m, a)
    annual = {}
    for y, p in prod.items():
        if p <= 0 or dt.date(y, 1, 1) < start:
            continue
        rate = rate_before if switch > dt.date(y, 12, 31) else rate_after
        annual[y] = -cap * rate * float(infl_annual.get(y, 1.0)) * 1e-3

    return opex._distribute_annual_to_monthly(m, a, annual)


# ---------------------------------------------------------------------------
# Other taxes (identique OPEX k€/an)
# ---------------------------------------------------------------------------
def other_taxes(m: Model, a: Asset) -> pd.Series:
    out = pd.Series(0.0, index=m.time)
    for spec in getattr(a, 'OTHER_TAXES', None) or []:
        out = out.add(opex.get_price_euros_by_year(m, a, spec), fill_value=0)
    return out


# ---------------------------------------------------------------------------
# CVAE (niveau SPV)
# ---------------------------------------------------------------------------
def _spv_annual_bases(m: Model, spv) -> tuple[dict, dict, dict]:
    """CA, opex total, opex loyer par annee civile (k€) pour un SPV."""
    turnover = defaultdict(float)
    total_opex = defaultdict(float)
    rent = defaultdict(float)

    for a in spv.assets:
        cr = contracted.annual_revenue_euros(m, a)
        mr = merchant.annual_revenue_euros(m, a)
        for y, v in cr.items():
            turnover[y] += v / 1000.0
        for y, v in mr.items():
            turnover[y] += v / 1000.0

        op = opex.get_price(m, a)
        for y, v in op.groupby(op.index.year).sum().items():
            total_opex[int(y)] += float(v)

        for spec in getattr(a, 'OPEX', None) or []:
            if spec.get('name') == 'Loyer':
                rr = opex.get_price_euros_by_year(m, a, spec)
                for y, v in rr.groupby(rr.index.year).sum().items():
                    rent[int(y)] += float(v)

    return turnover, total_opex, rent


def cvae_spv_annual(m: Model, spv) -> dict:
    """Net CVAE annuel (k€, negatif) pour un SPV, replique de l'Excel (r379)."""
    cfg = getattr(m, 'cvae', None)
    if not cfg:
        return {}
    rate_by_year = {int(y): r for y, r in zip(cfg['years'], cfg['rate'])}
    cci_by_year = {int(y): r for y, r in zip(cfg['years'], cfg['cci'])}
    thr = float(cfg['va_threshold'])
    low = float(cfg['va_rate_low'])
    high = float(cfg['va_rate_high'])

    turnover, total_opex, rent = _spv_annual_bases(m, spv)

    out = {}
    for y in set(turnover) | set(total_opex):
        to = turnover.get(y, 0.0)
        opex_excl_rent = total_opex.get(y, 0.0) - rent.get(y, 0.0)
        added_value = to + opex_excl_rent
        limitation = (low if to <= thr else high) * to
        base = max(0.0, min(added_value, limitation))
        rate = rate_by_year.get(y, 0.0)
        gross = rate * base
        cci = cci_by_year.get(y, 0.0) * gross
        net = -(gross + cci)
        if net:
            out[y] = net
    return out


def cvae_asset_share(m: Model, a: Asset) -> pd.Series:
    """
    CVAE est calculee au niveau SPV : on l'attribue entierement au 1er actif du SPV
    (la somme par SPV reste exacte), repartie sur les mois au prorata de sa production.
    """
    spv = a.parent
    assets = spv.assets
    if not assets or assets[0] is not a:
        return pd.Series(0.0, index=m.time)

    annual = cvae_spv_annual(m, spv)
    return opex._distribute_annual_to_monthly(m, a, annual)


# ---------------------------------------------------------------------------
# Total (point d'entree cash-flow)
# ---------------------------------------------------------------------------
def total_local_taxes(m: Model, a: Asset) -> pd.Series:
    """IFER + Other taxes (par actif) + CVAE (niveau SPV, portee par le 1er actif)."""
    return ifer(m, a) + other_taxes(m, a) + cvae_asset_share(m, a)
