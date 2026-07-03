import pytest
import pandas as pd
import datetime as dt

from typing import cast
# import termplotlib as tpl

from mca_model import Model, Asset
from mca_model.model.electricity import production
from mca_model.model.electricity import contracted
from mca_model.model.electricity import merchant

from mca_model.utils import (
    ONE_DAY,
    THIRTY_DAYS,
    ONE_YEAR,
    first_day_of_month,
    next_month)


from conftest import Node


def termplot(a, df):
    import plotext as plt
    plt.theme("clear")   # built-in theme with no background

    plt.clear_data()
    plt.scatter(df.index.year, df.values, marker='dot')
    plt.ylim( 0., 1.3*max(df.values))
    plt.plotsize(height=12)
    plt.xticks(df.index.year[::5])
    plt.title(f'{a.name} > {df.name}')
    plt.show()
    


            

def test_electricity_contracted_production_in_MWh(model):
    found = model.compute(contracted.in_MWh)

    for a, results in found:
        # checks are one in function call
        by_year = results.resample('YE').sum()

        # target - in MW
        if a.master_activation:
            target = 12*a.estimated_electricity_production_p50
            assert( pytest.approx(by_year.max(), rel=0.1) == target)  # 10%
            termplot(a, by_year)

        else:
            a.name == 'Actif_2'
            assert(by_year.max() == 0)


            

def test_electricity_merchant_production_in_MWh(model):
    found = model.compute(merchant.in_MWh)

    print(found)
    
    # for a, results in found:
    #     # checks are one in function call
    #     by_year = results.resample('YE').sum()

    #     # target - in MW
    #     if a.master_activation:
    #         target = 12*a.estimated_electricity_production_p50
    #         assert( pytest.approx(by_year.max(), rel=0.1) == target)  # 10%
    #         termplot(a, by_year)

    #     else:
    #         a.name == 'Actif_2'
    #         assert(by_year.max() == 0)

            
            
def test_time_selection():

    # build model and asset
    T0, T1 = dt.date(2000,1,1), dt.date(2010,12,31)
    t0, t1 = dt.date(2001,2,1),  dt.date(2008,5,13)
    m = Node({
        'time': pd.date_range(T0, T1, freq='ME'),
        't_start': T0,
        't_end': T1,
        })
    a = Node({
        'operation_contract_start': t0 ,
        'operation_contract_end': t1,
        } )

    # dummy call - output in in end of month
    found = contracted.f_days_of_electricity(cast(Model,m), cast(Asset,a))

    assert(found.loc[:t0].index.size + found.loc[t0:].index.size == found.index.size)
    
    # check time selection
    assert(found.index[0] == pd.Timestamp(year=2000, month=1, day=31))
    assert(found.index[-1] == pd.Timestamp(year=2010, month=12, day=31))

    # t0 not included
    assert(found.loc[:t0].index[-1] == pd.Timestamp(year=2001, month=1, day=31))

    #
    assert(found.loc[t0:t1].index[0] == pd.Timestamp(year=2001, month=2, day=28))
    assert(found.loc[t0:t1].index[-1] == pd.Timestamp(year=2008, month=4, day=30)) # ok
    

        
def test_f_days_of_electricity_contracted():


    # build model and asset
    T0, T1 = dt.date(2000,1,1), dt.date(2010,12,31)
    t0, t1 = dt.date(2001,2,3),  dt.date(2008,5,13)
    m = Node({
        'time': pd.date_range(T0, T1, freq='ME'),
        't_start': T0,
        't_end': T1,
        })
    a = Node({
        'operation_contract_start': t0 ,
        'operation_contract_end': t1} )

    # compute
    found = contracted.f_days_of_electricity(cast(Model,m), cast(Asset,a))

    # checks
    assert(found.loc[:t0].max()==0)
    assert(found.loc[t0:t1].max()==1)

    # all days are included
    assert(pytest.approx(found.loc[t0:].iloc[0], abs=0.001)==(28-3+1)/28)
    assert(found.loc[t1:].index[0] == pd.Timestamp(year=2008,month=5, day=31))
    assert(pytest.approx(found.loc[t1:].iloc[0], abs=0.001)==13/31)


def test_f_days_of_electricity_merchant():


    # build model and asset
    T0, T1 = dt.date(2000,1,1), dt.date(2010,12,31)
    t0, t1 = dt.date(2001,2,3),  dt.date(2002,5,13)
    t2, t3 = dt.date(2005,2,3),  dt.date(2008,5,13)
    
    m = Node({
        'time': pd.date_range(T0, T1, freq='ME'),
        't_start': T0,
        't_end': T1,
        })
    a = Node({
        'merchant_pre_contract_start': t0 ,
        'merchant_pre_contract_end': t1 ,
        'merchant_post_contract_start': t2 ,
        'merchant_post_contract_end': t3 ,
        
        } )

    # compute
    found = merchant.f_days_of_electricity(cast(Model,m), cast(Asset,a))

    # checks
    assert(found.loc[:t0].max()==0)
    assert(found.loc[t0:t1].max()==1)
    assert(found.loc[dt.date(2002,6,1):dt.date(2005,1,31)].max()==0)
    assert(found.loc[t2:t3].max()==1)
    assert(found.loc[dt.date(2008,6,1):].max()==0)




    
def test_f_capacity_degradation():

    # build model and asset
    T0, T1 = dt.date(2000,1,1), dt.date(2010,12,31)
    t0 = dt.date(2001,2,3)
    rate = 0.05                        # degradation
    monthly_rate = 1-(1-rate)**(1/12)  # degradation 
    
    m = Node({'time': pd.date_range(T0, T1, freq='ME'), 'scenario':'lender'})
    a = Node({
        'capacity_degradation_rate_lender': rate, # yearly
        'capacity_degradation_start_date': t0})

    # errors
    with pytest.raises(AttributeError):
        missing = Node( {'time':m.time})
        production.f_capacity_degradation(cast(Model,missing), cast(Asset,a))

    with pytest.raises(AttributeError):
        missing = Node( {'time':m.time, 'scenario':'unknown'})
        production.f_capacity_degradation(cast(Model,missing), cast(Asset,a))
        
    # compute
    found = production.f_capacity_degradation(cast(Model,m), cast(Asset,a))

    #
    assert(found.loc[:t0].max()==1)
    assert(found.loc[:t0].index.size + found.loc[t0:].index.size == found.index.size)

    degraded = found.loc[t0:]
    assert(degraded.max()<1)

    y0 = degraded.loc[dt.date(2001,3,1):dt.date(2002,4,1)]
    assert(y0.index.size == 13)  # 12 application of monthly rate
    observed_rate = y0.min() / y0.max()
    assert( pytest.approx(observed_rate, abs=1e-6) == 1-rate)
    
    observed_rate_first_month = degraded.iloc[0]/1.0
    assert( observed_rate_first_month > 1-monthly_rate)
    observed_rate_second_month = degraded.iloc[1]/degraded.iloc[0]
    assert( pytest.approx(observed_rate_second_month, abs=1e-6) == 1-monthly_rate)

    n_years = (T1-t0).days//365 
    assert(n_years==9)
    y10 = found.loc[:dt.date(2010,4,1)]
    observed_rate = 1 - y10.min()/y10.max() # degradation
    assert( observed_rate > 1-(1-rate)**n_years)
    assert( observed_rate < 1-(1-rate)**(n_years+1))
    
    
    
def test_f_price_contracted_FiT(model):

    # build model and asset
    T0, T1 = dt.date(2000,1,1), dt.date(2010,12,31)
    t0, t1 = dt.date(2001,2,1),  dt.date(2008,5,31)
       
    m = Node({
        'time': pd.date_range(T0, T1, freq='ME'),
        'scenario':'lender'})
    

    # simulate production 
    prod = pd.Series(100, index=m.time)
    prod.loc[:t0] = 0
    prod.loc[t1-ONE_YEAR:t1] = 50
    prod.loc[next_month(t1):] = 0
    
    # get price - no threshold
    a = Node({
        'contracted_revenues_ref_tariff': (42, '€ / MWh'),
        'contracted_revenues_yield_threshold_activation':False
        })

    found = contracted.f_price_FiT(cast(Model,m), cast(Asset,a), prod)

    assert(found[found.index.year==2000].max()==0)
    assert(found[found.index.year==2001].sum()==11*42*100)
    assert(found[found.index.year==2008].sum()==5*42*50)


    # get price - with threshold
    a = Node({
        'contracted_revenues_ref_tariff': (1, '€ / MWh'),
        'contracted_revenues_yield_threshold_activation': True,
        'contracted_revenues_yield_threshold': 550,
        'contracted_revenues_yield_tariff_above_threshold': (2, '€ / MWh')
        })


    # 179 jours sous le seuil 
    found = contracted.f_price_FiT(cast(Model,m), cast(Asset,a), prod)

    f = lambda x:found[found.index.year==x].sum()
    assert(f(2000)==0)
    assert(pytest.approx(f(2001), rel=1e-6)==(500*1+500*2+ 100*(15/31+2*16/31)))
    assert(pytest.approx(f(2002), rel=1e-6)==(500*1+600*2+ 150))
    assert(pytest.approx(f(2008), rel=1e-6)==(250*1))
    assert(f(2010)==0)



    
    
    
def test_contracted_revenues(model):

    # build model and asset
    T0, T1 = dt.date(2000,1,1), dt.date(2010,12,31)
    t0, t1 = dt.date(2001,2,3),  dt.date(2008,5,13)
    t = pd.date_range(T0, T1, freq='ME')
      
    m = Node({
        'time': t,
        't_start': T0,
        't_end': T1,
        'scenario':'lender',
        'inflation_start': dt.date(2000, 1, 1),

        'ipc_years': [ x.year for x in t ],
        'ipc_base_rate': [ 0 for i,x in enumerate(t) ],
        'ipc_percentage':[1, 0.2, .3, .4],
        'ipc_scenario':["IPC", "20% IPC", "30% IPC", "40% IPC"]
        })
        
    a = Node({
        'name':'foo',
        'master_activation': True,
        'operation_contract_start': t0 ,
        'operation_contract_end': t1,
        
        # about capacity
        'installed_capacity': (100, 'kWc'),
        'yield_lender':'P90',
        'yield_excl_capacity_p90':1300,
        'capacity_degradation_start_date': t0,
        'capacity_degradation_rate_lender': 0,
        'yield_portofolio_effect':0,
        'production_availability_lender':1,

        # about price
        'revenues_inflation': 'IPC',
        'self_consumption': False,
        'contracted_revenues_ref_tariff': (42, '€ / MWh'),
        'contracted_revenues_yield_threshold_activation': False,
        'contracted_revenues_malus_activation': False,
        'contracted_revenues_bonus_tariff': (10, '€ / MWh'),
        # 'contracted_revenues_malus_tariff': (-5, '€ / MWh'),
        # 'contracted_revenues_bonuss_activation': False,

    })

    # compute
    found = contracted.revenues(cast(Model,m),  cast(Asset,a))

    before_operation = found[found.index<pd.to_datetime(t0)]
    assert(before_operation.max()==0)
    
    after_operation = found[found.index>pd.to_datetime(t1)+THIRTY_DAYS]
    assert(after_operation.max()==0)


    operation = found.truncate(before=pd.to_datetime(t0), after=pd.to_datetime(t1))

    first_month = operation[t0:dt.date(2001,3,1)].iloc[0]
    second_month = operation[dt.date(2001,3,1):dt.date(2001,4,1)].iloc[0]
    last_full_month = operation[operation.index.year==2008].iloc[3]
    assert(first_month<second_month)  # first month is incomplete
    
    assert(pytest.approx(last_full_month, rel=1e-4) == second_month) # no inflation or degradation

    factor = 1e-3 # prod en kW, prix en euro/MWh
    target = (100*1300/12)*(42+10)*factor
    assert(pytest.approx(second_month, rel=1e-2) == target)

    
    # compute - add inflation
    m.ipc_base_rate = [ 0.01 for i,x in enumerate(t) ]
    a.contracted_revenues_bonus_tariff = (0, '€ / MWh')

    found = contracted.revenues(cast(Model,m),  cast(Asset,a))

    second_month = found[found.index.year==2001].iloc[2]
    last_full_month = found[found.index.year==2008].iloc[3]

    assert( pytest.approx(last_full_month/second_month, rel=1e-3) == 1.01**7)

