import warnings; warnings.filterwarnings('ignore')
from collections import defaultdict
from pathlib import Path
import numpy as np, pandas as pd, openpyxl
from mca_model.plumbing import build
from mca_model.model import capex

m = build.load(Path('test/assets/real_model.toml'))
idx=m.time

# golden annual D&A per SPV from Excel r429 (cols Q.. = 2025..)
wbv=openpyxl.load_workbook('model_real.xlsx',data_only=True,read_only=True)
def golden_da(name):
    ws=wbv[name]
    def row(r):
        for x in ws.iter_rows(min_row=r,max_row=r,min_col=1,max_col=60,values_only=True): return x
    yr=row(11); da=row(429); out={}
    for c in range(16,60):
        y=yr[c-1] if c-1<len(yr) else None; v=da[c-1] if c-1<len(da) else None
        if isinstance(y,(int,float)) and isinstance(v,(int,float)) and abs(v)>1e-9:
            out[int(y)]=round(v,3)
    return out

maxerr_all=0.0
for s in ['SPV_1','SPV_2','SPV_3','SPV_4','SPV_5']:
    spv=m.get_object(s)
    td=pd.Series(0.0,index=idx)
    for a in spv.assets: td=td.add(capex.depreciation(m,a),fill_value=0)
    ann=td.groupby(td.index.year).sum()
    g=golden_da(s)
    yrs=sorted(set(g)|set(y for y in ann.index if abs(ann[y])>1e-9))
    maxerr=max((abs(ann.get(y,0)-g.get(y,0)) for y in yrs), default=0)
    maxerr_all=max(maxerr_all,maxerr)
    print(f'\n{s}  max annual err = {maxerr:.4f} k€   EoP got={td.sum():.3f} golden={sum(g.values()):.3f}')
    for y in yrs[:4]+yrs[-3:]:
        gg=g.get(y,0.0); cc=ann.get(y,0.0)
        fl='' if abs(gg-cc)<0.01 else '  <-- ECART'
        print(f'   {y}: got={cc:12.3f} golden={gg:12.3f}{fl}')
print(f'\n=== MAX annual D&A error across SPVs: {maxerr_all:.4f} k€ ===')
wbv.close()
