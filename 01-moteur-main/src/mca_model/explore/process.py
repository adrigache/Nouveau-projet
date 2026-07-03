from pathlib import Path
import re
import pandas as pd
import pickle

from mca_model.config import rc

from .load import load

WORK_FROM_PICKLED_DATA = True
# WORK_FROM_PICKLED_DATA = False

FNAME_PICKLE = 'extracted.pickle'

SKIP_LINES = ['Cash proceeds account BoP']

EXCEL_REF = re.compile(
    r'\b([A-Za-z0-9]+[!\.]{1})?' # optional sheet name
    r'(\$?[A-Z]{1,3}\$?\d{1,7})\b', # column + row
    re.IGNORECASE
)



f_clean_sheetname = lambda s:s.strip('!').lower()

def f_clean_position(s:str):
    clean = re.sub(r'[^\w]','',s).upper()
    return re.sub(r'[^A-Z]','', clean), int(re.sub(r'[^\d]','',clean))


def _decode_name(src:str, sheet:str, codes:dict):
    """"""
    # print('\tsearch in another sheet', src)
    found = EXCEL_REF.findall(src)
    if found:
        assert(len(found) == 1)
        _sheet, pos = found[0]
        if _sheet:
            sheet = f_clean_sheetname(_sheet)

        column, i = f_clean_position(pos)

        if i > max( list(codes[sheet].keys())):
            rc.shift(f"skipping {column}{i} from '{sheet}'")
            return '(not found)', sheet
        
        name, value = codes[sheet][i]
        return name, sheet
        
    raise KeyError(f'cannot found key for: {src}')



def decode_name(src:str, sheet_src:str, codes:dict):
    """"""
    name, sheet = src, sheet_src
    did_something = False
    while name.startswith('='):
        did_something = True
        name, sheet = _decode_name(name, sheet, codes)

        if name is None:
            break
        
    return did_something, (name, sheet)
    
    




# def decode_formula_from_same_sheet(src:str, codes:dict):
#     """"""
#     # print('\tsearch in same sheet', src)
#     found = re.fullmatch(r'=([A-Za-z])\$?(\d+)', src)
#     if found:
#         column, iline = found.groups()
#         # print('found', column, iline)
#         assert(column == 'P')
#         if int(iline) > max( list(codes.keys())):
#             return None, (column, iline)

#         return codes[int(iline)]

#     raise KeyError(f'cannot found key for: {src}')



def _expand_and_decode_formula(node:tuple, codes:dict):
    """"""
    sheet, _, name, formula = node
    out = []
    many = EXCEL_REF.findall(formula)
    for found in many:
        _sheet, pos = found
        
        if _sheet:
            _sheet = f_clean_sheetname(_sheet)
        else:
            _sheet = sheet
            
        column, i = f_clean_position(pos)
        name, formula = codes[_sheet].get(i, ('not found', None))
        
        out.append((_sheet, i, name, formula))

    # print('EXIT', out)
    return out


def decode_formula(node:tuple[str, int, str, str], codes:dict, depth:int=0):
    """"""

    out = []
    stop_formula =  [ None, '_array_formula']
    stop_name = ['not found', 'Last actual date']

    nodes = _expand_and_decode_formula(node, codes)

    #
    for _node in nodes:
        out.append( (depth, _node))
        _, _, _name, _formula = _node
        if depth < 5 and (_name not in stop_name) and (_formula not in stop_formula) :
            out.extend( decode_formula( _node, codes, depth+1))

    return out
        

def process(fname:Path, debug:bool):
    """"""

    if WORK_FROM_PICKLED_DATA:
        rc.squared(f'loading pickled data: {FNAME_PICKLE}')
        extracted_lines = pickle.load(open(FNAME_PICKLE, 'rb'))
    else:
        extracted_lines = load(fname, debug)
        with open(FNAME_PICKLE, 'wb') as f:
            pickle.dump(extracted_lines, f)
            rc.squared(f'saving to {FNAME_PICKLE}')

    overview = extracted_lines['overview']
    for i, (name, formula) in overview.items():

        if formula is None:
            continue
        
        rc.p(f'\n#{i:03} `{name}`')

        # decode name
        decoded, (_decoded_name, _decoded_sheet) = decode_name(name, 'overview', extracted_lines)

        if decoded:
            rc.shift(f"decoded to '{_decoded_name}' from '{_decoded_sheet}'")

        # decode formula
        if _decoded_name in SKIP_LINES:
            rc.shift('skipped')
        else:
            root = ('overview', 0, name, formula)
            decoded = decode_formula(root, extracted_lines)

            # clean
            infos = set( [ (d, x[:3]) for d,x in decoded])
            ordered = sorted(list(infos), key=lambda x:x[0])
            shown = set()
            for depth, (sheet, i, name) in ordered:
                key = (sheet, i, name)
                if key not in shown:
                    if len(name) < 4:
                        continue
                    if name in ['not found', '_array_formula']:
                        name = '??'
                        
                    rc.shift(f'[{depth}] ({sheet}) #{i:03} {name}')
                    shown.add(key)

    



    
    
