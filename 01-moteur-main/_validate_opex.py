import warnings; warnings.filterwarnings('ignore')
import pandas as pd, numpy as np
from datetime import datetime, date
from types import SimpleNamespace

from mca_model.service.helpers import generate_month_range
from mca_model.model import opex as OPEX


def sd(x):
    return x.date() if isinstance(x, datetime) else None


def num(x):
    return 0.0 if (x is None or x is False or (isinstance(x, float) and np.isnan(x))) else float(x)


# ---- model-level inflation params (from ass_Market / ass_Model) ----
m = SimpleNamespace()
m.time = generate_month_range(date(2025, 1, 1), date(2062, 12, 30))
m.ipc_years = list(range(2025, 2063))
m.ipc_base_rate = [0.021 if y == 2025 else 0.02 for y in m.ipc_years]
m.ipc_scenario = ['IPC', '20% IPC', '30% IPC', '40% IPC']
m.ipc_percentage = [1.0, 0.2, 0.3, 0.4]
m.inflation_start = 2025  # index stays 1 up to & incl. 2025, compounds from 2026 (Excel K1535)


# ---- extract 39 SPV_1 assets with ALL k€/year opex blocks ----
aa = pd.read_excel('model_real.xlsx', sheet_name='ass_Asset', engine='openpyxl', header=None)
ref = aa.iloc[7]
cols = [c for c in range(12, aa.shape[1]) if ref.iat[c] == 4]

# blocks: (label, tag_row0, base_row0 ["Index"/de-indexed], start_row0, end_row0)
blocks = [
    ('OPEX k#/Year',     149, 149, 150, 151),
    ('OPEX Period kEUR', 155, 155, 156, 157),
    ('Loyer',            161, 161, 162, 163),
    ('Loyer / OPEX',     167, 167, 168, 169),
    ('[OPEX k#/year]#1', 173, 173, 174, 175),
    ('[OPEX k#/year]#2', 179, 179, 180, 181),
]

assets = []
for c in cols:
    a = SimpleNamespace()
    a.name = aa.iat[2, c]
    a.operation_contract_start = sd(aa.iat[150, c])
    a.operation_contract_end = sd(aa.iat[151, c])
    a.OPEX = []
    for (lab, tr, br, sr, er) in blocks:
        base = num(aa.iat[br, c])
        if base == 0:
            continue
        st = sd(aa.iat[sr, c]); en = sd(aa.iat[er, c])
        if not st or not en:
            continue
        tag = aa.iat[tr, 8]
        a.OPEX.append({
            'name': lab,
            'price': (base, 'k#/year'.replace('#', '\u20ac')),
            'start date': st,
            'end date': en,
            'inflation': tag,
        })
    assets.append(a)

tot = 0.0
actif_1 = None
for a in assets:
    s = OPEX.get_price(m, a)
    tot += s.sum()
    if a.name == 'Actif_1':
        actif_1 = s.sum()

print('=== VALIDATION MOTEUR PYTHON (corrige) vs EXCEL ===')
print(f'  Actif_1     = {actif_1:12.4f}   (Excel -1159.8580)  ecart = {actif_1 + 1159.858:+.4f} kEUR')
print(f'  TOTAL SPV_1 = {tot:12.4f}   (Excel -8429.0427)  ecart = {100*(tot+8429.0427)/-8429.0427:+.5f} %')
