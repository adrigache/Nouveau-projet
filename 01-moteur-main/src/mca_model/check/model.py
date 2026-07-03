from __future__ import annotations

from mca_model import Model
from mca_model.config import rc


def check(m:Model):
    """entry point for full model check"""

    check_dashboard(m)
    check_model(m)
    check_market(m)
    check_vehicles(m)
    check_assets(m)


    
def check_dashboard(m:Model):
    """"""
    
def check_model(m:Model):
    """"""
    
def check_market(m:Model):
    """"""
    
    # inflation
    a = m.ipc_percentage
    b = m.ipc_scenario
    assert( (a[0], b[0]) == (1,'IPC'))
    assert( [f'{r:.0%} IPC' for r in a[1:]] == b[1:])

    # market prices
    for k,v in m.market_price_scenario.items():
        assert(len(v) == len(m.market_price_years))

    scenarios = list(m.market_price_scenario.keys())
    
    f = lambda a:a.revenues_merchant_price_scenario in scenarios
    assert(all(list(map(f,  m.list_assets()))))
    
 
def check_vehicles(m:Model):
    """"""

    
def check_assets(m:Model):
    """"""

    scenarii = m.ipc_scenario

    # 
    for a in m.list_assets():
        if a.revenues_inflation not in scenarii:
            rc.fail(f'Asset {a.name} has wrong `revenues_inflation` value : {a.revenues_inflation} not in list {scenarii}')
            raise ValueError(f'error while checking assets')
   
    # times
    for a in m.list_assets():
        if a.master_activation:
            assert(a.construction_start <= a.construction_end)
            assert(a.construction_end <= a.operation_contract_start)
            assert(a.operation_contract_start <= a.operation_contract_end)
            assert(a.merchant_pre_contract_start <= a.operation_contract_start)
            assert(a.merchant_pre_contract_start <= a.merchant_pre_contract_end)
            assert(a.operation_contract_end <=  a.merchant_post_contract_start)
            assert(a.merchant_post_contract_start <= a.merchant_post_contract_end)


    
        
