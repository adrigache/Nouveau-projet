"""
One-shot extraction: model_real.xlsx  ->  test/assets/real_model.toml
Produit un jeu d'hypotheses Python-natif (meme schema que model_dummy.toml).
Apres cette extraction, Excel n'est plus necessaire.
"""
import warnings; warnings.filterwarnings('ignore')
import pandas as pd, numpy as np
import datetime as dt
import tomli_w

SRC = 'model_real.xlsx'
OUT = 'test/assets/real_model.toml'


def as_date(x):
    if isinstance(x, dt.datetime):
        return x.date()
    if isinstance(x, dt.date):
        return x
    return None


def num(x, default=0.0):
    if x is None or x is False or (isinstance(x, float) and np.isnan(x)):
        return default
    if isinstance(x, (int, float)):
        return float(x)
    return default


def as_bool(x):
    if x is True or x == 1:
        return True
    return False


def isval(x):
    return not (x is None or x is False or (isinstance(x, float) and np.isnan(x)))


# ---------------------------------------------------------------- sheets
model_sheet = pd.read_excel(SRC, sheet_name='ass_Model', engine='openpyxl', header=None)
market = pd.read_excel(SRC, sheet_name='ass_Market', engine='openpyxl', header=None)
veh = pd.read_excel(SRC, sheet_name='ass_Vehicle', engine='openpyxl', header=None)
aa = pd.read_excel(SRC, sheet_name='ass_Asset', engine='openpyxl', header=None)

# ---------------------------------------------------------------- [dashboard]
dashboard = {'sensitivity': 2, 'scenario': 'lender'}

# ---------------------------------------------------------------- [model]
model = {
    't_start': dt.date(2025, 1, 1),
    't_end': dt.date(2064, 12, 31),
    'inflation_start': dt.date(2026, 1, 1),
    't_freq': 'ME',
}

# ---------------------------------------------------------------- [market] inflation
# ass_Market: years col2 from row12; IPC rate col5; scenarios cols 5..8
ipc_years, ipc_base_rate = [], []
r = 11
while r < market.shape[0]:
    y = market.iat[r, 2]
    if isinstance(y, (int, float)) and not (isinstance(y, float) and np.isnan(y)) and 1900 < y < 2200:
        ipc_years.append(int(y))
        ipc_base_rate.append(round(float(market.iat[r, 5]), 6))
        r += 1
    else:
        if ipc_years:
            break
        r += 1

# ---------------------------------------------------------------- [market] prices
# ass_Market "MARKET PRICES": headers row73 (idx72) from col13; year in col8; values from col13.
MP_HEADER_ROW = 72
MP_YEAR_COL = 8
mp_scenario_cols = {}
for c in range(13, market.shape[1]):
    h = market.iat[MP_HEADER_ROW, c]
    if isinstance(h, str) and h.strip():
        mp_scenario_cols[c] = h.strip()

# collect year rows
mp_year_rows = []
for rr in range(MP_HEADER_ROW + 1, market.shape[0]):
    y = market.iat[rr, MP_YEAR_COL]
    if isinstance(y, (int, float)) and not isinstance(y, bool) and 2000 < y < 2200:
        mp_year_rows.append((int(y), rr))
    elif mp_year_rows and not (isinstance(y, (int, float)) and not isinstance(y, bool)):
        break

market_price_years_int = [y for y, _ in mp_year_rows]
market_price_years = [str(y) for y in market_price_years_int]

market_price_scenario_full = {}
for c, name in mp_scenario_cols.items():
    vals = []
    for (_, rr) in mp_year_rows:
        vals.append(round(num(market.iat[rr, c], 0.0), 6))
    market_price_scenario_full[name] = vals

# ---------------------------------------------------------------- vehicles
VEH_COLS = list(range(12, 21))  # Topco .. SPV_6
ref_to_name = {}
vehicles = {}
for c in VEH_COLS:
    name = veh.iat[1, c]
    if not isinstance(name, str) or not name.strip():
        continue
    vtype = veh.iat[5, c]
    ref = veh.iat[4, c]
    if isinstance(ref, (int, float)) and not isinstance(ref, bool):
        ref_to_name[int(ref)] = name
    is_topco = name.lower() == 'topco'
    if is_topco:
        ref_to_name[1] = name  # topco ref shown as True

    # vehicle opex (row441 base, 442 start, 443 end, 444 index)  -> empty => 0
    opex_base = num(veh.iat[440, c], 0.0)
    opex_start = as_date(veh.iat[441, c])
    opex_end = as_date(veh.iat[442, c])
    opex_infl = veh.iat[443, c] if isinstance(veh.iat[443, c], str) else 'IPC'

    node = {
        'type': 'TopCo' if is_topco else vtype,
        'opex': [opex_base, 'k€ / year'],
        'opex_start_date': opex_start or dt.date(2026, 1, 1),
        'opex_end_date': opex_end or dt.date(2062, 12, 30),
        'opex_inflation': opex_infl if opex_infl in ('IPC', '20% IPC', '30% IPC', '40% IPC') else 'IPC',
        # ---- financement (Phase 4) ----
        # SHL (shareholder loan) : ass_Vehicle r415 taux, r416 capitalisation, r418/419 min SHL,
        # r423 taux cash pooling.
        'shl_rate': round(num(veh.iat[414, c]), 8),
        'shl_capitalise': as_bool(veh.iat[415, c]),
        'shl_base': veh.iat[416, c] if isinstance(veh.iat[416, c], str) else 'Exact',
        'min_shl_activation': as_bool(veh.iat[417, c]),
        'min_shl_amount': num(veh.iat[418, c]),
        'cash_pooling_rate': round(num(veh.iat[422, c]), 8),
        # BFR (ass_Vehicle r428/r429)
        'days_receivables': int(num(veh.iat[427, c], 30)),
        'days_payables': int(num(veh.iat[428, c], 30)),
        'share_capital_amount': 1.0,  # 1 k€ a la 1ere annee de funding (Excel r456)
    }
    # date de mise en service pour amortissement vehicle/perimeter (= injection date / FC)
    _da_veh_start = as_date(veh.iat[433, c]) or as_date(veh.iat[54, c])
    if _da_veh_start is not None:
        node['da_vehicle_start'] = _da_veh_start
    # CAPEX vehicle/perimeter pour D&A : somme ass_Asset r225/r226 (tous actifs du
    # SPV, y compris inactifs) — voir boucle apres extraction des assets.
    node['da_vehicle_capex'] = 0.0
    node['da_perimeter_capex'] = 0.0
    if isinstance(ref, (int, float)) and not isinstance(ref, bool):
        node['_veh_ref'] = int(ref)
    elif is_topco:
        node['_veh_ref'] = 1
    vehicles[name] = node

# hierarchy (ass_Vehicle r41 Holding vehicle name / r43 Vehicle held by ref /
# r45 Detention by holdco). Generique : parent = nom holdant, sinon ref→nom.
topco_name = next((n for n in vehicles if n.lower() == 'topco'), 'Topco')
holdcos = [n for n, v in vehicles.items() if v['type'] == 'Holdco']
default_holdco = holdcos[0] if holdcos else topco_name
for c in VEH_COLS:
    name = veh.iat[1, c]
    if name not in vehicles:
        continue
    v = vehicles[name]
    hold_name = veh.iat[40, c]
    held_ref = veh.iat[42, c]
    det = veh.iat[44, c]
    if isinstance(det, bool):
        v['detention_pct'] = 1.0 if det else 0.0
    else:
        v['detention_pct'] = float(num(det, 1.0))
    if name.lower() == 'topco':
        continue
    if isinstance(hold_name, str) and hold_name.strip() and hold_name in vehicles:
        v['parent'] = hold_name.strip()
    elif isinstance(held_ref, (int, float)) and not isinstance(held_ref, bool):
        v['parent'] = ref_to_name.get(int(held_ref), default_holdco)
    elif held_ref is True or (isinstance(held_ref, bool) and held_ref):
        v['parent'] = topco_name
    elif v['type'] == 'Holdco':
        v['parent'] = topco_name
    elif v['type'] == 'SPV':
        v['parent'] = default_holdco

# ---------------------------------------------------------------- assets
ASSET_FIELDS_SCALAR = {
    'name': 2, 'type': 3, 'typology': 9,
    'construction_start': 24, 'construction_end': 25,
    'merchant_pre_contract_start': 29, 'merchant_pre_contract_end': 31,
    'merchant_post_contract_start': 36, 'merchant_post_contract_end': 38,
    'operation_contract_start': 32, 'operation_contract_end': 35,
    'capacity_degradation_start_date': 65,
}
DATE_KEYS = {k for k in ASSET_FIELDS_SCALAR if 'start' in k or 'end' in k or 'date' in k}

OPEX_BLOCKS = [
    (126, 127, 128, '€/MWh', 'OPEX €/MWh (period 1)'),
    (132, 133, 134, '€/MWh', 'OPEX €/MWh (period 2)'),
    (149, 150, 151, 'k€/year', 'OPEX k€ /Year'),
    (155, 156, 157, 'k€/year', 'OPEX Period kEUR/YEAR'),
    (161, 162, 163, 'k€/year', 'Loyer'),
    (167, 168, 169, 'k€/year', 'Loyer / OPEX'),
    (173, 174, 175, 'k€/year', '[OPEX k€/year] #1'),
    (179, 180, 181, 'k€/year', '[OPEX k€/year] #2'),
]

# ------- D&A durations (mois) --------
# ass_Asset r207/r208 (type1/type2), ass_Vehicle r366 (vehicle/perimeter) : tous 240/120.
da_months_type1 = int(num(aa.iat[206, 8], 240))   # ass_Asset r207 col I
da_months_type2 = int(num(aa.iat[207, 8], 120))   # ass_Asset r208 col I
da_months_vehicle = int(num(veh.iat[365, 12], 240))   # ass_Vehicle r366
da_months_perimeter = da_months_vehicle

# ------- local taxes constants (ass_Model) --------
# IFER duration (years) : ass_Model M94 (0-based row 93, col 12)
ifer_years = int(num(model_sheet.iat[93, 12], 20))

# CVAE schedule : ass_Model years row26, sponsor rate row49, CCI row52 ; cols M..T = 12..19
cvae_years, cvae_rate, cvae_cci = [], [], []
for col in range(12, 20):
    y = model_sheet.iat[25, col]
    if not (isinstance(y, (int, float)) and not isinstance(y, bool)):
        continue
    cvae_years.append(int(y))
    cvae_rate.append(round(num(model_sheet.iat[48, col], 0.0), 8))
    cvae_cci.append(round(num(model_sheet.iat[51, col], 0.0), 8))
# added-value limitation : M22 threshold, M23 low rate, M24 high rate (0-based rows 21/22/23)
cvae_va_threshold = num(model_sheet.iat[21, 12], 7600.0)
cvae_va_rate_low = num(model_sheet.iat[22, 12], 0.80)
cvae_va_rate_high = num(model_sheet.iat[23, 12], 0.85)

ref_row = aa.iloc[7]
asset_cols = list(range(12, aa.shape[1]))

n_assets = 0
for c in asset_cols:
    if not as_bool(aa.iat[15, c]):   # Asset activation (row16)
        continue
    ref_v = aa.iat[7, c]
    if not isinstance(ref_v, (int, float)) or isinstance(ref_v, bool):
        continue
    spv_name = ref_to_name.get(int(ref_v))
    if spv_name is None or spv_name not in vehicles:
        continue

    asset_name = aa.iat[2, c]
    asset_name = asset_name if isinstance(asset_name, str) else str(asset_name)

    a = {}
    for key, ridx in ASSET_FIELDS_SCALAR.items():
        if key == 'name':
            continue  # name is the table key, not a field
        v = aa.iat[ridx, c]
        if key in DATE_KEYS:
            a[key] = as_date(v)
        elif key in ('type', 'typology'):
            a[key] = v if isinstance(v, str) else str(v)
        else:
            a[key] = v
    a['master_activation'] = True

    a['installed_capacity'] = [num(aa.iat[59, c]), 'kWc']
    a['revenues_inflation'] = aa.iat[92, c] if isinstance(aa.iat[92, c], str) else 'IPC'
    a['capacity_degradation_rate_lenders'] = num(aa.iat[62, c])
    a['capacity_degradation_rate_sponsor'] = num(aa.iat[63, c])
    a['production_availability_lenders'] = num(aa.iat[80, c], 1.0)
    a['production_availability_sponsor'] = num(aa.iat[81, c], 1.0)
    a['yield_lenders'] = aa.iat[69, c] if aa.iat[69, c] in ('P50', 'P90') else 'P90'
    a['yield_sponsor'] = aa.iat[70, c] if aa.iat[70, c] in ('P50', 'P90') else 'P50'
    a['yield_portofolio_effect'] = num(aa.iat[73, c])
    a['yield_excl_capacity_p50'] = num(aa.iat[76, c])
    a['yield_excl_capacity_p90'] = num(aa.iat[75, c])
    a['self_consumption'] = as_bool(aa.iat[52, c])
    a['self_consumption_annual_fee'] = num(aa.iat[53, c])
    a['contracted_revenues_ref_tariff'] = [num(aa.iat[87, c]), '€ / MWh']
    a['contracted_revenues_bonus_tariff'] = [num(aa.iat[88, c]), '€ / MWh']
    a['contracted_revenues_malus_tariff'] = [num(aa.iat[89, c]), '€ / MWh']
    a['contracted_revenues_malus_activation'] = as_bool(aa.iat[90, c])
    a['contracted_revenues_yield_threshold_activation'] = as_bool(aa.iat[94, c])
    merch = aa.iat[103, c]
    a['revenues_merchant_price_scenario'] = merch if isinstance(merch, str) else 'Mid'
    a['opex'] = 0
    a['local_taxes'] = 0
    a['contracted_revenues_yield_threshold'] = num(aa.iat[95, c])
    a['contracted_revenues_yield_tariff_above_threshold'] = [num(aa.iat[96, c]), '€ / MWh']

    # OPEX contracts
    opex_list = []
    for (br, sr, er, unit, bname) in OPEX_BLOCKS:
        base = aa.iat[br, c]
        if not isval(base) or float(base) == 0.0:
            continue
        st = as_date(aa.iat[sr, c])
        en = as_date(aa.iat[er, c])
        if st is None or en is None:
            continue
        tag = aa.iat[br, 8]
        opex_list.append({
            'name': bname,
            'price': [float(base), unit],
            'start date': st,
            'end date': en,
            'inflation': tag if tag in ('IPC', '20% IPC', '30% IPC', '40% IPC') else 'IPC',
        })
    a['OPEX'] = opex_list

    # ---- LOCAL TAXES ----
    # IFER (Portfolio r9148): capacite injectee (ass_Asset r191), taux avant/apres 20 ans
    # (r193/r194), duree (ass_Model M94), inflation IPC ; date de reference = COD (r30).
    ifer_cap = aa.iat[190, c]
    if isval(ifer_cap) and float(ifer_cap) != 0.0:
        a['IFER'] = {
            'capacity_kW': float(ifer_cap),
            'rate_before': num(aa.iat[192, c]),
            'rate_after': num(aa.iat[193, c]),
            'years': ifer_years,
            'inflation': 'IPC',
        }

    # Other taxes (Portfolio r9652): forfait k€/an, prorata jours, inflation IPC.
    other_amount = aa.iat[198, c]
    other_start = as_date(aa.iat[199, c])
    other_end = as_date(aa.iat[200, c])
    other_list = []
    if isval(other_amount) and float(other_amount) != 0.0 and other_start and other_end:
        other_list.append({
            'name': 'Other taxes',
            'price': [float(other_amount), 'k€/year'],
            'start date': other_start,
            'end date': other_end,
            'inflation': 'IPC',
        })
    a['OTHER_TAXES'] = other_list

    # ---- CAPEX (cout de construction, ass_Asset) ----
    # type1 (r223, amorti da_months_type1) + type2 (r224) + vehicle (r225) + perimeter (r226).
    a['capex'] = {
        'type1': num(aa.iat[222, c]),
        'type2': num(aa.iat[223, c]),
        'vehicle': num(aa.iat[224, c]),
        'perimeter': num(aa.iat[225, c]),
    }

    # ---- Echeancier de decaissement du CAPEX (ass_Asset r330-425) ----
    # colonne E (idx4) = periode mensuelle 1..96 ; periode 1 <-> 2025-01 (model.time[0]).
    # Le decaissement pilote le CAPEX cash, le profil annuel du D&A, et l'injection SHL.
    sched_periods, sched_amounts = [], []
    for rr in range(329, 425):  # r330..r425
        E = aa.iat[rr, 4]
        if not isinstance(E, (int, float)) or isinstance(E, bool):
            continue
        val = aa.iat[rr, c]
        if isval(val) and float(val) != 0.0:
            sched_periods.append(int(E))
            sched_amounts.append(round(float(val), 6))
    a['capex_schedule'] = {'periods': sched_periods, 'amounts': sched_amounts}

    node = vehicles[spv_name]
    node.setdefault('assets', {})
    node['assets'][asset_name] = a
    n_assets += 1

# ensure every SPV has an assets table
for v in vehicles.values():
    if v['type'] == 'SPV':
        v.setdefault('assets', {})

# D&A vehicle (Excel SPV!r413) = somme ass_Asset r225 pour TOUTES les colonnes du
# SPV (actifs + inactifs). Perimeter (r420) filtre en plus une typologie — on
# conserve la somme des seuls actifs actives (deja dans asset.capex.perimeter).
_ref_to_veh = {v.get('_veh_ref'): v for v in vehicles.values() if v.get('_veh_ref') is not None}
for c in range(12, aa.shape[1]):
    pref = aa.iat[7, c]
    if pref is True:
        pref = 1
    if not isinstance(pref, (int, float)) or isinstance(pref, bool):
        continue
    node = _ref_to_veh.get(int(pref))
    if node is None:
        continue
    node['da_vehicle_capex'] = round(node.get('da_vehicle_capex', 0.0) + num(aa.iat[224, c]), 6)
for v in vehicles.values():
    peri = sum(
        float((a.get('capex') or {}).get('perimeter', 0.0) or 0.0)
        for a in v.get('assets', {}).values()
    )
    v['da_perimeter_capex'] = round(peri, 6)
    v.pop('_veh_ref', None)

# ---------------------------------------------------------------- market prices
scenarios = set()
for v in vehicles.values():
    for a in v.get('assets', {}).values():
        scenarios.add(a['revenues_merchant_price_scenario'])

market_price_scenario = dict(market_price_scenario_full)
for s in scenarios:
    if s not in market_price_scenario:
        market_price_scenario[s] = [0.0] * len(market_price_years)

market_block = {
    'ipc_years': ipc_years,
    'ipc_base_rate': ipc_base_rate,
    'ipc_percentage': [1.0, 0.2, 0.3, 0.4],
    'ipc_scenario': ['IPC', '20% IPC', '30% IPC', '40% IPC'],
    'market_price_years': market_price_years,
    'market_price_scenario': market_price_scenario,
    'cvae': {
        'years': cvae_years,
        'rate': cvae_rate,
        'cci': cvae_cci,
        'va_threshold': cvae_va_threshold,
        'va_rate_low': cvae_va_rate_low,
        'va_rate_high': cvae_va_rate_high,
    },
    'da_months': {
        'type1': da_months_type1,
        'type2': da_months_type2,
        'vehicle': da_months_vehicle,
        'perimeter': da_months_perimeter,
    },
    # ---- fiscalite (Phase 4), ass_Model ----
    # IS r56, report de deficits r59/r60 (seuil plein + proportion au-dela),
    # rabot deductibilite interets SHL r79 (taux plafond ATAD).
    'tax': {
        'cit_rate': num(model_sheet.iat[55, 12], 0.25),
        'loss_threshold': num(model_sheet.iat[58, 12], 1000.0),
        'loss_proportion': num(model_sheet.iat[59, 12], 0.5),
        'shl_deductibility_rate': num(model_sheet.iat[78, 12], 0.0464),
        # ATAD / thin-cap (ass_Model M71-M76)
        'thin_cap_ratio': num(model_sheet.iat[70, 12], 1.5),
        'atad_t1_floor': num(model_sheet.iat[71, 12], 3000.0),
        'atad_t1_rate': num(model_sheet.iat[72, 12], 0.30),
        'atad_t2_floor': num(model_sheet.iat[73, 12], 1000.0),
        'atad_t2_rate': num(model_sheet.iat[74, 12], 0.10),
        'atad_deferral_pct': num(model_sheet.iat[75, 12], 1.0 / 3.0),
        # Contribution sociale sur l'IS (CSB) : 3.3% de la fraction d'IS > 763 k€,
        # si CA agregé > 7630 k€ (ass_Model / SPV G349/G350/J350).
        'csb_turnover_threshold': 7630.0,
        'csb_cit_threshold': 763.0,
        'csb_rate': 0.033,
        # Produits de cash pooling dans la base IS (Excel r282 inclut r149).
        # Modulable : false si un modele source les exclut.
        'cit_include_cash_pooling': True,
        # Acomptes IS (Excel F332:F335 = 1/n) — FR classique = 4.
        'cit_n_deposits': 4,
    },
}

# ---------------------------------------------------------------- assemble & write
for v in vehicles.values():
    v.pop('_veh_ref', None)

doc = {
    'dashboard': dashboard,
    'model': model,
    'market': market_block,
    'vehicle': vehicles,
}

with open(OUT, 'wb') as f:
    tomli_w.dump(doc, f)

n_spv = sum(1 for v in vehicles.values() if v['type'] == 'SPV')
print(f'OK -> {OUT}')
print(f'  vehicles: {len(vehicles)} | SPV: {n_spv} | assets actifs: {n_assets}')
print(f'  ipc_years: {ipc_years[0]}..{ipc_years[-1]} ({len(ipc_years)})')
print(f'  merchant scenarios: {sorted(scenarios)}')
for name, v in vehicles.items():
    na = len(v.get('assets', {})) if v['type'] == 'SPV' else '-'
    print(f'    {name:10} {v["type"]:7} parent={v.get("parent","-"):10} assets={na}')
