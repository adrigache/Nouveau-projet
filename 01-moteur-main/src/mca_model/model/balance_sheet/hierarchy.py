"""
Detentions Holdco/Topco — aggregation des stocks filiales.

Excel Holdco B/S :
  r159 Share capital in vehicle detention = Σ (SC filiale × % detention)
  r160 SHL in SPVs                       = Σ (SHL filiale × % detention)
  r174 Cash pooling with vehicle detention = Σ CP actif filiales (passif holdco)

Generique : parcours ``vehicle.children`` (SPV ou Holdco), ponderes par
``detention_pct`` (defaut 1.0 = 100 %).
"""
from __future__ import annotations

import pandas as pd

from mca_model import Model
from mca_model.plumbing.nodes import HoldCo, Node, SPV, TopCo
from mca_model.model import financing as fin_mod
from mca_model.model.balance_sheet import functions as bf


def _detention_pct(node: Node) -> float:
    pct = getattr(node, 'detention_pct', 1.0)
    if pct is True:
        return 1.0
    if pct is False:
        return 0.0
    try:
        return float(pct)
    except (TypeError, ValueError):
        return 1.0


def _sum_spv_fn(m: Model, spv: SPV, fn) -> pd.Series:
    out = pd.Series(0.0, index=m.time)
    for a in spv.assets:
        out = out + fn(m, a)
    return out


def _child_spvs(vehicle: Node) -> list[SPV]:
    """SPV detenus directement (ou via Holdco si Topco)."""
    if isinstance(vehicle, SPV):
        return []
    out: list[SPV] = []
    for child in vehicle.children:
        if isinstance(child, SPV):
            out.append(child)
        elif isinstance(child, (HoldCo, TopCo)):
            out.extend(_child_spvs(child))
    return out


def _direct_children_for_detention(vehicle: Node) -> list[Node]:
    """Enfants directs (Excel detention = 1 niveau)."""
    return list(getattr(vehicle, 'children', []) or [])


def share_capital_in_detention(m: Model, vehicle: Node) -> pd.Series:
    """Actif Holdco : capital social des SPV detenus (Excel r159)."""
    out = pd.Series(0.0, index=m.time)
    for child in _direct_children_for_detention(vehicle):
        if not isinstance(child, SPV):
            continue
        out = out + _sum_spv_fn(m, child, bf.share_capital) * _detention_pct(child)
    return out


def shl_in_detention(m: Model, vehicle: Node) -> pd.Series:
    """Actif Holdco : SHL octroyes aux SPV (Excel r160)."""
    out = pd.Series(0.0, index=m.time)
    for child in _direct_children_for_detention(vehicle):
        if not isinstance(child, SPV):
            continue
        out = out + _sum_spv_fn(m, child, bf.SHL) * _detention_pct(child)
    return out


def cash_pooling_in_detention(m: Model, vehicle: Node) -> pd.Series:
    """Passif Holdco : miroir des creances CP SPV (Excel r174)."""
    out = pd.Series(0.0, index=m.time)
    for child in _direct_children_for_detention(vehicle):
        if not isinstance(child, SPV):
            continue
        out = (
            out
            + _sum_spv_fn(m, child, bf.cash_pooling_with_shareholders)
            * _detention_pct(child)
        )
    return out


def ensure_spv_financing(m: Model, vehicle: Node) -> None:
    """Pre-calcule le financement de toutes les SPV sous le vehicule."""
    for spv in _child_spvs(vehicle):
        fin_mod.run_spv_financing(m, spv)


def spv_financing_stock(m: Model, spv: SPV, attr: str) -> pd.Series:
    """
    Stock bilan issu du moteur financement, meme sans actifs (ex. SPV_6).

    Remplace la somme asset-level quand ``spv.assets`` est vide.
    """
    res = fin_mod.run_spv_financing(m, spv)
    annual = getattr(res, attr)
    return fin_mod._expand_stock_annual_to_monthly(m, annual)


def empty_spv_nbv(m: Model, spv: SPV) -> pd.Series:
    """
    NBV vehicle-only (Excel r430) : cumul des D&A P&L du chemin sans actifs.

    Asset EoP(y) = Σ ebit_DA(t) pour t ≤ y (dual amort. type1 / vehicle).
    """
    years = sorted({int(t.year) for t in m.time})
    da = fin_mod._spv_level_da_annual(m, spv, years)
    cum = 0.0
    annual = {}
    for y in years:
        cum += da.get(y, 0.0)
        annual[y] = cum
    return fin_mod._expand_stock_annual_to_monthly(m, annual)
