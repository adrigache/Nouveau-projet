"""
BFR (Working Capital Requirement) : creances clients + dettes fournisseurs.

Replique Excel (onglet SPV r435-446) — calcul ANNUEL puis projection mensuelle :
  receivables(y) = revenues(y) * days_receivables / days_in_year(y)
  payables(y)    = (-opex)(y) * days_payables / days_in_year(y)
  net_flow(y)    = (payables(y) - payables(y-1)) - (receivables(y) - receivables(y-1))

Parametres modulables (attributs SPV / TOML) :
  days_receivables (defaut 30), days_payables (defaut 30).
"""
import numpy as np
import pandas as pd

from mca_model import Model, Asset
from mca_model.model import opex
from mca_model.model.electricity import contracted, merchant


def _days_in_year(y: int) -> int:
    return 366 if (y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)) else 365


def _revenues_keur(m: Model, a: Asset) -> pd.Series:
    return (contracted.revenues(m, a) + merchant.revenues(m, a)) / 1000.0


def _expand_annual(m: Model, annual: dict) -> pd.Series:
    out = np.zeros(len(m.time))
    yrs = np.asarray(m.time.year)
    for y, val in annual.items():
        mask = yrs == int(y)
        n = int(mask.sum())
        if n and val:
            out[mask] = val / n
    return pd.Series(out, index=m.time)


def _wcr_stocks(m: Model, a: Asset) -> tuple[dict, dict, dict]:
    """Retourne (receivables, payables, net_flow) annuels en k€."""
    spv = a.parent
    d_recv = float(getattr(spv, 'days_receivables', 30) or 30)
    d_pay = float(getattr(spv, 'days_payables', 30) or 30)

    rev = _revenues_keur(m, a).groupby(m.time.year).sum()
    ox = (-opex.get_price(m, a)).groupby(m.time.year).sum()  # positif

    years = sorted(set(int(y) for y in m.time.year))
    recv, pay, flow = {}, {}, {}
    prev_r = prev_p = 0.0
    for y in years:
        diy = _days_in_year(y)
        recv[y] = float(rev.get(y, 0.0)) * d_recv / diy
        pay[y] = float(ox.get(y, 0.0)) * d_pay / diy
        flow[y] = (pay[y] - prev_p) - (recv[y] - prev_r)
        prev_r, prev_p = recv[y], pay[y]
    return recv, pay, flow


def _expand_stock(m: Model, annual: dict) -> pd.Series:
    """Stock de fin d'annee diffuse sur tous les mois (sans /12)."""
    out = np.zeros(len(m.time))
    yrs = np.asarray(m.time.year)
    for y, val in annual.items():
        out[yrs == int(y)] = val
    return pd.Series(out, index=m.time)


def trade_receivables_stock(m: Model, a: Asset, **kwargs) -> pd.Series:
    """Stock creances clients (k€) — stock de fin d'annee."""
    recv, _, _ = _wcr_stocks(m, a)
    return _expand_stock(m, recv)


def trade_payables_stock(m: Model, a: Asset, **kwargs) -> pd.Series:
    """Stock dettes fournisseurs (k€)."""
    _, pay, _ = _wcr_stocks(m, a)
    return _expand_stock(m, pay)


def net_flow_of_WCR(m: Model, a: Asset, **kwargs) -> pd.Series:
    """Variation nette du BFR (k€). Profil annuel exact Excel ; etale sur les mois."""
    _, _, flow = _wcr_stocks(m, a)
    # a la fin de vie Excel libererait le stock ; sur notre horizon le terminal
    # n'est pas force (coherent avec totaux EoP Excel ~ 0 via last actual).
    return _expand_annual(m, flow)
