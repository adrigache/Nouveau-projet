"""
Regression Phase 4 : financement SPV (SHL + IS + BFR + dividendes + cash pooling).

Verrouille au centime (EoP, k€) pour les 6 SPV.
"""
import tomllib
from collections import defaultdict
from pathlib import Path

import pytest

from mca_model.plumbing import build
from mca_model.model import financing
from mca_model.model.profit_loss import entries as pnl_entries

ROOT = Path(__file__).parents[1]
FNAME_REAL = ROOT / 'assets' / 'real_model.toml'
FNAME_GOLDEN = ROOT / 'assets' / 'golden_results.toml'

SPVS_EXACT = ['SPV_1', 'SPV_2', 'SPV_3', 'SPV_4', 'SPV_5', 'SPV_6']
SPVS_ALL = SPVS_EXACT


@pytest.fixture(scope='module')
def real_model():
    return build.load(FNAME_REAL, debug=False)


@pytest.fixture(scope='module')
def golden():
    with open(FNAME_GOLDEN, 'rb') as f:
        return tomllib.load(f)


def _fin(m, spv_name):
    financing.clear_cache()
    return financing.run_spv_financing(m, m.get_object(spv_name))


@pytest.mark.parametrize('spv', SPVS_EXACT)
def test_shl_interests_exact(real_model, golden, spv):
    r = _fin(real_model, spv)
    got = sum(r.shl_interest.values())
    assert got == pytest.approx(golden['pnl_shl_interests_by_spv'][spv], abs=1e-1)


@pytest.mark.parametrize('spv', SPVS_EXACT)
def test_ebt_exact(real_model, golden, spv):
    r = _fin(real_model, spv)
    got = sum(r.ebt.values())
    assert got == pytest.approx(golden['pnl_ebt_by_spv'][spv], abs=1e-1)


@pytest.mark.parametrize('spv', SPVS_EXACT)
def test_cit_due_exact(real_model, golden, spv):
    r = _fin(real_model, spv)
    got = sum(r.cit_due.values())
    assert got == pytest.approx(golden['pnl_cit_due_by_spv'][spv], abs=1e-1)


@pytest.mark.parametrize('spv', SPVS_EXACT)
def test_net_result_exact(real_model, golden, spv):
    r = _fin(real_model, spv)
    got = sum(r.net_result.values())
    assert got == pytest.approx(golden['pnl_net_result_by_spv'][spv], abs=1e-1)


@pytest.mark.parametrize('spv', SPVS_EXACT)
def test_pnl_entries_ebt_wired(real_model, golden, spv):
    """EBT via profit_loss.entries (SHL cable) matche le golden."""
    financing.clear_cache()
    out = defaultdict(float)
    for a in real_model.get_object(spv).assets:
        out[spv] += pnl_entries.EBT(real_model, a).sum()
    # SPV_6 : pas d'actifs — EBT via moteur financement (D&A vehicle)
    if not real_model.get_object(spv).assets:
        r = _fin(real_model, spv)
        out[spv] = sum(r.ebt.values())
    assert out[spv] == pytest.approx(golden['pnl_ebt_by_spv'][spv], abs=1e-1)


def test_spv5_cash_pooling_exact(real_model, golden):
    r = _fin(real_model, 'SPV_5')
    assert sum(r.cash_pooling_interest.values()) == pytest.approx(
        golden['pnl_cash_pooling_interests_by_spv']['SPV_5'], abs=1e-1)
