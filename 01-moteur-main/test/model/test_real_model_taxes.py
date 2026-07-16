"""
Regression Phase 2 : le vrai portefeuille (real_model.toml) reproduit les TAXES LOCALES
par SPV du modele Excel (golden_results.toml), sans dependance a Excel.

Total local taxes (onglet SPV r387) = CVAE + IFER + Other taxes :
  - IFER (Portfolio r9148)  : capacite injectee * taux(avant/apres 20 ans) * inflation, par
                              annee civile productrice >= COD (arrondi au 1er janvier).
  - Other taxes (r9652)     : forfait k€/an, prorata jours, inflation (identique OPEX k€/an).
  - CVAE (r379, niveau SPV)  : valeur ajoutee plafonnee * bareme 2022-2029 + taxe CCI.

Les trois composantes sont reproduites au centime pres (k€).
"""
import tomllib
from collections import defaultdict
from pathlib import Path

import pytest

from mca_model.plumbing import build
from mca_model.model import taxes

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
    """somme, par SPV, d'une fonction (deja en k€)."""
    out = defaultdict(float)
    for a in m.list_assets():
        out[a.parent.name] += fn(m, a).sum()
    return out


@pytest.mark.parametrize('spv', SPVS)
def test_ifer_matches_excel_exactly(real_model, golden, spv):
    got = _sum_by_spv(real_model, taxes.ifer).get(spv, 0.0)
    expected = golden['local_taxes_ifer_by_spv'][spv]
    assert got == pytest.approx(expected, abs=1e-2)


@pytest.mark.parametrize('spv', SPVS)
def test_other_taxes_matches_excel_exactly(real_model, golden, spv):
    got = _sum_by_spv(real_model, taxes.other_taxes).get(spv, 0.0)
    expected = golden['local_taxes_other_by_spv'][spv]
    assert got == pytest.approx(expected, abs=1e-2)


@pytest.mark.parametrize('spv', SPVS)
def test_cvae_matches_excel_exactly(real_model, golden, spv):
    got = _sum_by_spv(real_model, taxes.cvae_asset_share).get(spv, 0.0)
    expected = golden['local_taxes_cvae_by_spv'][spv]
    assert got == pytest.approx(expected, abs=1e-2)


@pytest.mark.parametrize('spv', SPVS)
def test_total_local_taxes_matches_excel_exactly(real_model, golden, spv):
    got = _sum_by_spv(real_model, taxes.total_local_taxes).get(spv, 0.0)
    expected = golden['local_taxes_total_by_spv'][spv]
    assert got == pytest.approx(expected, abs=2e-2)
