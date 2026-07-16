import warnings; warnings.filterwarnings('ignore')
from collections import defaultdict
from pathlib import Path
from mca_model.plumbing import build
from mca_model.model import taxes

m = build.load(Path('test/assets/real_model.toml'))

golden = {'SPV_1': -8669.3246, 'SPV_2': -209644.6192, 'SPV_3': -107349.0204,
          'SPV_4': -419.8911, 'SPV_5': -96.4098, 'SPV_6': 0.0}
gi = {'SPV_1': -4593.0249, 'SPV_2': -110081.1158, 'SPV_3': -56260.1868, 'SPV_4': -195.4605, 'SPV_5': -58.6381}
go = {'SPV_1': -4029.2897, 'SPV_2': -98398.4025, 'SPV_3': -50596.6154, 'SPV_4': -222.5086, 'SPV_5': -37.1831}
gc = {'SPV_1': -47.0100, 'SPV_2': -1165.1008, 'SPV_3': -492.2181, 'SPV_4': -1.9221, 'SPV_5': -0.5885}

tot = defaultdict(float); dif = defaultdict(float); dot = defaultdict(float); dcv = defaultdict(float)
for a in m.list_assets():
    s = a.parent.name
    dif[s] += taxes.ifer(m, a).sum()
    dot[s] += taxes.other_taxes(m, a).sum()
    dcv[s] += taxes.cvae_asset_share(m, a).sum()
    tot[s] += taxes.total_local_taxes(m, a).sum()

print(f"{'SPV':6}{'IFER got':>13}{'IFER exp':>13}{'Other got':>13}{'Other exp':>13}{'CVAE got':>11}{'CVAE exp':>11}{'TOT got':>13}{'TOT exp':>13}{'ecart%':>9}")
for s in ['SPV_1','SPV_2','SPV_3','SPV_4','SPV_5','SPV_6']:
    e = golden[s]; g = tot[s]
    ecart = 100*(g-e)/e if e else 0.0
    print(f"{s:6}{dif[s]:13.4f}{gi.get(s,0):13.4f}{dot[s]:13.4f}{go.get(s,0):13.4f}{dcv[s]:11.4f}{gc.get(s,0):11.4f}{g:13.4f}{e:13.4f}{ecart:+9.4f}")
