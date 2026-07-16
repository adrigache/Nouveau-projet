from functools import reduce

from . import functions as f


ASSET_COMPONENTS = (
    f.assets,
    f.share_capital_in_vehicle_detention,
    f.SHL_in_SPVS,
    f.cash_pooling_with_shareholders,
    f.MDRA,
    f.MRA,
    f.proceeds_account,
    f.trade_receivables,
)

LIABILITY_COMPONENTS = (
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
    f.trade_payables,
)


def total_assets(*args):
    return reduce(lambda a, b: a + b, map(lambda fn: fn(*args), ASSET_COMPONENTS))


def total_liabilities(*args):
    return reduce(lambda a, b: a + b, map(lambda fn: fn(*args), LIABILITY_COMPONENTS))


def check_balance_sheet(*args):
    """Ecart actif − passif (doit etre ~0)."""
    return total_assets(*args) - total_liabilities(*args)
