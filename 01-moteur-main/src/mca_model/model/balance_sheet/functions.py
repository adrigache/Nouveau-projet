"""
Bilan (B/S) — stocks de fin de periode (k€).

Convention : series alignees sur model.time (valeur de stock de l'annee civile
repartie uniformement sur les mois, comme le reste du moteur annuel).
Au niveau SPV, les postes vehicule sont portes par le 1er actif.
"""
from __future__ import annotations

import pandas as pd

from mca_model import Model, Asset
from mca_model.model import capex as capex_mod
from mca_model.model import financing as fin_mod
from mca_model.model import wcr as wcr_mod


# total_assets

def assets(m: Model, a: Asset, **kwargs) -> pd.Series:
    """
    Immobilisations nettes (NBV) : cumul CAPEX (−sortie) + cumul D&A (charge negative).
    NBV = (−CAPEX).cumsum() + D&A.cumsum().
    """
    cx = capex_mod.capex(m, a)
    da = capex_mod.depreciation(m, a)
    return (-cx).cumsum() + da.cumsum()


def _zero(m: Model) -> pd.Series:
    return pd.Series(0.0, index=m.time)


def share_capital_in_vehicle_detention(m: Model, a: Asset, **kwargs):
    """Au niveau SPV : 0. Aggregation Holdco → ``hierarchy.share_capital_in_detention``."""
    return _zero(m)


def SHL_in_SPVS(m: Model, a: Asset, **kwargs):
    """Au niveau SPV : 0. Aggregation Holdco → ``hierarchy.shl_in_detention``."""
    return _zero(m)


def cash_pooling_with_shareholders(m: Model, a: Asset, **kwargs) -> pd.Series:
    """Creance de cash pooling sur le holdco (actif SPV)."""
    return fin_mod.cash_pooling_balance(m, a)


def MDRA(m: Model, a: Asset, **kwargs):
    return _zero(m)


def MRA(m: Model, a: Asset, **kwargs):
    return _zero(m)


def proceeds_account(m: Model, a: Asset, **kwargs) -> pd.Series:
    """Cash proceeds account EoP (Excel r125 / B/S r164)."""
    return fin_mod.proceeds_balance(m, a)


def trade_receivables(m: Model, a: Asset, **kwargs) -> pd.Series:
    return wcr_mod.trade_receivables_stock(m, a)


# total_liabilities

def share_capital(m: Model, a: Asset, **kwargs) -> pd.Series:
    return fin_mod.share_capital_balance(m, a)


def legal_reserves(m: Model, a: Asset, **kwargs) -> pd.Series:
    return fin_mod.legal_reserves_balance(m, a)


def retained_earnings(m: Model, a: Asset, **kwargs) -> pd.Series:
    return fin_mod.retained_earnings_balance(m, a)


def crowdfunding(m: Model, a: Asset, **kwargs):
    return _zero(m)


def SHL(m: Model, a: Asset, **kwargs) -> pd.Series:
    return fin_mod.shl_balance(m, a)


def cash_pooling_with_vehicle_detention(m: Model, a: Asset, **kwargs):
    """Au niveau SPV : 0. Aggregation Holdco → ``hierarchy.cash_pooling_in_detention``."""
    return _zero(m)


def senior_facility(m: Model, a: Asset, **kwargs):
    return _zero(m)


def DSRF_facility(m: Model, a: Asset, **kwargs):
    return _zero(m)


def EBL(m: Model, a: Asset, **kwargs):
    return _zero(m)


def junior_facility(m: Model, a: Asset, **kwargs):
    return _zero(m)


def VAT_facility_EoP(m: Model, a: Asset, **kwargs):
    return _zero(m)


def corporate_income_tax_payable(m: Model, a: Asset, **kwargs) -> pd.Series:
    return fin_mod.cit_payable_balance(m, a)


def crowdfunding_interest_payable(m: Model, a: Asset, **kwargs):
    return _zero(m)


def junior_facility_interests_payable(m: Model, a: Asset, **kwargs):
    return _zero(m)


def SHL_interest_payable(m: Model, a: Asset, **kwargs) -> pd.Series:
    return fin_mod.shl_interest_payable_balance(m, a)


def trade_payables(m: Model, a: Asset, **kwargs) -> pd.Series:
    return wcr_mod.trade_payables_stock(m, a)
