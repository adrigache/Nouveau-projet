"""
Regression Phase 3 : le vrai portefeuille (real_model.toml) reproduit le haut du P&L et le
CAPEX/D&A par SPV du modele Excel (golden_results.toml), sans dependance a Excel.

Postes valides au total (col EoP, k€) :
  - CAPEX (CF r72)   : cout de construction (ass_Asset type1/type2/vehicle/perimeter).
  - D&A (P&L r141)   : amortissement lineaire (= -CAPEX sur la vie).
  - EBITDA (r139)    : revenus + opex + agency + taxes locales.
  - EBIT (r142)      : EBITDA + D&A.

Note : le profil ANNUEL du CAPEX/D&A depend du calendrier de decaissement du plan de
financement (Phase 4) ; seuls les totaux EoP sont verrouilles ici. L'IS (r152) depend de
l'EBT complet (interets de dette / SHL) et sera valide en Phase 4.
"""
import tomllib
from collections import defaultdict
from pathlib import Path

import pytest

from mca_model.plumbing import build
from mca_model.model import capex
from mca_model.model.profit_loss import functions as pnl
from mca_model.model.profit_loss import entries as pnl_entries

ROOT = Path(__file__).parents[1]
FNAME_REAL = ROOT / 'assets' / 'real_model.toml'
FNAME_GOLDEN = ROOT / 'assets' / 'golden_results.toml'

SPVS = ['SPV_1', 'SPV_2', 'SPV_3', 'SPV_4', 'SPV_5', 'SPV_6']


@pytest.fixture(scope='module')
def real_model():
    return build.load(FNAME_REAL, debug=False)


@pytest.fixture(scope='module')
def golden():
    with open(FNAME_GOLDEN, 'rb') as f:
        return tomllib.load(f)


def _sum_by_spv(m, fn):
    out = defaultdict(float)
    for a in m.list_assets():
        out[a.parent.name] += fn(m, a).sum()
    return out


@pytest.mark.parametrize('spv', SPVS)
def test_capex_total_matches_excel_exactly(real_model, golden, spv):
    got = _sum_by_spv(real_model, capex.capex).get(spv, 0.0)
    expected = golden['capex_total_by_spv'][spv]
    assert got == pytest.approx(expected, abs=1e-2)


@pytest.mark.parametrize('spv', SPVS)
def test_da_total_matches_excel_exactly(real_model, golden, spv):
    got = _sum_by_spv(real_model, capex.depreciation).get(spv, 0.0)
    expected = golden['pnl_da_by_spv'][spv]
    assert got == pytest.approx(expected, abs=1e-2)


@pytest.mark.parametrize('spv', SPVS)
def test_ebitda_matches_excel_exactly(real_model, golden, spv):
    got = _sum_by_spv(real_model, pnl_entries.EBITDA).get(spv, 0.0)
    expected = golden['pnl_ebitda_by_spv'][spv]
    assert got == pytest.approx(expected, abs=2e-2)


@pytest.mark.parametrize('spv', SPVS)
def test_ebit_matches_excel_exactly(real_model, golden, spv):
    got = _sum_by_spv(real_model, pnl_entries.EBIT).get(spv, 0.0)
    expected = golden['pnl_ebit_by_spv'][spv]
    assert got == pytest.approx(expected, abs=2e-2)


def test_da_equals_capex(real_model):
    """Coherence interne : sur la vie, tout le CAPEX est amorti (D&A cumule = CAPEX cumule)."""
    da = _sum_by_spv(real_model, capex.depreciation)
    cx = _sum_by_spv(real_model, capex.capex)
    for spv in SPVS:
        assert da[spv] == pytest.approx(cx[spv], abs=1e-6)


def test_capex_annual_profile_spv1(real_model, golden):
    """Calendrier de decaissement CAPEX : profil annuel SPV_1 exact vs Excel."""
    import pandas as pd
    spv = real_model.get_object('SPV_1')
    tot = pd.Series(0.0, index=real_model.time)
    for a in spv.assets:
        tot = tot.add(capex.capex(real_model, a), fill_value=0)
    ann = tot.groupby(tot.index.year).sum()
    for y, expected in golden['capex_annual_spv1'].items():
        assert float(ann.get(int(y), 0.0)) == pytest.approx(expected, abs=1e-2)


def test_da_annual_profile_spv1(real_model, golden):
    """Profil annuel D&A SPV_1 exact vs Excel (depend du calendrier de decaissement)."""
    import pandas as pd
    spv = real_model.get_object('SPV_1')
    tot = pd.Series(0.0, index=real_model.time)
    for a in spv.assets:
        tot = tot.add(capex.depreciation(real_model, a), fill_value=0)
    ann = tot.groupby(tot.index.year).sum()
    for y, expected in golden['pnl_da_annual_spv1'].items():
        assert float(ann.get(int(y), 0.0)) == pytest.approx(expected, abs=1e-2)
