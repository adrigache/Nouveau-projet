"""
Financement au niveau vehicule (SPV / Holdco / Topco).

Architecture modulable : chaque instrument (share capital, SHL, senior, DSRF, junior,
crowdfunding, cash pooling) est un bloc parametre. La cascade (waterfall) les enchaine
dans l'ordre ; un instrument inactif (montant/taux/flag a 0) contribue naturellement 0.

Dans le jeu de donnees actuel, au niveau SPV seul le SHL (et 1 k€ de share capital) est
actif ; senior/DSRF/junior/crowdfunding restent a 0. Le code les porte quand meme pour
qu'une activation via la config (TOML) les declenche sans modification du moteur.

Convention : k€. Calcul ANNUEL (comme l'onglet SPV Excel), puis projection mensuelle.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Callable

import numpy as np
import pandas as pd

from mca_model import Model, Asset
from mca_model.model import capex as capex_mod
from mca_model.model import wcr as wcr_mod
from mca_model.model.profit_loss import entries as pnl_entries


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _years(m: Model) -> list[int]:
    return sorted(set(int(y) for y in m.time.year))


def _annual_sum(series: pd.Series) -> dict[int, float]:
    if series is None or (isinstance(series, (int, float)) and series == 0):
        return {}
    if isinstance(series, (int, float)):
        return {}
    return {int(y): float(v) for y, v in series.groupby(series.index.year).sum().items()}


def _spv_assets(spv) -> list:
    return list(getattr(spv, 'assets', []) or [])


def _zero_annual(years: list[int]) -> dict[int, float]:
    return {y: 0.0 for y in years}


def _expand_annual_to_monthly(m: Model, annual: dict[int, float]) -> pd.Series:
    """Repartit une valeur annuelle (flux) uniformement sur les mois de l'annee."""
    out = np.zeros(len(m.time))
    yrs = np.asarray(m.time.year)
    for y, val in annual.items():
        mask = yrs == y
        n = int(mask.sum())
        if n and val:
            out[mask] = val / n
    return pd.Series(out, index=m.time)


def _expand_stock_annual_to_monthly(m: Model, annual: dict[int, float]) -> pd.Series:
    """Diffuse un stock de fin d'annee sur tous les mois de l'annee (sans /12)."""
    out = np.zeros(len(m.time))
    yrs = np.asarray(m.time.year)
    for y, val in annual.items():
        out[yrs == y] = val
    return pd.Series(out, index=m.time)


# ---------------------------------------------------------------------------
# Building blocks (modulables) : chaque instrument expose drawdown / interest / repay
# ---------------------------------------------------------------------------

@dataclass
class InstrumentState:
    """Etat courant d'un instrument de dette / equity pour la recursion annuelle."""
    name: str
    rate: float = 0.0
    capitalise: bool = False
    min_balance: float = 0.0
    min_active: bool = False
    bop: float = 0.0
    interest_payable_bop: float = 0.0


@dataclass
class SpvFinancingResult:
    """Resultats annuels du moteur de financement (par annee civile)."""
    years: list[int]
    shl_injection: dict[int, float] = field(default_factory=dict)
    shl_interest: dict[int, float] = field(default_factory=dict)          # negatif (charge)
    shl_interest_paid: dict[int, float] = field(default_factory=dict)     # negatif (cash out)
    shl_interest_capitalised: dict[int, float] = field(default_factory=dict)
    shl_repayment: dict[int, float] = field(default_factory=dict)         # negatif
    shl_eop: dict[int, float] = field(default_factory=dict)
    share_capital_drawdown: dict[int, float] = field(default_factory=dict)
    dividend_paid: dict[int, float] = field(default_factory=dict)         # negatif (cash out)
    dividend_offset_cp: dict[int, float] = field(default_factory=dict)    # negatif (drain CP)
    cash_pooling_addition: dict[int, float] = field(default_factory=dict)
    cash_pooling_interest: dict[int, float] = field(default_factory=dict)  # signe P&L (positif = produit)
    cash_pooling_eop: dict[int, float] = field(default_factory=dict)
    share_capital_eop: dict[int, float] = field(default_factory=dict)
    legal_reserves_eop: dict[int, float] = field(default_factory=dict)
    retained_earnings_eop: dict[int, float] = field(default_factory=dict)
    shl_interest_payable_eop: dict[int, float] = field(default_factory=dict)
    cit_payable_eop: dict[int, float] = field(default_factory=dict)
    ebitda: dict[int, float] = field(default_factory=dict)
    ebit: dict[int, float] = field(default_factory=dict)
    ebt: dict[int, float] = field(default_factory=dict)
    taxable_income: dict[int, float] = field(default_factory=dict)
    cit_due: dict[int, float] = field(default_factory=dict)               # negatif (charge)
    cit_paid: dict[int, float] = field(default_factory=dict)              # negatif (cash out)
    net_result: dict[int, float] = field(default_factory=dict)
    cfads: dict[int, float] = field(default_factory=dict)                 # Excel r91 (incl. proceeds BoP)
    proceeds_eop: dict[int, float] = field(default_factory=dict)          # Excel r125 / B/S r164


def _share_capital_drawdown_annual(m: Model, spv, years: list[int],
                                   capex_annual: dict[int, float]) -> dict[int, float]:
    """
    Share capital : 1 k€ a la premiere annee de decaissement CAPEX (Excel r1162/r456).
    Parametrable via spv.share_capital_amount (defaut 1.0).
    """
    out = _zero_annual(years)
    amount = float(getattr(spv, 'share_capital_amount', 1.0) or 0.0)
    if amount == 0:
        return out
    for y in years:
        if abs(capex_annual.get(y, 0.0)) > 1e-9:
            out[y] = amount
            break
    return out


def _shl_injection_annual(capex_annual: dict[int, float],
                          share_capital: dict[int, float],
                          years: list[int],
                          other_sources: dict[int, float] | None = None) -> dict[int, float]:
    """
    Injection SHL = CAPEX (positif) - share capital - autres sources de financement
    (senior drawdown, etc.). Modulable : other_sources absorbe tout instrument amont.
    """
    other = other_sources or {}
    out = {}
    for y in years:
        uses = -capex_annual.get(y, 0.0)          # CAPEX serie est negative
        funded = share_capital.get(y, 0.0) + other.get(y, 0.0)
        out[y] = max(uses - funded, 0.0)
    return out


def _tax_cfg(m: Model) -> dict:
    return getattr(m, 'tax', None) or {}


def _cit_due_annual(ebit: float, interest: float, ebitda: float, shl_bop: float,
                    equity_bop: float, deferred_int_bop: float, cfg: dict,
                    financial_income: float = 0.0):
    """
    Calcule taxable income (avant deficits), stock d'interets diferes EoP.

    Replique Excel r279-316 :
      - NFC (r282) = -(interets dette + produits financiers)  [P&L signs]
      - ATAD s'applique a max(NFC, 0)
      - taxable = EBIT + interest + financial_income + nonded - reint
        (= EBIT + (-NFC) +/- ATAD)

    ``financial_income`` : produits financiers inclus dans la base IS
    (ex. interets de cash pooling, r149). Parametrable via
    ``tax.cit_include_cash_pooling`` (defaut True, fidèle Excel).
    """
    thin_ratio = float(cfg.get('thin_cap_ratio', 1.5))
    t1_floor = float(cfg.get('atad_t1_floor', 3000.0))
    t1_rate = float(cfg.get('atad_t1_rate', 0.30))
    t2_floor = float(cfg.get('atad_t2_floor', 1000.0))
    t2_rate = float(cfg.get('atad_t2_rate', 0.10))
    deferral_pct = float(cfg.get('atad_deferral_pct', 1.0 / 3.0))

    # Excel r282 : NFC = -(SHL + senior + ... + cash pooling + ...)
    nfc_net = -interest - financial_income
    nfc = max(nfc_net, 0.0)                                  # charge nette pour ATAD
    thin_cap = shl_bop > equity_bop * thin_ratio
    total_debt = shl_bop                                     # + external (=0)

    if total_debt > 0:
        part1 = min((max(thin_ratio * equity_bop, 0.0)) / total_debt, 1.0)
        part2 = max(0.0, (shl_bop - max(thin_ratio * equity_bop, 0.0)) / total_debt)
    else:
        part1 = part2 = 0.0

    fc1 = nfc * part1
    fc2 = nfc * part2
    lim1 = max(t1_floor, t1_rate * ebitda) * part1
    lim2 = max(t2_floor, t2_rate * ebitda) * part2
    ded1 = min(fc1, lim1)
    ded2 = min(fc2, lim2)
    nonded1 = max(0.0, fc1 - ded1)
    nonded2 = max(0.0, fc2 - ded2)
    reintegrated = min(max(lim1 - fc1, 0.0), deferred_int_bop)
    nonded = nonded1 + nonded2

    if thin_cap:
        disallowed = nonded1 + nonded2 * deferral_pct
    else:
        disallowed = nonded1
    deferred_eop = deferred_int_bop + disallowed - reintegrated

    # Excel r316 = EBIT fiscal + (-NFC) + ATAD adj.  (-NFC = interest + financial_income)
    taxable = ebit + interest + financial_income + nonded - reintegrated
    return taxable, deferred_eop


def _all_spvs(m: Model) -> list:
    """Tous les SPV du modele (via assets → parent)."""
    seen = {}
    for a in m.list_assets():
        spv = a.parent
        seen[spv.name] = spv
    return list(seen.values())


def _portfolio_revenues_annual(m: Model, years: list[int]) -> dict[int, float]:
    """CA agregé portefeuille (k€) — sert au flag CSB (seuil de CA)."""
    from mca_model.model.electricity import contracted, merchant
    out = _zero_annual(years)
    for a in m.list_assets():
        rev = (contracted.revenues(m, a) + merchant.revenues(m, a)) / 1000.0
        for y, v in _annual_sum(rev).items():
            out[y] = out.get(y, 0.0) + v
    return out


def _spv_level_da_annual(m: Model, spv, years: list[int]) -> dict[int, float]:
    """
    D&A vehicule / perimeter au niveau SPV quand il n'y a pas d'actifs (ex. SPV_6).

    Replique Excel r393/r413/r414/r429 :
      - add type1 = -da_vehicle_capex (si aucun CAPEX actif) l'annee d'injection
      - D&A type1 annuel = -add / 20 ans  (signe P&L)
      - D&A vehicle = amortissement lineaire journalier sur 240 mois
    EoP net ~ 0 ; le timing cree l'IS 'last actual' (~1 k€).
    """
    out = _zero_annual(years)
    if _spv_assets(spv):
        return out
    veh = float(getattr(spv, 'da_vehicle_capex', 0.0) or 0.0)
    peri = float(getattr(spv, 'da_perimeter_capex', 0.0) or 0.0)
    cap_vp = veh + peri
    if abs(cap_vp) < 1e-12:
        return out
    start = getattr(spv, 'da_vehicle_start', None)
    if isinstance(start, dt.datetime):
        start = start.date()
    if start is None:
        t0 = m.time[0]
        start = t0.date() if hasattr(t0, 'date') else t0
    cfg = getattr(m, 'da_months', {}) or {}
    dur_vp = int(cfg.get('vehicle', 240))
    dur1_years = 20  # Excel I395 (colonnes annuelles)
    n = len(m.time)
    dep = np.zeros(n)
    inj_year = int(start.year)
    yf = {}
    for i, t in enumerate(m.time):
        y = int(t.year)
        if y not in yf:
            yf[y] = i
    i0 = yf.get(inj_year, 0)
    months1 = dur1_years * 12
    # add type1 = -cap_vp → contribution dep negative → D&A P&L positive
    dep[i0:min(i0 + months1, n)] += (-cap_vp) / months1
    dep += capex_mod._straight_line_window(m, cap_vp, start, dur_vp)
    series = pd.Series(-dep, index=m.time)
    ann = _annual_sum(series)
    for y in years:
        out[y] = ann.get(y, 0.0)
    return out


def run_spv_financing(m: Model, spv) -> SpvFinancingResult:
    """
    Moteur recursif annuel au niveau SPV.

    Ordre Excel equity waterfall (r450-539), une annee a la fois :
      1. IS paye (lag) → CFADS ; CF actionnaires (flag distribution)
      2. Dividendes (RE BoP + net N-1 − reserves) + offset CP
      3. Interets / remboursement SHL (min SHL)
      4. Cash pooling (addition + interets)
      5. IS du : NFC = SHL + CP (si tax.cit_include_cash_pooling) + ATAD/deficits/CSB
      6. EBT = EBIT + SHL int + CP int ; Net = EBT + CIT due
    """
    years = _years(m)
    res = SpvFinancingResult(years=years)
    cfg = _tax_cfg(m)

    # --- Aggregats annuels pre-calcules (independants de la recursion dette) ---
    capex_annual = _zero_annual(years)
    ebit_annual = _zero_annual(years)
    ebitda_annual = _zero_annual(years)
    wcr_annual = _zero_annual(years)
    for a in _spv_assets(spv):
        for y, v in _annual_sum(capex_mod.capex(m, a)).items():
            capex_annual[y] = capex_annual.get(y, 0.0) + v
        for y, v in _annual_sum(pnl_entries.EBIT(m, a)).items():
            ebit_annual[y] = ebit_annual.get(y, 0.0) + v
        for y, v in _annual_sum(pnl_entries.EBITDA(m, a)).items():
            ebitda_annual[y] = ebitda_annual.get(y, 0.0) + v
        for y, v in _annual_sum(wcr_mod.net_flow_of_WCR(m, a)).items():
            wcr_annual[y] = wcr_annual.get(y, 0.0) + v
    # SPV sans actifs : D&A vehicle/perimeter (timing IS, ex. SPV_6)
    for y, v in _spv_level_da_annual(m, spv, years).items():
        ebit_annual[y] = ebit_annual.get(y, 0.0) + v
    res.ebit = ebit_annual
    res.ebitda = ebitda_annual

    other_debt_drawdown = _zero_annual(years)
    for attr in ('senior_drawdown_annual', 'dsrf_drawdown_annual',
                 'junior_drawdown_annual', 'crowdfunding_drawdown_annual'):
        extra = getattr(spv, attr, None) or {}
        for y, v in extra.items():
            other_debt_drawdown[int(y)] = other_debt_drawdown.get(int(y), 0.0) + float(v)

    share = _share_capital_drawdown_annual(m, spv, years, capex_annual)
    res.share_capital_drawdown = share
    shl_inj = _shl_injection_annual(capex_annual, share, years, other_debt_drawdown)
    res.shl_injection = shl_inj

    # Precompute portfolio revenues (for CSB flag : CA agregé) + SPV revenues (distribution flag)
    portfolio_rev = _portfolio_revenues_annual(m, years)
    from mca_model.model.electricity import contracted, merchant
    spv_rev = _zero_annual(years)
    for a in _spv_assets(spv):
        rev = (contracted.revenues(m, a) + merchant.revenues(m, a)) / 1000.0
        for y, v in _annual_sum(rev).items():
            spv_rev[y] = spv_rev.get(y, 0.0) + v
    # remaining revenues from year y to end (Excel SUM(Q206:BD206)>0)
    remaining_rev = {}
    run = 0.0
    for y in reversed(years):
        run += spv_rev.get(y, 0.0)
        remaining_rev[y] = run

    rate = float(getattr(spv, 'shl_rate', 0.0) or 0.0)
    capitalise = bool(getattr(spv, 'shl_capitalise', True))
    min_active = bool(getattr(spv, 'min_shl_activation', False))
    min_amt = float(getattr(spv, 'min_shl_amount', 0.0) or 0.0) if min_active else 0.0
    cp_rate = float(getattr(spv, 'cash_pooling_rate', 0.0) or 0.0)
    lr_target_ratio = float(getattr(spv, 'legal_reserve_ratio', 0.1) or 0.0)
    lr_funding_rate = float(getattr(spv, 'legal_reserve_funding_rate', 0.05) or 0.0)
    # Produits financiers (cash pooling) dans la base IS — defaut True (Excel r282/r149).
    # Desactivable via market.tax.cit_include_cash_pooling = false.
    cit_include_cp = bool(cfg.get('cit_include_cash_pooling', True))
    n_cit_deposits = int(cfg.get('cit_n_deposits', 4) or 4)
    cit_dep_f = 1.0 / max(n_cit_deposits, 1)

    # --- Recursion annuelle ---
    bop = 0.0
    interest_payable = 0.0
    deferred_int = 0.0
    loss_cf = 0.0                    # carried-forward tax losses (positif)
    re_div = 0.0                     # retained earnings (piste dividendes, Excel r488-493)
    retained_bs = 0.0                # retained earnings B/S (piste r502-507, thin-cap)
    net_prev = 0.0                   # net result N-1
    cit_due_prev = 0.0
    cit_due_prev2 = 0.0
    cit_dep_sum_prev = 0.0           # SUM acomptes N-1 (Excel r337)
    share_cap_eop = 0.0
    lr_eop = 0.0                     # legal reserves EoP
    cp_bop = 0.0                     # cash pooling balance BoP
    cit_payable = 0.0
    proceeds_bop = 0.0               # cash proceeds account BoP (Excel r59)

    for y in years:
        inj = shl_inj.get(y, 0.0)
        sc = share.get(y, 0.0)
        share_cap_eop += sc

        ebit = ebit_annual.get(y, 0.0)
        ebitda = ebitda_annual.get(y, 0.0)

        # Interets SHL (base = BoP + injections)
        balance_for_int = bop + inj
        interest = -max(balance_for_int, 0.0) * rate
        res.shl_interest[y] = interest

        # IS paye = acomptes + solde (Excel r332-339), independant de l'IS du N.
        d332 = max(-cit_due_prev2 * cit_dep_f, 0.0)
        d333 = max(
            -cit_dep_f * cit_due_prev + (cit_due_prev2 - cit_due_prev) * cit_dep_f,
            0.0,
        )
        d334 = max(-cit_due_prev * cit_dep_f, 0.0)
        d335 = max(-cit_due_prev * cit_dep_f, 0.0)
        cit_dep_sum = d332 + d333 + d334 + d335
        cit_balancing = -cit_due_prev - cit_dep_sum_prev
        cit_paid = -(cit_dep_sum + cit_balancing)
        if abs(cit_paid) < 1e-12:
            cit_paid = 0.0
        res.cit_paid[y] = cit_paid

        # CFADS Excel r91 = proceeds BoP + operating/invest lines (ici EBITDA+WCR+IS paye)
        period_cf = ebitda_annual.get(y, 0.0) + wcr_annual.get(y, 0.0) + cit_paid
        cfads = proceeds_bop + period_cf
        res.cfads[y] = cfads

        # Flag distribution (Excel r451 simplifie) : revenus restants > 0
        distrib = 1.0 if remaining_rev.get(y, 0.0) > 1e-9 else 0.0
        # Waterfall equity : uniquement le cash positif distribuable (hors BoP piege)
        cf_shareholders = max(period_cf, 0.0) * distrib

        # --- Reserves legales (Excel r461-466) ---
        lr_target = lr_target_ratio * share_cap_eop
        lr_funding = max(0.0, min(lr_target - lr_eop, net_prev * lr_funding_rate))
        lr_eop = lr_eop + lr_funding

        # --- Dividendes AVANT SHL (Excel r486-499) ---
        max_dist = max(re_div + net_prev - lr_funding, 0.0)
        cash_for_div = max(cf_shareholders, 0.0)
        dividend = -min(cash_for_div, max_dist) if max_dist > 0 else 0.0
        cp_offset = -min(cp_bop, max_dist + dividend) if (max_dist + dividend) > 0 else 0.0
        res.dividend_paid[y] = dividend
        res.dividend_offset_cp[y] = cp_offset
        re_div = re_div + net_prev - lr_funding + dividend + cp_offset

        # --- SHL sur cash restant apres dividendes (Excel r509-530) ---
        cash_shl = max(cf_shareholders + dividend, 0.0)
        due = -(interest) + interest_payable
        paid = -min(cash_shl, due) if due > 0 else 0.0
        capitalised = (paid - interest - interest_payable) * (1.0 if capitalise else 0.0)
        capitalised = max(capitalised, 0.0)
        res.shl_interest_paid[y] = paid
        res.shl_interest_capitalised[y] = capitalised

        cash_for_repay = max(cash_shl + paid, 0.0)
        balance_before_repay = bop + inj + capitalised
        floor = min_amt if min_active else 0.0
        max_repay = max(balance_before_repay - floor, 0.0)
        repay = -min(cash_for_repay, max_repay) * distrib
        res.shl_repayment[y] = repay

        eop = balance_before_repay + repay
        if abs(eop) < 1e-9:
            eop = 0.0
        res.shl_eop[y] = eop

        # --- Cash pooling (Excel r533-539) ---
        cp_addition = max(cash_for_repay + repay, 0.0)
        cp_interest = max(cp_bop + cp_addition, 0.0) * cp_rate
        cp_eop = cp_bop + cp_addition + cp_offset + cp_interest
        if abs(cp_eop) < 1e-12:
            cp_eop = 0.0
        res.cash_pooling_addition[y] = cp_addition
        res.cash_pooling_interest[y] = cp_interest
        res.cash_pooling_eop[y] = cp_eop

        # --- IS du APRES CP (Excel NFC r282 inclut r149) ---
        equity_bop = share_cap_eop - sc + retained_bs
        fin_income = cp_interest if cit_include_cp else 0.0
        taxable, deferred_int = _cit_due_annual(
            ebit, interest, ebitda, bop, equity_bop, deferred_int, cfg,
            financial_income=fin_income,
        )
        cit_rate = float(cfg.get('cit_rate', 0.25))
        loss_thr = float(cfg.get('loss_threshold', 1000.0))
        loss_prop = float(cfg.get('loss_proportion', 0.5))
        if taxable > 0 and loss_cf > 0:
            if taxable <= loss_thr:
                used = min(loss_cf, taxable)
            else:
                used = min(loss_cf, loss_thr + loss_prop * (taxable - loss_thr))
            used = -used
        else:
            used = 0.0
        loss_new = -min(taxable, 0.0)
        loss_cf = loss_cf + loss_new + used
        taxable_after = max(taxable + used, 0.0)
        cit_base = -taxable_after * cit_rate if taxable_after > 0 else 0.0
        csb_to = float(cfg.get('csb_turnover_threshold', 7630.0))
        csb_thr = float(cfg.get('csb_cit_threshold', 763.0))
        csb_rate = float(cfg.get('csb_rate', 0.033))
        flag_csb = 1.0 if portfolio_rev.get(y, 0.0) > csb_to else 0.0
        csb = -flag_csb * max(-cit_base - csb_thr, 0.0) * csb_rate
        cit_due = cit_base + csb
        res.taxable_income[y] = taxable
        res.cit_due[y] = cit_due

        ebt = ebit + interest + cp_interest
        res.ebt[y] = ebt
        net = ebt + cit_due
        res.net_result[y] = net

        # Proceeds EoP (Excel r125) = CFADS − cash sorti via waterfall equity
        outflow = -(dividend + paid + repay) + cp_addition
        proceeds_eop = cfads - outflow
        if abs(proceeds_eop) < 1e-12:
            proceeds_eop = 0.0
        res.proceeds_eop[y] = proceeds_eop

        # roll forward
        bop = eop
        interest_payable = interest_payable + interest - paid + capitalised
        if abs(interest_payable) < 1e-9:
            interest_payable = 0.0
        retained_bs = retained_bs + net - lr_funding + dividend + cp_offset
        cit_payable = cit_payable - cit_due + cit_paid
        if abs(cit_payable) < 1e-9:
            cit_payable = 0.0
        net_prev = net
        cp_bop = cp_eop
        cit_due_prev2 = cit_due_prev
        cit_due_prev = cit_due
        cit_dep_sum_prev = cit_dep_sum
        proceeds_bop = proceeds_eop

        res.share_capital_eop[y] = share_cap_eop
        res.legal_reserves_eop[y] = lr_eop
        res.retained_earnings_eop[y] = retained_bs
        res.shl_interest_payable_eop[y] = interest_payable
        res.cit_payable_eop[y] = cit_payable

    return res


# ---------------------------------------------------------------------------
# API asset-level (pour branchement P&L / CF) : porte le resultat SPV sur le 1er actif
# ---------------------------------------------------------------------------

_CACHE: dict[tuple[int, str], SpvFinancingResult] = {}


def _result_for(m: Model, a: Asset) -> SpvFinancingResult:
    spv = a.parent
    key = (id(m), spv.name)
    if key not in _CACHE:
        _CACHE[key] = run_spv_financing(m, spv)
    return _CACHE[key]


def clear_cache():
    _CACHE.clear()


def shl_interests_to_be_paid(m: Model, a: Asset, **kwargs) -> pd.Series:
    """
    Interets SHL (k€, negatif). Porte par le 1er actif du SPV (comme CVAE) pour
    eviter le double-compte dans sum_by_assets.
    """
    spv = a.parent
    assets = _spv_assets(spv)
    if not assets or a is not assets[0]:
        return pd.Series(0.0, index=m.time)
    res = _result_for(m, a)
    return _expand_annual_to_monthly(m, res.shl_interest)


def cash_pooling_interests(m: Model, a: Asset, **kwargs) -> pd.Series:
    """Interets de cash pooling (k€, positif = produit). Porte par le 1er actif."""
    spv = a.parent
    assets = _spv_assets(spv)
    if not assets or a is not assets[0]:
        return pd.Series(0.0, index=m.time)
    res = _result_for(m, a)
    return _expand_annual_to_monthly(m, res.cash_pooling_interest)


def corporate_income_tax_due(m: Model, a: Asset, **kwargs) -> pd.Series:
    """IS du (k€, negatif = charge). Porte par le 1er actif."""
    spv = a.parent
    assets = _spv_assets(spv)
    if not assets or a is not assets[0]:
        return pd.Series(0.0, index=m.time)
    res = _result_for(m, a)
    return _expand_annual_to_monthly(m, res.cit_due)


def shl_injection(m: Model, a: Asset, **kwargs) -> pd.Series:
    """Injection SHL (k€, positif en Sources). Portee par le 1er actif."""
    spv = a.parent
    assets = _spv_assets(spv)
    if not assets or a is not assets[0]:
        return pd.Series(0.0, index=m.time)
    res = _result_for(m, a)
    return _expand_annual_to_monthly(m, res.shl_injection)


def _stock_on_first_asset(m: Model, a: Asset, attr: str) -> pd.Series:
    """Stock annuel SPV diffuse sur les mois, porte par le 1er actif."""
    assets = _spv_assets(a.parent)
    if not assets or a is not assets[0]:
        return pd.Series(0.0, index=m.time)
    res = _result_for(m, a)
    return _expand_stock_annual_to_monthly(m, getattr(res, attr))


def shl_balance(m: Model, a: Asset, **kwargs) -> pd.Series:
    """Solde SHL EoP (k€, positif = dette)."""
    return _stock_on_first_asset(m, a, 'shl_eop')


def cash_pooling_balance(m: Model, a: Asset, **kwargs) -> pd.Series:
    """Solde cash pooling EoP (k€, positif = creance sur holdco)."""
    return _stock_on_first_asset(m, a, 'cash_pooling_eop')


def share_capital_balance(m: Model, a: Asset, **kwargs) -> pd.Series:
    return _stock_on_first_asset(m, a, 'share_capital_eop')


def legal_reserves_balance(m: Model, a: Asset, **kwargs) -> pd.Series:
    return _stock_on_first_asset(m, a, 'legal_reserves_eop')


def retained_earnings_balance(m: Model, a: Asset, **kwargs) -> pd.Series:
    return _stock_on_first_asset(m, a, 'retained_earnings_eop')


def shl_interest_payable_balance(m: Model, a: Asset, **kwargs) -> pd.Series:
    return _stock_on_first_asset(m, a, 'shl_interest_payable_eop')


def cit_payable_balance(m: Model, a: Asset, **kwargs) -> pd.Series:
    return _stock_on_first_asset(m, a, 'cit_payable_eop')


def proceeds_balance(m: Model, a: Asset, **kwargs) -> pd.Series:
    """Cash proceeds account EoP (k€)."""
    return _stock_on_first_asset(m, a, 'proceeds_eop')
