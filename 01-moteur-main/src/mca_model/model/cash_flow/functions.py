
from mca_model import Model, Asset
from mca_model.model import electricity

# functions for operating_cf
def cash_proceeds_account_BoP(*args):
    """
    HYPO: ce sont le montant du cashflow de la période précédente
    """
    return 0


def total_revenues_from_electricity_production(m:Model, a:Asset, **kwargs):
    """"""

    return \
        electricity.contracted.revenues(m, a) +\
        electricity.merchant.revenues(m, a)



def dividend(*args):
    """"""

    return 0


def SHL_interests(*args):
    """"""
    return 0


def SHL_repayment_BoP(*args):
    """"""
    return 0


def cash_pooling(*args):
    """"""
    return 0


def total_opex(*args):
    """"""
    return 0


def agency_fees(*args):
    """"""
    return 0


def corporate_income_tax_paid(*args):
    """"""
    return 0


def total_local_taxes(*args):
    """"""
    return 0


def net_flow_of_WCR(*args):
    """"""
    return 0





# CFADS
 
def CAPEX(*args):
    """"""
    return 0


def development_fees_variable(*args):
    """"""
    return 0


def share_capital_injection_in_vehicles(*args) :
    """"""
    return 0


def prior_SHL_from_holdco_injection_to_be_refinanced_at_financial_close(*args):
    """"""
    return 0


def SHL_injection_in_SPV(*args):
    """"""
    return 0


def upfront_fees_1st_period(*args):
    """"""
    return 0


def senior_facilities_interests_and_commitment_fees(*args):
    """"""
    return 0


def crowdfunding_premium_to_be_paid_to_crowdfunders(*args):
    """"""
    return 0


def share_capital_drawdown(*args):
    """"""
    return 0


def EBL_drawdown(*args):
    """"""
    return 0


def SHL_from_holdco_drawdown(*args):
    """"""
    return 0

def senior_facility_drawdown(*args):
    """"""
    return 0


def VAT_refund(*args):
    """"""
    return 0


def VAT_facility_drawdown(*args):
    """"""
    return 0


def VAT_facility_repayment(*args):
    """"""
    return 0


def VAT_payed(*args):
    """"""
    return 0


def mdra_release_at_last_funding_date_for_mandatory_repayment(*args):
    """"""
    return 0





# CF_available_for_MRA


def senior_facility_interests(*args):
    """"""
    return 0


def senior_facility_repayment(*args):
    """"""
    return 0


def total_interests_and_fees_DSRF(*args):
    """"""
    return 0


def DSRF_drawdown(*args):
    """"""
    return 0


def DSRF_repayment(*args):
    """"""
    return 0


# CF_available_for_MDRA(*args):

def MRA_funding(*args):
    """"""
    return 0



# CF_available_for_junior_facility(*args):

def MDRA_funding(*args):
    """"""
    return 0


def MDRA_release(*args):
    """"""
    return 0




#  CF_available_for_shareholders(*args):

def junior_drawdown(*args):
    """"""
    return 0

def junior_facility_interests_paid(*args):
    """"""
    return 0


def junior_repayment(*args):
    """"""
    return 0


# cash_proceeds_account_EoP(*args):

 
def crowdfunding_interests_paid(*args):
    """"""
    return 0

    
def crowdfunding_injection(*args):
    """"""
    return 0


def SHL_injection_for_crowdfunding_and_EBL_repayment(*args):
    """"""
    return 0


def EBL_repayment(*args):
    """"""
    return 0


def crowdfunding_repayment_via_SHL_injection(*args):
    """"""
    return 0


def share_capital_reduction_crowdfunding(*args):
    """"""
    return 0


def SHL_interests_paid(*args):
    """"""
    return 0

 
def SHL_repayment_EoP(*args):
    """"""
    return 0


def dividend_paid(*args):
    """"""
    return 0


def cash_pooling_addition(*args):
    """"""
    return 0

 
def SHL_injection_to_cover_equity_cash_shortfall(*args):
    """"""
    return 0


def last_actual_cash(*args):
    """"""
    return 0


