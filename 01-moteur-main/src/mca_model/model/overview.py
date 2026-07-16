"""
Overview = vue d'un vehicule selectionne (Excel ref_Vehicle → Computations).

Runtime : choisit une entite du modele (parametre), expose CFADS / B/S / check.
Pas de dependance Excel.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from mca_model import Model
from mca_model.plumbing.nodes import Node
from mca_model.model.balance_sheet import vehicle as vbs


@dataclass
class OverviewSnapshot:
    entity: str
    balance_sheet: dict[str, pd.Series]
    check_bs: pd.Series

    @property
    def total_assets(self) -> pd.Series:
        return self.balance_sheet['total_assets']

    @property
    def total_liabilities(self) -> pd.Series:
        return self.balance_sheet['total_liabilities']


def resolve_entity(m: Model, name: str | None = None) -> Node:
    """
    Entite Overview.

    Priorite : argument ``name`` > ``overview_entity`` (dashboard TOML) >
    premier Holdco > Topco.
    """
    if name:
        return m.get_object(name)
    cfg = getattr(m, 'overview_entity', None)
    if isinstance(cfg, str) and cfg:
        return m.get_object(cfg)
    holdcos = m.list_objects('HoldCo')
    if holdcos:
        return holdcos[0]
    return m.TopCo


def build_overview(m: Model, entity: str | None = None) -> OverviewSnapshot:
    node = resolve_entity(m, entity)
    bs = vbs.vehicle_balance_sheet(m, node)
    return OverviewSnapshot(
        entity=node.name,
        balance_sheet=bs,
        check_bs=bs['total_assets'] - bs['total_liabilities'],
    )
