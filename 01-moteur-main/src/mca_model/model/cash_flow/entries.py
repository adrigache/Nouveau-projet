from mca_model import Model, Asset
from mca_model.service.computing import sum_results_by_assets

from . import functions as f


# TODO: passer en fonctionnel comme P&L

def operating_cf(m:Model, **kwargs):
    """level 1"""

    functions = [
        # f.cash_proceeds_account_BoP,
        f.total_revenues_from_electricity_production,
        f.dividend,
        f.SHL_interests,
        f.SHL_repayment_BoP,
        f.cash_pooling,
        f.total_opex,
        f.agency_fees,
        f.corporate_income_tax_paid,
        f.total_local_taxes,
        f.net_flow_of_WCR,
    ]

    return sum_results_by_assets(m, functions, **kwargs)

    
def CFADS(m:Model, **kwargs):
    """"""

    functions = [
        # operating_cf,   # -- added somewhere else
        f.CAPEX,
        f.development_fees_variable,
        f.share_capital_injection_in_vehicles,
        f.prior_SHL_from_holdco_injection_to_be_refinanced_at_financial_close,
        f.SHL_injection_in_SPV,
        f.upfront_fees_1st_period,
        f.senior_facilities_interests_and_commitment_fees,
        f.crowdfunding_premium_to_be_paid_to_crowdfunders,
        f.share_capital_drawdown,
        f.EBL_drawdown,
        f.SHL_from_holdco_drawdown,
        f.senior_facility_drawdown,
        f.VAT_refund,
        f.VAT_facility_drawdown,
        f.VAT_facility_repayment,
        f.VAT_payed,
        f.mdra_release_at_last_funding_date_for_mandatory_repayment
    ]

    return sum_results_by_assets(m, functions, **kwargs)



def CF_available_for_MRA(m:Model, **kwargs):
    """"""
    functions = [
        # CFADS,
        f.senior_facility_interests,
        f.senior_facility_repayment,
        f.total_interests_and_fees_DSRF,
        f.DSRF_drawdown,
        f.DSRF_repayment
    ]

    return sum_results_by_assets(m, functions, **kwargs)


def CF_available_for_MDRA(m:Model, **kwargs):
    """"""
    
    functions = [
        # CF_available_for_MRA,
        f.MRA_funding
        ]
    
    return sum_results_by_assets(m, functions, **kwargs)




def CF_available_for_junior_facility(m:Model, **kwargs):
    """"""

    functions = [
        # CF_available_for_MDRA,
        f.MDRA_funding,
        f.MDRA_release
        ]

    return sum_results_by_assets(m, functions, **kwargs)
    

def CF_available_for_shareholders(m:Model, **kwargs):
    """"""

    functions = [ 
        # CF_available_for_junior_facility,
        f.junior_drawdown,
        f.junior_facility_interests_paid,
        f.junior_repayment
        ]

    return sum_results_by_assets(m, functions, **kwargs)



def cash_proceeds_account_EoP(m:Model, **kwargs):
    """"""

    functions = [
        # CF_available_for_shareholders,
        f.crowdfunding_interests_paid,
        f.crowdfunding_injection,
        f.SHL_injection_for_crowdfunding_and_EBL_repayment,
        f.EBL_repayment,
        f.crowdfunding_repayment_via_SHL_injection,
        f.share_capital_reduction_crowdfunding,
        f.SHL_interests_paid,
        f.SHL_repayment_EoP,
        f.dividend_paid,
        f.cash_pooling_addition,
        f.SHL_injection_to_cover_equity_cash_shortfall,
        f.last_actual_cash
        ]
    
    return sum_results_by_assets(m, functions, **kwargs)

