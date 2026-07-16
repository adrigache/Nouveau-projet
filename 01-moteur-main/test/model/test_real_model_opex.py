"""
Regression Phase 0 : le vrai portefeuille (real_model.toml, extrait une fois de
l'Excel) se construit et reproduit l'OPEX par SPV du modele Excel (golden_results.toml).
Aucune dependance a Excel : tout est fige dans des fichiers Python-natifs.
"""
import tomllib
from collections import defaultdict
from pathlib import Path

import pytest

from mca_model.plumbing import build
from mca_model.model import opex as OPEX

ROOT = Path(__file__).parents[1]
FNAME_REAL = ROOT / 'assets' / 'real_model.toml'
FNAME_GOLDEN = ROOT / 'assets' / 'golden_results.toml'


@pytest.fixture(scope='module')
def real_model():
    return build.load(FNAME_REAL, debug=False)


@pytest.fixture(scope='module')
def golden():
    with open(FNAME_GOLDEN, 'rb') as f:
        return tomllib.load(f)


def _opex_by_spv(m):
    out = defaultdict(float)
    for a in m.list_assets():
        out[a.parent.name] += OPEX.get_price(m, a).sum()
    return out


def test_real_model_builds(real_model):
    assert len(real_model.list_assets()) == 183


@pytest.mark.parametrize('spv', ['SPV_1', 'SPV_2', 'SPV_3', 'SPV_4', 'SPV_5', 'SPV_6'])
def test_opex_matches_excel_exactly(real_model, golden, spv):
    """
    OPEX (k€/year ET €/MWh) reproduit au centime pres pour tous les SPV.
    Le bloc €/MWh utilise la production annuelle exacte (R2555 + R3058), ce qui
    resorbe l'ancien residu de +0.058% sur SPV_3 (production merchant d'Actif_5).
    """
    got = _opex_by_spv(real_model).get(spv, 0.0)
    expected = golden['opex_total_by_spv'][spv]
    assert got == pytest.approx(expected, abs=1e-2)
