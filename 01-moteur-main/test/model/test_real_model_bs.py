"""
Regression Phase 5 : bilan SPV (stocks) + detentions Holdco vs Excel.
"""
import tomllib
from pathlib import Path

import pytest

from mca_model.plumbing import build
from mca_model.model import financing
from mca_model.model.balance_sheet import entries as bs
from mca_model.model.balance_sheet import functions as bf
from mca_model.model.balance_sheet import hierarchy as hier

ROOT = Path(__file__).parents[1]
FNAME_REAL = ROOT / 'assets' / 'real_model.toml'
FNAME_GOLDEN = ROOT / 'assets' / 'golden_results.toml'

# SPV_6 : pas d'actifs — Bilan complet (proceeds account) reporte ; stocks
# financement + NBV vehicle testes a part.
SPVS_FULL_BS = ['SPV_1', 'SPV_2', 'SPV_3', 'SPV_4', 'SPV_5']


@pytest.fixture(scope='module')
def real_model():
    return build.load(FNAME_REAL, debug=False)


@pytest.fixture(scope='module')
def golden():
    with open(FNAME_GOLDEN, 'rb') as f:
        return tomllib.load(f)


def _idx_year_end(m, year: int) -> int:
    return max(i for i, t in enumerate(m.time) if t.year == year)


def _sum_spv(m, spv_name, fn):
    out = None
    for a in m.get_object(spv_name).assets:
        s = fn(m, a)
        out = s if out is None else out + s
    return out


def test_hierarchy_parents(real_model):
    """Excel ass_Vehicle r41/r43 : SPV_1-2→Holdco_1, SPV_3-6→Holdco_2."""
    m = real_model
    h1 = {c.name for c in m.get_object('Holdco_1').children}
    h2 = {c.name for c in m.get_object('Holdco_2').children}
    assert h1 == {'SPV_1', 'SPV_2'}
    assert h2 == {'SPV_3', 'SPV_4', 'SPV_5', 'SPV_6'}
    top_kids = {c.name for c in m.TopCo.children}
    assert top_kids == {'Holdco_1', 'Holdco_2'}


@pytest.mark.parametrize('spv', SPVS_FULL_BS)
def test_spv_bs_balances_2026(real_model, golden, spv):
    financing.clear_cache()
    m = real_model
    i = _idx_year_end(m, 2026)
    g = golden[f'bs_{spv.replace("_", "").lower()}_2026']
    ta = _sum_spv(m, spv, bs.total_assets)
    tl = _sum_spv(m, spv, bs.total_liabilities)
    assert float(ta.iloc[i]) == pytest.approx(g['total_assets'], abs=1e-2)
    assert float(tl.iloc[i]) == pytest.approx(g['total_liabilities'], abs=1e-2)
    assert float((ta - tl).iloc[i]) == pytest.approx(0.0, abs=1e-4)


@pytest.mark.parametrize('spv', SPVS_FULL_BS)
def test_spv_bs_components_2026(real_model, golden, spv):
    financing.clear_cache()
    m = real_model
    i = _idx_year_end(m, 2026)
    g = golden[f'bs_{spv.replace("_", "").lower()}_2026']
    assert float(_sum_spv(m, spv, bf.assets).iloc[i]) == pytest.approx(
        g['nbv_assets'], abs=1e-2)
    assert float(_sum_spv(m, spv, bf.SHL).iloc[i]) == pytest.approx(
        g['shl'], abs=1e-2)
    assert float(_sum_spv(m, spv, bf.retained_earnings).iloc[i]) == pytest.approx(
        g['retained_earnings'], abs=1e-2)
    assert float(_sum_spv(m, spv, bf.share_capital).iloc[i]) == pytest.approx(
        g['share_capital'], abs=1e-6)
    assert float(_sum_spv(m, spv, bf.trade_receivables).iloc[i]) == pytest.approx(
        g['trade_receivables'], abs=1e-2)
    assert float(_sum_spv(m, spv, bf.trade_payables).iloc[i]) == pytest.approx(
        g['trade_payables'], abs=1e-2)


def test_spv6_empty_bs_stocks_2026(real_model, golden):
    """SPV sans actifs : NBV + proceeds + RE + CIT (A=L)."""
    financing.clear_cache()
    m = real_model
    i = _idx_year_end(m, 2026)
    g = golden['bs_spv6_2026']
    spv = m.get_object('SPV_6')
    assert not spv.assets
    nbv = float(hier.empty_spv_nbv(m, spv).iloc[i])
    proc = float(hier.spv_financing_stock(m, spv, 'proceeds_eop').iloc[i])
    re = float(hier.spv_financing_stock(m, spv, 'retained_earnings_eop').iloc[i])
    cit = float(hier.spv_financing_stock(m, spv, 'cit_payable_eop').iloc[i])
    assert nbv == pytest.approx(g['nbv_assets'], abs=1e-2)
    assert proc == pytest.approx(g['proceeds'], abs=1e-2)
    assert re == pytest.approx(g['retained_earnings'], abs=1e-2)
    assert cit == pytest.approx(g['cit_payable'], abs=1e-2)
    assert float(hier.spv_financing_stock(m, spv, 'share_capital_eop').iloc[i]) == pytest.approx(
        g['share_capital'], abs=1e-6)
    assert float(hier.spv_financing_stock(m, spv, 'shl_eop').iloc[i]) == pytest.approx(
        g['shl'], abs=1e-2)
    assert nbv + proc == pytest.approx(g['total_assets'], abs=1e-2)
    assert re + cit == pytest.approx(g['total_liabilities'], abs=1e-2)
    assert (nbv + proc) - (re + cit) == pytest.approx(0.0, abs=1e-6)


@pytest.mark.parametrize('holdco,key', [
    ('Holdco_1', 'bs_holdco1_detention_2026'),
    ('Holdco_2', 'bs_holdco2_detention_2026'),
])
def test_holdco_detention_2026(real_model, golden, holdco, key):
    financing.clear_cache()
    m = real_model
    i = _idx_year_end(m, 2026)
    g = golden[key]
    h = m.get_object(holdco)
    hier.ensure_spv_financing(m, h)
    assert float(hier.share_capital_in_detention(m, h).iloc[i]) == pytest.approx(
        g['share_capital_in_detention'], abs=1e-6)
    assert float(hier.shl_in_detention(m, h).iloc[i]) == pytest.approx(
        g['shl_in_spvs'], abs=1e-2)
    assert float(hier.cash_pooling_in_detention(m, h).iloc[i]) == pytest.approx(
        g['cash_pooling_in_detention'], abs=1e-2)


@pytest.mark.parametrize('holdco,key', [
    ('Holdco_1', 'bs_holdco1_2026'),
    ('Holdco_2', 'bs_holdco2_2026'),
])
def test_holdco_bs_full_2026(real_model, golden, holdco, key):
    """B/S Holdco : detentions moteur + postes propres (schedules TOML)."""
    from mca_model.model.balance_sheet import vehicle as vbs
    financing.clear_cache()
    m = real_model
    i = _idx_year_end(m, 2026)
    g = golden[key]
    bs = vbs.vehicle_balance_sheet(m, m.get_object(holdco))
    assert float(bs['total_assets'].iloc[i]) == pytest.approx(g['total_assets'], abs=1e-2)
    assert float(bs['total_liabilities'].iloc[i]) == pytest.approx(
        g['total_liabilities'], abs=1e-2)
    assert float((bs['total_assets'] - bs['total_liabilities']).iloc[i]) == pytest.approx(
        0.0, abs=1e-2)
    assert float(bs['nbv'].iloc[i]) == pytest.approx(g['nbv_assets'], abs=1e-2)
    assert float(bs['sc_detention'].iloc[i]) == pytest.approx(g['sc_detention'], abs=1e-6)
    assert float(bs['shl_detention'].iloc[i]) == pytest.approx(g['shl_in_spvs'], abs=1e-2)
    assert float(bs['senior'].iloc[i]) == pytest.approx(g['senior'], abs=1e-2)
    assert float(bs['ebl'].iloc[i]) == pytest.approx(g['ebl'], abs=1e-2)
    assert float(bs['proceeds'].iloc[i]) == pytest.approx(g['proceeds'], abs=1e-2)


def test_overview_holdco1_2026(real_model, golden):
    from mca_model.model import overview as ov
    financing.clear_cache()
    m = real_model
    i = _idx_year_end(m, 2026)
    g = golden['overview_holdco1_2026']
    snap = ov.build_overview(m, entity=g['entity'])
    assert snap.entity == g['entity']
    assert float(snap.total_assets.iloc[i]) == pytest.approx(g['total_assets'], abs=1e-2)
    assert float(snap.total_liabilities.iloc[i]) == pytest.approx(
        g['total_liabilities'], abs=1e-2)
    assert float(snap.check_bs.iloc[i]) == pytest.approx(g['check_bs'], abs=1e-2)


def test_hdscr_holdco2_2027(real_model, golden):
    """HDSCR Holdco_2 2027 ≈ 1.15 (Excel Overview)."""
    from mca_model.model import ratios
    financing.clear_cache()
    m = real_model
    i = _idx_year_end(m, 2027)
    g = golden['ratios_holdco2_2027']
    series = ratios.hdscr(m, m.get_object('Holdco_2'))
    assert float(series.iloc[i]) == pytest.approx(g['hdscr'], abs=1e-2)
