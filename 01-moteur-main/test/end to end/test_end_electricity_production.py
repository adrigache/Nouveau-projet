import pytest
from mca_model.model.electricity import contracted as e_contracted

import datetime as dt

from mca_model.model.model import Model
from mca_model.utils import next_month

# local import
import utils as u



def test_revenues_contracted_no_degradation():
    """contracted period"""

    # default - no degradation
    m:Model = u.load_model(0)

    # apply function and get values for first (an unique) asset
    out =  m.compute(e_contracted.revenues)

    # get asset
    (a, found), = out
     
    # test production with no degradation
    in_prod = found[a.operation_contract_start:next_month(a.operation_contract_end)]

    target = a.estimated_revenues_from_electricity_contracted
    assert(pytest.approx(in_prod.median(), rel=.01)== target)  # 1% !



def test_revenues_contracted_with_degradation():
    """contracted period"""

    # default - no degradation
    m:Model = u.load_model(0)
    assert(m.scenario == 'lender')

    # add degradatation
    
    k, a = list(m.spv[0]._assets.items())[0]
    a.capacity_degradation_rate_lender=0.001  # yearly
    a.capacity_degradation_start_date = dt.date(2035, 1, 1)
    m.spv[0]._assets = {k:a}
    
    # apply function and get values for first (an unique) asset
    out =  m.compute(e_contracted.revenues)
 
    # get asset
    (a, found), = out  # only ony asset

    # degradation starts on first month (end of month)
    # target = a.installed_capacity[0]*a.yield_excl_capacity_p90/12*1e-3
    target = a.estimated_revenues_from_electricity_contracted
    not_degraded = found[a.operation_contract_start:a.capacity_degradation_start_date]
    assert( pytest.approx(not_degraded.min(), rel=.1)==target)  # 10%

    degraded = found[a.capacity_degradation_start_date:next_month(a.operation_contract_end)]
    n = 12*(48-35+1) # 2035/01 -> 2048/12 (start on 01 Jan)
    assert(n == degraded.index.size)
    assert(degraded.index[-1].date() == a.operation_contract_end)
    assert(degraded.median() < 1.01*target)


    rm = (1-a.capacity_degradation_rate_lender)**(1/12)  # monthly degradation

    ref = degraded.iloc[1] # full month
    assert(pytest.approx(degraded.iloc[2], rel=1e-6)== ref*rm)
    assert(pytest.approx(degraded.iloc[3], rel=1e-6)== ref*rm**2)
    assert(pytest.approx(degraded.iloc[4], rel=1e-6)== ref*rm**3)
   
  
    # last
    # last_prod = degraded.iloc[-1]
    # target = target * (1-a.capacity_degradation_rate_lender)**(48-35+1)
    # assert(pytest.approx(last_prod, rel=1e-9)== target)
