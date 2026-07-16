import warnings; warnings.filterwarnings('ignore')
import tomllib
from collections import defaultdict

from mca_model.plumbing import build
from mca_model.model import opex as OPEX

with open('test/assets/real_model.toml', 'rb') as f:
    raw = tomllib.load(f)
m = build.make_model(raw, debug=False)

by_spv = defaultdict(list)
for a in m.list_assets():
    by_spv[a.parent.name].append(a)

EXCEL_SPV3 = {
    'OPEX €/MWh (period 1)': -27249.549,
    'OPEX k€ /Year': -100898.096,
    'Loyer': -1232.661,
}

for spv in ['SPV_3']:
    print(f'=== {spv}: moteur par bloc ===')
    tot_by_name = defaultdict(float)
    per_asset = defaultdict(lambda: defaultdict(float))
    for a in by_spv[spv]:
        for k in a.OPEX:
            unit = k['price'][1]
            if unit == '€/MWh':
                cost = OPEX.get_price_euros_by_MWh(m, a, k).sum()
            else:
                cost = OPEX.get_price_euros_by_year(m, a, k).sum()
            tot_by_name[k['name']] += cost
            per_asset[a.name][k['name']] += cost
    grand = 0.0
    for name in sorted(tot_by_name):
        v = tot_by_name[name]
        grand += v
        exc = EXCEL_SPV3.get(name)
        tag = ''
        if exc is not None:
            tag = f'  Excel={exc:12.3f}  ecart={v-exc:+.3f}'
        print(f'  {name:25} moteur={v:12.3f}{tag}')
    print(f'  {"TOTAL":25} moteur={grand:12.3f}  Excel=-129380.306  ecart={grand+129380.306:+.3f}')

    # which assets carry the €/MWh (period 1) block + their production split
    from mca_model.model.electricity import contracted, merchant
    print('\n  -- assets with OPEX €/MWh (period 1): production split --')
    for a in by_spv[spv]:
        has = any(k['name'] == 'OPEX €/MWh (period 1)' for k in a.OPEX)
        if not has:
            continue
        c_mwh = contracted.in_MWh(m, a).sum()
        m_mwh = merchant.in_MWh(m, a).sum()
        emwh = per_asset[a.name].get('OPEX €/MWh (period 1)', 0.0)
        print(f'     {a.name:12} €/MWh_opex={emwh:11.3f}  contracted={c_mwh:11.1f} MWh  merchant={m_mwh:11.1f} MWh')
