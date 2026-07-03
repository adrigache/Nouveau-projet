from . import functions as f
from functools import reduce


EBITDA_COMPONENTS = (
    f.total_revenues_from_electricity_production,
    f.dividend,
    f.non_cash_dividend,
    f.SHL_to_be_paid_for_PnL,
    f.total_opex,
    f.agency_fees,
    f.total_local_taxes,
    f.crowdfunding_premium_to_be_paid_to_crowdfunders,
)

def EBITDA(*args):
    return reduce(lambda a, b: a + b, map(lambda fn: fn(*args), EBITDA_COMPONENTS))


EBIT_COMPONENTS = [
    EBITDA,
    f.DnA
    ]


def EBIT(*args):
    return reduce(lambda a, b: a + b, map(lambda fn: fn(*args), EBIT_COMPONENTS))



EBT_COMPONENTS = [
        EBIT,
        f.senior_facilities_interests,
        f.total_interests_and_fees_DSRF,
        f.junior_facility_interests_to_be_paid,
        f.crowdfunding_interests_to_be_paid,
        f.SHL_interests_to_be_paid,
        f.cash_pooling_interests_to_be_paid
        ]


def EBT(*args):
    return reduce(lambda a, b: a + b, map(lambda fn: fn(*args), EBT_COMPONENTS))


NET_RESULT_COMPONENTS = [
        EBT,
        f.corporate_income_tax_due
        ]


def net_result(*args):
    return reduce(lambda a, b: a + b, map(lambda fn: fn(*args), NET_RESULT_COMPONENTS))
