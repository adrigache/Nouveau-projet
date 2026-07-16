"""
CAPEX (investissement) et D&A (amortissement), replique de l'Excel (onglet SPV, blocs
CF r72 "CAPEX" et P&L r141 "D&A" <- r427-430).

- CAPEX : cout de construction (ass_Asset : type1/type2/vehicle/perimeter), decaisse selon
  l'echeancier de paiements par actif (ass_Asset r330-425, periode mensuelle 1 <-> model.time[0]).
  Convention : k€, negatif (sortie de cash).
- D&A   : chaque tranche de CAPEX decaissee au mois s s'amortit lineairement sur sa duree
  (mois) a partir de son decaissement. Groupe A = type1 + vehicle + perimeter (240 mois),
  groupe B = type2 (120 mois). Chaque categorie est decaissee selon le meme profil que
  l'echeancier global (repartition au prorata). Sur l'horizon, l'amortissement cumule
  reproduit exactement le CAPEX (tout est amorti).
"""
import datetime as dt

import numpy as np
import pandas as pd

from mca_model import Model, Asset
from mca_model.service import helpers


def _capex(a: Asset) -> dict:
    return getattr(a, 'capex', None) or {}


def total_capex_keur(a: Asset) -> float:
    c = _capex(a)
    return c.get('type1', 0.0) + c.get('type2', 0.0) + c.get('vehicle', 0.0) + c.get('perimeter', 0.0)


def _disbursement(m: Model, a: Asset) -> np.ndarray:
    """Decaissement mensuel du CAPEX total (k€, positif) aligne sur model.time."""
    n = len(m.time)
    out = np.zeros(n, dtype=float)
    sched = getattr(a, 'capex_schedule', None) or {}
    periods = sched.get('periods', [])
    amounts = sched.get('amounts', [])
    for p, amt in zip(periods, amounts):
        i = int(p) - 1                 # periode mensuelle 1 <-> model.time[0]
        if 0 <= i < n:
            out[i] += float(amt)
    return out


def capex(m: Model, a: Asset, **kwargs) -> pd.Series:
    """CAPEX (k€, negatif) selon l'echeancier de decaissement par actif."""
    return pd.Series(-_disbursement(m, a), index=m.time)


def _year_first_index(m: Model) -> dict:
    """annee -> index du 1er mois de cette annee dans model.time."""
    out = {}
    for i, t in enumerate(m.time):
        if t.year not in out:
            out[t.year] = i
    return out


def _straight_line_window(m: Model, total: float, start: dt.date, months: int) -> np.ndarray:
    """
    Amortissement sur une fenetre de dates (vehicle/perimeter) : total reparti sur
    [start, start + months) au prorata JOURNALIER exact (convention Excel : injection date
    -> +240 mois). Les annees bissextiles amortissent un peu plus (366 j) : reproduit l'Excel.
    """
    n = len(m.time)
    out = np.zeros(n)
    if total == 0 or start is None or months <= 0:
        return out
    if isinstance(start, dt.datetime):
        start = start.date()
    end = (pd.Timestamp(start) + pd.DateOffset(months=months)).date()   # exclue
    total_days = (end - start).days
    if total_days <= 0:
        return out
    for i, t in enumerate(m.time):
        month_start = (t - pd.offsets.MonthBegin(1)).date()
        month_end = (t + pd.offsets.MonthEnd(0)).date()               # inclus
        t0 = max(month_start, start)
        t1 = min(month_end, end - dt.timedelta(days=1))               # borne haute incluse
        if t1 >= t0:
            out[i] = total * ((t1 - t0).days + 1) / total_days
    return out


def depreciation(m: Model, a: Asset, **kwargs) -> pd.Series:
    """
    D&A total (k€, negatif). Deux conventions Excel distinctes :
      - type1 (240 mois) / type2 (120 mois) : amortissement 'comptable annuel'. Les tranches
        decaissees une annee y s'amortissent a taux plein 1/duree des JANVIER de y, sur des annees
        civiles pleines (D&A(y) = cumul des tranches amortissables / duree). Le vehicle+perimeter
        est retire des tranches amortissables de son annee d'injection (convention Excel r393).
      - vehicle + perimeter : fenetre de dates [injection date, +240 mois], prorata journalier.
    """
    cfg = getattr(m, 'da_months', {}) or {}
    dur1 = int(cfg.get('type1', 240))
    dur2 = int(cfg.get('type2', 120))
    dur_vp = int(cfg.get('vehicle', dur1))

    c = _capex(a)
    cap1 = c.get('type1', 0.0)
    cap2 = c.get('type2', 0.0)
    cap_vp_asset = max(c.get('vehicle', 0.0) + c.get('perimeter', 0.0), 0.0)

    # Excel r413/r420 : CAPEX @Vehicle/@Perimeter = somme ass_Asset (actifs actifs
    # ET inactifs du SPV). Les actifs TOML n'en portent parfois qu'une fraction
    # (ex. SPV_5 : 10 vs 350). Le reliquat est applique une fois sur le 1er actif.
    spv = a.parent
    assets = list(getattr(spv, 'assets', []) or [])
    is_first = bool(assets) and a is assets[0]
    spv_veh = float(getattr(spv, 'da_vehicle_capex', 0.0) or 0.0)
    spv_peri = float(getattr(spv, 'da_perimeter_capex', 0.0) or 0.0)
    assets_vp = sum(
        max((getattr(x, 'capex', None) or {}).get('vehicle', 0.0)
            + (getattr(x, 'capex', None) or {}).get('perimeter', 0.0), 0.0)
        for x in assets
    ) if is_first else 0.0
    # Si da_vehicle_capex vient encore de ass_Vehicle (sous-estime), ne pas
    # retirer du VP actif : missing = max(0, spv - assets).
    missing_vp = max(spv_veh + spv_peri - assets_vp, 0.0) if is_first else 0.0
    cap_vp = cap_vp_asset + missing_vp

    total = cap1 + cap2 + cap_vp
    if total == 0:
        return pd.Series(0.0, index=m.time)

    start_vp = getattr(spv, 'da_vehicle_start', None)
    if isinstance(start_vp, dt.datetime):
        start_vp = start_vp.date()

    n = len(m.time)
    disb = _disbursement(m, a)                       # decaissement total (positif, k€)
    yearly = pd.Series(disb, index=m.time).groupby(m.time.year).sum()

    # tranches amortissables type1+type2 = decaissement total moins vehicle/perimeter,
    # ce dernier etant injecte en une fois (retire de son annee d'injection).
    amort = yearly.copy()
    if cap_vp > 0 and len(amort) > 0:
        inj_year = start_vp.year if start_vp is not None else int(amort.index[0])
        if inj_year not in amort.index:
            inj_year = int(amort.index[0])
        amort[inj_year] = amort.get(inj_year, 0.0) - cap_vp

    cap12 = cap1 + cap2
    share1 = (cap1 / cap12) if cap12 else (1.0 if not cap2 else 0.0)
    share2 = (cap2 / cap12) if cap12 else 0.0

    yf = _year_first_index(m)
    dep = np.zeros(n)
    for year, add in amort.items():
        if add == 0:
            continue
        i0 = yf.get(int(year))
        if i0 is None:
            continue
        if share1:
            dep[i0:min(i0 + dur1, n)] += add * share1 / dur1
        if share2:
            dep[i0:min(i0 + dur2, n)] += add * share2 / dur2

    if cap_vp > 0:
        dep += _straight_line_window(m, cap_vp, start_vp, dur_vp)
    return pd.Series(-dep, index=m.time)
