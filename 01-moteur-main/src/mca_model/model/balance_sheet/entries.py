
from . import functions as f

# TODO: passer en fonctionnel comme P&L


def total_assets(*args):
    """"""

    functions = [
        f.assets,
        f.share_capital_in_vehicle_detention,
        f.SHL_in_SPVS,
        f.cash_pooling_with_shareholders,
        f.MDRA,
        f.MRA,
        f.proceeds_account,
        f.trade_receivables
    ]
    
    return sum(f(*args) for f in functions)


def total_liabilities(*args):
    """"""
    
    functions = [
        f.share_capital,
        f.legal_reserves,
        f.retained_earnings,
        f.crowdfunding,
        f.SHL,
        f.cash_pooling_with_vehicle_detention,
        f.senior_facility,
        f.DSRF_facility,
        f.EBL,
        f.junior_facility,
        f.VAT_facility_EoP,
        f.corporate_income_tax_payable,
        f.crowdfunding_interest_payable,
        f.junior_facility_interests_payable,
        f.SHL_interest_payable,
        f.trade_payables
        ]
    
    return sum(f(*args) for f in functions)

# check b/s overview
