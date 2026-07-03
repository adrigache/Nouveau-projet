import pytest
import pandas as pd
import datetime as dt
import numpy as np

from mca_model import Model, Asset
from mca_model.service import helpers

from mca_model.model import inflation
from conftest import Node

    
def test_build_inflation():
    """IPC"""

    t = pd.date_range(dt.date(1999,1,1), dt.date(2002,12,31), freq='ME')

    years = list(range(1999, t.max().year+1))
    rates = [0.01 + 0.001*i for i in range(len(years))]
    rates_by_year = {year:rate for year,rate in zip(years, rates)} 

    # compute
    found = inflation._build(t, rates_by_year)
    assert(found.index.equals(t))
    
    assert( (found[found.index.year==1999]==1).all())
    after_first_year = found[found.index.year>1999]
    
    assert((after_first_year.diff()[1:]>0).all())

    after_one_year = found.loc[dt.date(2000,12,31):].iloc[0]
    assert(pytest.approx(after_one_year) == 1 + rates[1])
    after_two_years = found.loc[dt.date(2001,12,30):].iloc[0]
    assert(pytest.approx(after_two_years) == (1+rates[1])*(1+rates[2]))

    assert(pytest.approx(found.iloc[-1]) == np.prod([1+r for r in rates[1:]]))

    # with modifier
    found = inflation._build(t, rates_by_year, 0.5)
    assert(found.index.equals(t))
    assert( (found[found.index.year==1999]==1).all())
    after_first_year = found[found.index.year>1999]
    assert((after_first_year.diff()[1:]>0).all())

    assert(pytest.approx(found.iloc[-1]) == np.prod([1+r*0.5 for r in rates[1:]]))


    # with start_date
    start = dt.date(2001,3,1)
    found = inflation._build(t, rates_by_year, start=start)

    before_inflation = found[found.index<pd.to_datetime(start)]
    assert((before_inflation==1).all())

    assert(pytest.approx(found.iloc[-1], abs=1e-9) == (1+rates[2])**(10/12)*(1+rates[3]))

    # test again
    rm = helpers.transform_yearly_rate_to_monthly(1+rates[2])
    assert(pytest.approx(found.iloc[-1], abs=1e-9) == rm**10*(1+rates[3]))

    
    
def test_f_price_inflation(model):

    # build model and asset
    T0, T1 = dt.date(2000,1,1), dt.date(2010,12,31)
    t0, t1 = dt.date(2001,2,1),  dt.date(2008,5,31)

    t = pd.date_range(T0, T1, freq='ME')

    years = list(range(2000,2011))
    m = Node({
        'time': t,
        'inflation_start': None,
        'ipc_years': years,
        'ipc_base_rate': [ 0.1+0.001*i for i,x in enumerate(years) ],
        'ipc_percentage':[1, 0.2, .3, .4],
        'ipc_scenario':["IPC", "20% IPC", "30% IPC", "40% IPC"]
        })

    a = Node({'revenues_inflation':'30% IPC'})

    # compute
    found = inflation.compute(m, a)
    assert( (found[found.index.year==2000]==1).all())

    after_one_year = found.iloc[24-1]
    assert(pytest.approx(after_one_year) == (1+0.101*0.3))
    after_two_years = found.iloc[36-1]
    assert(pytest.approx(after_two_years) == (1+0.101*0.3)*(1+0.102*0.3))


    # compute with inflation start date
    m.inflation_start = dt.date(2004,1,1)
    found = inflation.compute(m, a)
    assert( (found[found.index.year<2004]==1).all())

    last_year = found.iloc[-1]
    target = np.prod( [ 1+r*0.3 for r in m.ipc_base_rate[4:]])
    assert(pytest.approx(last_year, abs=1e-9) == target)
