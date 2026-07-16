"""
Regression Phase 1 : le vrai portefeuille (real_model.toml) reproduit les REVENUS
electricite par SPV du modele Excel (golden_results.toml), sans dependance a Excel.

- Contracte (FiT/PPA/CfD) : reproduit au centime (replication annuelle exacte de
  l'onglet Portfolio r3565 : seuil par annee sur la production MWh, inflation FiT
  a la date anniversaire, degradation en moyenne annuelle).
- Merchant : en cours de calage (biais residuel connu), verrouille en tolerance
  large tant que la formule exacte n'est pas integree.
"""
import tomllib
from collections import defaultdict
from pathlib import Path

import pytest

from mca_model.plumbing import build
from mca_model.model.electricity import contracted, merchant

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


def _sum_by_spv(m, fn):
    """somme, par SPV, d'une fonction de revenu (euros) -> ramenee en k€."""
    out = defaultdict(float)
    for a in m.list_assets():
        out[a.parent.name] += fn(m, a).sum()
    return {k: v / 1000.0 for k, v in out.items()}


@pytest.mark.parametrize('spv', ['SPV_1', 'SPV_2', 'SPV_3', 'SPV_4', 'SPV_5', 'SPV_6'])
def test_contracted_matches_excel_exactly(real_model, golden, spv):
    """Revenu contracte reproduit au centime pres (k€)."""
    got = _sum_by_spv(real_model, contracted.revenues).get(spv, 0.0)
    expected = golden['revenues_contracted_by_spv'][spv]
    assert got == pytest.approx(expected, abs=1e-2)


@pytest.mark.parametrize('spv', ['SPV_1', 'SPV_2', 'SPV_3', 'SPV_4', 'SPV_5', 'SPV_6'])
def test_merchant_matches_excel_exactly(real_model, golden, spv):
    """Revenu merchant reproduit au centime pres (k€)."""
    got = _sum_by_spv(real_model, merchant.revenues).get(spv, 0.0)
    expected = golden['revenues_merchant_by_spv'][spv]
    assert got == pytest.approx(expected, abs=1e-2)


@pytest.mark.parametrize('spv', ['SPV_1', 'SPV_2', 'SPV_3', 'SPV_4', 'SPV_5', 'SPV_6'])
def test_total_revenues_matches_excel_exactly(real_model, golden, spv):
    """Total (contracte + merchant) reproduit au centime pres (k€)."""
    c = _sum_by_spv(real_model, contracted.revenues).get(spv, 0.0)
    mk = _sum_by_spv(real_model, merchant.revenues).get(spv, 0.0)
    expected = golden['revenues_total_by_spv'][spv]
    assert (c + mk) == pytest.approx(expected, abs=2e-2)
