"""
Bilan au niveau vehicule (SPV / Holdco / Topco).

- SPV avec actifs : somme des composants asset-level (entries.py)
- SPV vide : NBV vehicle + stocks financement (hierarchy)
- Holdco/Topco : detentions calculees + stocks propres
  (schedules importes tant que le P&L Holdco n'est pas entierement moteur)
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd
import tomllib

from mca_model import Model
from mca_model.plumbing.nodes import HoldCo, Node, SPV, TopCo
from mca_model.model import financing as fin_mod
from mca_model.model.balance_sheet import entries as bs
from mca_model.model.balance_sheet import functions as bf
from mca_model.model.balance_sheet import hierarchy as hier

_SCHEDULES_NAME = 'holdco_schedules.toml'


@lru_cache(maxsize=4)
def _load_holdco_schedules(path: str) -> dict:
    p = Path(path)
    if not p.is_file():
        return {}
    with open(p, 'rb') as f:
        return tomllib.load(f)


def holdco_schedules_path(m: Model) -> Path | None:
    """Cherche holdco_schedules.toml (cwd/test/assets ou voisin du package)."""
    here = Path(__file__).resolve()
    candidates = [
        Path.cwd() / 'test' / 'assets' / _SCHEDULES_NAME,
        here.parents[4] / 'test' / 'assets' / _SCHEDULES_NAME,  # .../01-moteur-main
        here.parents[5] / 'test' / 'assets' / _SCHEDULES_NAME,
    ]
    src = getattr(m, '_source_path', None)
    if src:
        candidates.insert(0, Path(src).resolve().parent / _SCHEDULES_NAME)
    for cand in candidates:
        if cand.is_file():
            return cand
    return None


def _schedules_for(m: Model, name: str) -> dict:
    path = holdco_schedules_path(m)
    if path is None:
        return {}
    doc = _load_holdco_schedules(str(path.resolve()))
    return dict(doc.get(name) or {})


def _annual_to_stock(m: Model, annual: dict) -> pd.Series:
    if not annual:
        return pd.Series(0.0, index=m.time)
    norm = {int(k): float(v) for k, v in annual.items()}
    return fin_mod._expand_stock_annual_to_monthly(m, norm)


def _sum_assets(m: Model, spv: SPV, fn) -> pd.Series:
    out = pd.Series(0.0, index=m.time)
    for a in spv.assets:
        out = out + fn(m, a)
    return out


def spv_balance_sheet(m: Model, spv: SPV) -> dict[str, pd.Series]:
    """Composants B/S d'un SPV (avec ou sans actifs)."""
    if spv.assets:
        return {
            'nbv': _sum_assets(m, spv, bf.assets),
            'sc_detention': _sum_assets(m, spv, bf.share_capital_in_vehicle_detention),
            'shl_detention': _sum_assets(m, spv, bf.SHL_in_SPVS),
            'cp_asset': _sum_assets(m, spv, bf.cash_pooling_with_shareholders),
            'proceeds': _sum_assets(m, spv, bf.proceeds_account),
            'receivables': _sum_assets(m, spv, bf.trade_receivables),
            'share_capital': _sum_assets(m, spv, bf.share_capital),
            'legal_reserves': _sum_assets(m, spv, bf.legal_reserves),
            'retained_earnings': _sum_assets(m, spv, bf.retained_earnings),
            'shl': _sum_assets(m, spv, bf.SHL),
            'cp_liability': _sum_assets(m, spv, bf.cash_pooling_with_vehicle_detention),
            'senior': _sum_assets(m, spv, bf.senior_facility),
            'ebl': _sum_assets(m, spv, bf.EBL),
            'vat': _sum_assets(m, spv, bf.VAT_facility_EoP),
            'cit_payable': _sum_assets(m, spv, bf.corporate_income_tax_payable),
            'payables': _sum_assets(m, spv, bf.trade_payables),
            'total_assets': _sum_assets(m, spv, bs.total_assets),
            'total_liabilities': _sum_assets(m, spv, bs.total_liabilities),
        }
    # Empty SPV (ex. SPV_6)
    fin_mod.run_spv_financing(m, spv)
    nbv = hier.empty_spv_nbv(m, spv)
    proc = hier.spv_financing_stock(m, spv, 'proceeds_eop')
    re = hier.spv_financing_stock(m, spv, 'retained_earnings_eop')
    cit = hier.spv_financing_stock(m, spv, 'cit_payable_eop')
    sc = hier.spv_financing_stock(m, spv, 'share_capital_eop')
    shl = hier.spv_financing_stock(m, spv, 'shl_eop')
    z = pd.Series(0.0, index=m.time)
    ta = nbv + proc
    tl = sc + re + shl + cit
    return {
        'nbv': nbv, 'sc_detention': z, 'shl_detention': z, 'cp_asset': z,
        'proceeds': proc, 'receivables': z, 'share_capital': sc,
        'legal_reserves': z, 'retained_earnings': re, 'shl': shl,
        'cp_liability': z, 'senior': z, 'ebl': z, 'vat': z,
        'cit_payable': cit, 'payables': z,
        'total_assets': ta, 'total_liabilities': tl,
    }


def holdco_balance_sheet(m: Model, holdco: HoldCo | TopCo) -> dict[str, pd.Series]:
    """
    B/S Holdco = detentions (moteur) + postes propres.

    Postes propres : schedules TOML ``holdco_schedules.toml`` tant que
    ``senior_schedule_mode = "imported"``. Remplacables progressivement
    par le moteur sans changer l'API.
    """
    hier.ensure_spv_financing(m, holdco)
    sch = _schedules_for(m, holdco.name)
    z = pd.Series(0.0, index=m.time)

    sc_det = hier.share_capital_in_detention(m, holdco)
    shl_det = hier.shl_in_detention(m, holdco)
    cp_det = hier.cash_pooling_in_detention(m, holdco)

    nbv = _annual_to_stock(m, sch.get('own_nbv_annual') or {})
    proceeds = _annual_to_stock(m, sch.get('own_proceeds_annual') or {})
    recv = _annual_to_stock(m, sch.get('own_trade_receivables_annual') or {})
    sc = _annual_to_stock(m, sch.get('own_share_capital_annual') or {})
    lr = _annual_to_stock(m, sch.get('own_legal_reserves_annual') or {})
    re = _annual_to_stock(m, sch.get('own_retained_earnings_annual') or {})
    shl = _annual_to_stock(m, sch.get('own_shl_annual') or {})
    senior = _annual_to_stock(m, sch.get('senior_eop_annual') or {})
    ebl = _annual_to_stock(m, sch.get('ebl_eop_annual') or {})
    vat = _annual_to_stock(m, sch.get('vat_facility_eop_annual') or {})
    cit = _annual_to_stock(m, sch.get('own_cit_payable_annual') or {})

    ta = nbv + sc_det + shl_det + proceeds + recv
    tl = sc + lr + re + shl + cp_det + senior + ebl + vat + cit
    return {
        'nbv': nbv,
        'sc_detention': sc_det,
        'shl_detention': shl_det,
        'cp_asset': z,
        'proceeds': proceeds,
        'receivables': recv,
        'share_capital': sc,
        'legal_reserves': lr,
        'retained_earnings': re,
        'shl': shl,
        'cp_liability': cp_det,
        'senior': senior,
        'ebl': ebl,
        'vat': vat,
        'cit_payable': cit,
        'payables': z,
        'total_assets': ta,
        'total_liabilities': tl,
        'cfads': _annual_to_stock(m, sch.get('own_cfads_annual') or {}),
        'senior_interest': _annual_to_stock(m, sch.get('senior_interest_annual') or {}),
        'senior_repayment': _annual_to_stock(m, sch.get('senior_repayment_annual') or {}),
    }


def vehicle_balance_sheet(m: Model, vehicle: Node) -> dict[str, pd.Series]:
    if isinstance(vehicle, SPV):
        return spv_balance_sheet(m, vehicle)
    if isinstance(vehicle, (HoldCo, TopCo)):
        return holdco_balance_sheet(m, vehicle)
    raise TypeError(f'unsupported vehicle type: {type(vehicle)}')


def check_vehicle_balance_sheet(m: Model, vehicle: Node) -> pd.Series:
    bs_ = vehicle_balance_sheet(m, vehicle)
    return bs_['total_assets'] - bs_['total_liabilities']
