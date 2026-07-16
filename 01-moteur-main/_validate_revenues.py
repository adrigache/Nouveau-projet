import warnings; warnings.filterwarnings('ignore')
import tomllib
from collections import defaultdict

import pandas as pd, numpy as np
from mca_model.plumbing import build
from mca_model.model.electricity import contracted, merchant


def golden():
    """Par SPV: total, contracte, merchant (col EoP=12)."""
    out = {}
    for spv in ['SPV_1', 'SPV_2', 'SPV_3', 'SPV_4', 'SPV_5', 'SPV_6']:
        df = pd.read_excel('model_real.xlsx', sheet_name=spv, engine='openpyxl', header=None)
        tot = con = mer = 0.0
        seen_block = False
        for r in range(df.shape[0]):
            lab = df.iat[r, 2]
            if not isinstance(lab, str):
                continue
            lab = lab.strip()
            v = df.iat[r, 12]
            v = float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else 0.0
            if lab == 'Total revenues from electricity production' and tot == 0.0:
                tot = v
            # the first "Contracted period"/"Merchant period" pair (revenues section ~r192)
            if lab == 'Contracted period' and not seen_block:
                con = v
            if lab == 'Merchant period' and not seen_block:
                mer = v
                seen_block = True
        out[spv] = (tot, con, mer)
    return out


G = golden()
with open('test/assets/real_model.toml', 'rb') as f:
    raw = tomllib.load(f)
m = build.make_model(raw, debug=False)

by_spv = defaultdict(list)
for a in m.list_assets():
    by_spv[a.parent.name].append(a)

print('=== REVENUS par SPV : moteur vs Excel (k€) ===')
print(f'{"SPV":7} {"poste":11} {"moteur":>13} {"Excel":>13} {"ecart%":>9}')
for spv in ['SPV_1', 'SPV_2', 'SPV_3', 'SPV_4', 'SPV_5', 'SPV_6']:
    c = sum(contracted.revenues(m, a).sum() for a in by_spv.get(spv, [])) / 1000
    mm = sum(merchant.revenues(m, a).sum() for a in by_spv.get(spv, [])) / 1000
    tot = c + mm
    gt, gc, gm = G[spv]
    def pct(x, g): return '' if g == 0 else f'{100*(x-g)/g:+.3f}%'
    print(f'{spv:7} {"contracte":11} {c:13.3f} {gc:13.3f} {pct(c,gc):>9}')
    print(f'{spv:7} {"merchant":11} {mm:13.3f} {gm:13.3f} {pct(mm,gm):>9}')
    print(f'{spv:7} {"TOTAL":11} {tot:13.3f} {gt:13.3f} {pct(tot,gt):>9}')
    print()
