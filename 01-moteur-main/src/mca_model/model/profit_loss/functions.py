from mca_model import Model, Asset
from mca_model.model import electricity
from mca_model.model import opex
from mca_model.model import taxes
from mca_model.model import capex as capex_mod
from mca_model.model import financing as fin_mod

# EBITDA

def total_revenues_from_electricity_production(m: Model, a: Asset, **kwargs):
    """Revenus totaux (contracte + merchant), convertis en k€ (convention Excel / SPV)."""

    return (
        electricity.contracted.revenues(m, a) +
        electricity.merchant.revenues(m, a)
    ) / 1000.0



def dividend(*args):
    """Dividende recu : nul au niveau SPV (remonte au niveau Holdco/Topco - Phase 5)."""
    return 0


def non_cash_dividend(*args):
    """Dividende non cash : nul au niveau SPV (Phase 5)."""
    return 0


def SHL_to_be_paid_for_PnL(*args):
    """Nul au niveau SPV (financement - Phase 4)."""
    return 0


def total_opex(m: Model, a: Asset, **kwargs):
    """OPEX total (k€, negatif)."""
    return opex.get_price(m, a, **kwargs)


def agency_fees(*args):
    """Agency fees : factures au niveau Holdco/Topco -> 0 au niveau SPV (Phase 4)."""
    return 0


def total_local_taxes(m: Model, a: Asset, **kwargs):
    """CVAE + IFER + Other taxes (k€, negatif)."""
    return taxes.total_local_taxes(m, a)


def crowdfunding_premium_to_be_paid_to_crowdfunders(*args):
    """Nul au niveau SPV (financement - Phase 4). Hook pret si active via config."""
    return 0

    
# EBIT

def DnA(m: Model, a: Asset, **kwargs):
    """Dotation aux amortissements (k€, negatif)."""
    return capex_mod.depreciation(m, a)


# EBT

def senior_facilities_interests(*args):
    """Hook senior facility (0 si inactif / non dimensionne). Modulable via config."""
    return 0


def total_interests_and_fees_DSRF(*args):
    """Hook DSRF (0 si inactif). Modulable via config."""
    return 0


def junior_facility_interests_to_be_paid(*args):
    """Hook junior facility (0 si inactif). Modulable via config."""
    return 0


def crowdfunding_interests_to_be_paid(*args):
    """Hook crowdfunding (0 si inactif). Modulable via config."""
    return 0


def SHL_interests_to_be_paid(m: Model, a: Asset, **kwargs):
    """Interets SHL (k€, negatif)."""
    return fin_mod.shl_interests_to_be_paid(m, a)


def cash_pooling_interests_to_be_paid(m: Model, a: Asset, **kwargs):
    """Interets cash pooling (k€, positif = produit)."""
    return fin_mod.cash_pooling_interests(m, a)


# net_result

def corporate_income_tax_due(m: Model, a: Asset, **kwargs):
    """
    Impot sur les societes (IS) du (k€, negatif).
    Inclut ATAD thin-cap, report de deficits, CSB (3.3% au-dela de 763 k€).
    """
    return fin_mod.corporate_income_tax_due(m, a)
