import warnings; warnings.filterwarnings('ignore')
import tomllib
from pathlib import Path

from mca_model.plumbing import build
from mca_model.model import opex as OPEX

with open('test/assets/real_model.toml', 'rb') as f:
    raw = tomllib.load(f)

try:
    m = build.make_model(raw, debug=False)
    print('BUILD OK')
except Exception as e:
    print('BUILD FAILED:', type(e).__name__, e)
    raise

# OPEX per SPV
print('\n=== OPEX par SPV (via pipeline complet) ===')
by_spv = {}
for a in m.list_assets():
    spv = a.parent.name
    by_spv.setdefault(spv, []).append(a)

for spv in sorted(by_spv):
    tot = sum(OPEX.get_price(m, a).sum() for a in by_spv[spv])
    print(f'  {spv:8} assets={len(by_spv[spv]):3}  OPEX total = {tot:12.3f} kEUR')

tot1 = sum(OPEX.get_price(m, a).sum() for a in by_spv['SPV_1'])
print(f'\n  >> SPV_1 = {tot1:.4f}  (Excel -8429.0427)  ecart = {100*(tot1+8429.0427)/-8429.0427:+.5f} %')
