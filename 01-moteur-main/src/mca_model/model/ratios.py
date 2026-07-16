"""
Ratios dette (Overview r137+).

HDSCR / LLCR / PLCR necessitent CFADS + service de la dette senior.
Tant que ``senior_schedule_mode = imported``, on utilise les series Holdco
(cfads, interest, repayment) — meme API quand le sculpting sera moteur.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from mca_model import Model
from mca_model.plumbing.nodes import HoldCo, Node, SPV
from mca_model.model.balance_sheet import vehicle as vbs
from mca_model.model import overview as ov


def _annual_last(series: pd.Series) -> dict[int, float]:
    """Stock/flux : valeur de fin d'annee (dernier mois)."""
    out = {}
    for y, g in series.groupby(series.index.year):
        out[int(y)] = float(g.iloc[-1])
    return out


def hdscr(m: Model, vehicle: Node | None = None) -> pd.Series:
    """
    Historical DSCR (Excel HDSCR) = CFADS / (interets + principal senior).

    0 si pas de dette senior / denominateur nul (SPV typiquement).
    """
    node = vehicle or ov.resolve_entity(m)
    bs = vbs.vehicle_balance_sheet(m, node)
    cfads = bs.get('cfads')
    interest = bs.get('senior_interest')
    repay = bs.get('senior_repayment')
    if cfads is None or interest is None or repay is None:
        return pd.Series(0.0, index=m.time)
    # Excel : interets/repay en cash out (negatif). Debt service = -(int+repay).
    ds = -(interest + repay)
    if float(repay.sum()) > 0:
        # repay positif = amortissement
        ds = (-interest) + repay
    ratio = pd.Series(0.0, index=m.time)
    mask = ds > 1e-9
    ratio[mask] = cfads[mask] / ds[mask]
    return ratio


def llcr(m: Model, vehicle: Node | None = None, discount_rate: float | None = None) -> pd.Series:
    """
    LLCR approx = NPV(CFADS restants) / Senior BoP.

    Discount : ``avg TL rate`` approx = -interest/senior si non fourni.
    """
    node = vehicle or ov.resolve_entity(m)
    bs = vbs.vehicle_balance_sheet(m, node)
    cfads = bs.get('cfads')
    senior = bs.get('senior')
    interest = bs.get('senior_interest')
    if cfads is None or senior is None:
        return pd.Series(0.0, index=m.time)

    years = sorted({int(t.year) for t in m.time})
    cf_a = _annual_last(cfads)
    sen_a = _annual_last(senior)
    int_a = _annual_last(interest) if interest is not None else {}

    out_annual = {y: 0.0 for y in years}
    for i, y in enumerate(years):
        bop = sen_a.get(y, 0.0)
        if bop <= 1e-9:
            continue
        if discount_rate is None:
            # taux moyen periodique
            r = 0.0
            if bop and int_a.get(y, 0.0):
                r = max(-int_a[y] / bop, 0.0)
        else:
            r = float(discount_rate)
        npv = 0.0
        for k, y2 in enumerate(years[i:]):
            npv += cf_a.get(y2, 0.0) / ((1.0 + r) ** k)
        out_annual[y] = npv / bop

    from mca_model.model import financing as fin_mod
    return fin_mod._expand_stock_annual_to_monthly(m, out_annual)


def plcr(m: Model, vehicle: Node | None = None, discount_rate: float | None = None) -> pd.Series:
    """PLCR : meme forme que LLCR sur l'horizon projet (ici = LLCR annualise)."""
    return llcr(m, vehicle, discount_rate=discount_rate)
