from mca_model.model import electricity 

# EBITDA

def total_revenues_from_electricity_production(*args):
    """"""
    
    return \
        electricity.contracted.revenues(*args) +\
        electricity.merchant.revenues(*args)



def dividend(*args):
    """"""
    return 0


def non_cash_dividend(*args):
    """"""
    return 0


def SHL_to_be_paid_for_PnL(*args):
    """"""
    return 0


def total_opex(*args):
    """"""
    return 0


def agency_fees(*args):
    """"""
    return 0


def total_local_taxes(*args):
    """"""
    return 0


def crowdfunding_premium_to_be_paid_to_crowdfunders(*args):
    """"""
    return 0

    
# EBIT

def DnA(*args):
    """"""
    return 0


# EBT

def senior_facilities_interests(*args):
    """"""
    return 0


def total_interests_and_fees_DSRF(*args):
    """"""
    return 0


def junior_facility_interests_to_be_paid(*args):
    """"""
    return 0


def crowdfunding_interests_to_be_paid(*args):
    """"""
    return 0


def SHL_interests_to_be_paid(*args):
    """"""
    return 0


def cash_pooling_interests_to_be_paid(*args):
    """"""
    return 0

# net_result

def corporate_income_tax_due(*args):
    """"""
    return 0
