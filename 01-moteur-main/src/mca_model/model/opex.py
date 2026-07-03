import pandas as pd
from mca_model import Model, Asset
from mca_model.service import helpers
from mca_model.model import inflation
from mca_model.model.electricity.production import compute_raw_production

def get_price_euros_by_MWh(m: Model, a: Asset, opex: dict) -> pd.Series:
    """
    Calcule l'OPEX variable (indexé sur la production).
    """
    # 1. On récupère le prix de base en €/MWh
    base_price = opex['price'][0]
    
    # 2. On récupère la production mensuelle exacte en MWh pour cet actif
    production_mwh = compute_raw_production(m, a)
    
    # 3. On applique la fenêtre temporelle de l'OPEX (start date -> end date)
    start_date = opex.get('start date')
    if pd.isna(start_date) or start_date is None:
        start_date = a.operation_contract_start
        
    end_date = opex.get('end date')
    if pd.isna(end_date) or end_date is None:
        end_date = a.operation_contract_end

    # Fraction de jours d'opération dans le mois pour cet OPEX
    active_days_frac = helpers.days_in_range_per_month(m.time, start_date, end_date, m.debug)
    
    # 4. On récupère l'inflation si elle existe
    inflation_tag = opex.get('inflation')
    if inflation_tag and str(inflation_tag).lower() not in ['none', 'nan', '']:
        # Note: L'inflation est généralement gérée au niveau du modèle global.
        # Pour rester simple, on utilise le helper d'inflation si l'actif l'a.
        # Ici on simule l'indexation. Si tu as un module inflation générique, on l'appelle.
        # Par défaut, on va relier l'inflation de l'actif.
        inflation_index = inflation.compute(m, a)
    else:
        inflation_index = pd.Series(1.0, index=m.time)

    # 5. Calcul: Prod (MWh) * (Prix de base * Inflation) * Filtre de dates
    # On masque la production en dehors des dates de contrat OPEX
    cost_euros = (production_mwh * active_days_frac) * (base_price * inflation_index)
    
    # 6. Conversion en k€ car le Cash Flow Waterfall s'exprime en k€
    cost_keuros = cost_euros / 1000.0
    
    # Convention comptable : Les coûts sortants sont négatifs dans l'Overview
    return -cost_keuros


def get_price_euros_by_year(m: Model, a: Asset, opex: dict) -> pd.Series:
    """
    Calcule l'OPEX fixe (forfait annuel en k€).
    """
    # 1. On récupère le prix de base en k€/year
    base_price_keuros = opex['price'][0]
    
    # 2. Fenêtre temporelle de l'OPEX
    start_date = opex.get('start date')
    if pd.isna(start_date) or start_date is None:
        start_date = a.operation_contract_start
        
    end_date = opex.get('end date')
    if pd.isna(end_date) or end_date is None:
        end_date = a.operation_contract_end

    # Fraction de jours par mois
    active_days_frac = helpers.days_in_range_per_month(m.time, start_date, end_date, m.debug)
    
    # 3. Le coût mensuel de base (Prix annuel / 12)
    # L'Excel projette souvent le coût annuel réparti sur les mois, proratisé par les jours.
    monthly_base_cost = (base_price_keuros / 12.0) * active_days_frac
    
    # 4. Inflation
    inflation_tag = opex.get('inflation')
    if inflation_tag and str(inflation_tag).lower() not in ['none', 'nan', '']:
        inflation_index = inflation.compute(m, a)
    else:
        inflation_index = pd.Series(1.0, index=m.time)

    # 5. Calcul final en k€
    cost_keuros = monthly_base_cost * inflation_index
    
    # Convention comptable : Les coûts sortants sont négatifs
    return -cost_keuros


def get_price(m: Model, a: Asset, **kwargs) -> pd.Series:
    """
    Point d'entrée de l'OPEX pour un Actif. 
    Somme tous les contrats OPEX (O&M, Management, etc.) rattachés à cet actif.
    """
    total_opex = pd.Series(0.0, index=m.time)
    
    # Si l'actif n'a pas d'OPEX extrait, on renvoie 0
    if not hasattr(a, 'OPEX') or not a.OPEX:
        return total_opex

    for opex_contract in a.OPEX:
        unit = opex_contract['price'][1]
        
        # Dispatch selon l'unité de l'Excel
        if unit == '€/MWh':
            cost = get_price_euros_by_MWh(m, a, opex_contract)
        elif unit == 'k€/year':
            cost = get_price_euros_by_year(m, a, opex_contract)
        else:
            raise NotImplementedError(f"OPEX unit unknown: {unit}")
            
        total_opex = total_opex.add(cost, fill_value=0)

    return total_opex
