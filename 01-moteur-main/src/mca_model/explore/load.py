import pandas as pd

from openpyxl.worksheet.formula import ArrayFormula

from mca_model.repository.filesystem.read_xls import load_full_model

from mca_model.config import (
    rc,
    FNAME_MODEL,
    MODEL_SHEETS,
    MODEL_SHEETS_COMPUTATIONS)


COL_NAME = 1
COL_FORMULA = 15


def extract_formula(df):
    """"""

    lines = df.iloc[:,[COL_NAME, COL_FORMULA]]
    # lines.columns = ['name', 'formula']
    # lines.dropna(subset=[lines.columns[0]], inplace=True)

    out = {}
    for i,(_, x) in enumerate(lines.iterrows()):
        name, value = tuple(x.values)
        if name is None:
            continue

        if isinstance(value, ArrayFormula) :
            value = '_array_formula'

        if isinstance(name, ArrayFormula) :
            name = '_array_formula'
            out[i+1] = (name, value)
            
        if isinstance(name, str):
            if name.upper() in ['RATIOS & GRAPH', 'END']:
                break

        # base
        out[i+1] = (name, value)
        
      
    return out

    
def load(fname, debug):
    """"""
    wb = load_full_model(fname, silent=not debug, raw=True)

    lines = {}
    for sheet, df in wb.items():
        # if sheet in ['overview', 'portfolio', 'computations']:
        _lines = extract_formula(df)
        rc.p(f"'{sheet}' rows extracted wih formula: {len(_lines)}")
        
        # {line_number: (name, formula)} 
        # for i,(name, formula) in _lines.items():
        #     print(f"#{i:02}\t{name}\t{formula}")
        
        lines[sheet] = _lines
    #
    
    return lines
            
        
                
