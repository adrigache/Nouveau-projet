import pytest
import datetime as dt
import pandas as pd
import numpy as np
from dateutil.relativedelta import relativedelta

from mca_model.service import helpers

ONE_DAY = relativedelta(days=1)




def test_generate_month_range():
    """"""
    
    #
    t0, t1 = dt.datetime(2022, 2, 1), dt.datetime(2040, 8, 31)
    months = helpers.generate_month_range(t0, t1) 
    assert((months[0].year==2022) and (months[0].month==2) and (months[0].day==28))
    assert((months[-1].year==2040) and (months[-1].month==8)and (months[-1].day==31))

    # 
    t0, t1 = dt.datetime(2022, 2, 5), dt.datetime(2040, 8, 28)
    _months = helpers.generate_month_range(t0, t1) 
    assert(months[0] == _months[0])
    assert(months[-1] == _months[-1])


def test_month_frac():

    f = lambda a,b,incl:pytest.approx(helpers.monthfrac(a, b, incl), rel=1e-5)

    assert(f(dt.date(2000,1,1), dt.date(2000,1,1), True) == 1/31)
    assert(f(dt.date(2000,1,1), dt.date(2000,1,1), False) == 0)
    assert(f(dt.date(2000,1,1), dt.date(2000,1,31), True) == 1)
    assert(f(dt.date(2000,1,1), dt.date(2000,1,31), False) == 30/31)

    # skip first argument
    assert(pytest.approx(helpers.monthfrac(dt.date(2000,1,2), included=True)) == 2/31)
    assert(pytest.approx(helpers.monthfrac(dt.date(2000,1,2), included=False)) == 1/31)
    with pytest.raises(Exception):
        assert(helpers.monthfrac(dt.date(2000,1,2), True) == 1/31)

    with pytest.raises(AssertionError):
        helpers.monthfrac( dt.date(1000,1,1), dt.date(2000,2,1), True)

    with pytest.raises(AssertionError):
        helpers.monthfrac(dt.date(2000,1,1), dt.date(1999,1,1), True)

  
def test_days_in_range_per_month():

    t0 = dt.datetime(2022, 2, 1)
    t1 = dt.datetime(2040, 8, 31)
    months = helpers.generate_month_range(t0, t1)

    # -- test full
    days = helpers.days_in_range_per_month(months, t0, t1, debug=True)
    assert( days.min()==1)
    assert( days.index[0].date() == dt.date(2022, 2, 28))
    assert( days.index[-1].date() == dt.date(2040, 8, 31) )

    # -- test full with different days
    _t0 = t0.replace(day=13)
    _t1 = t1.replace(day=24)
    days = helpers.days_in_range_per_month(months, _t0, _t1, debug=True)
    assert( days.index[0].date() == dt.date(2022, 2, 28))
    assert( days.index[-1].date() == dt.date(2040, 8, 31) )
    assert( days.min()>0 and days.max()==1)
    assert( pytest.approx(days.iloc[0], rel=1e-6)==(28-13+1)/28 )
    assert( pytest.approx(days.iloc[-1], rel=1e-6)==24/31 )

    # -- test first month
    days = helpers.days_in_range_per_month(months, t0.replace(day=1), t0.replace(day=28))
    assert(days.iloc[0]==1)
    assert(days.iloc[1]==0)

    
    # -- test short second month - half
    days = helpers.days_in_range_per_month(months, t0.replace(day=1), t0.replace(day=15, month=3))

    assert(pytest.approx(days.iloc[0], abs=0.001)==1)
    assert(pytest.approx(days.iloc[1], abs=0.001)==15/31)
    assert(days.iloc[2:].max()==0)

    
    # -- test months - interval
    days = helpers.days_in_range_per_month(months, t0.replace(day=1,month=4), t1.replace(year=2022, month=6, day=30))
    assert(pytest.approx(days.iloc[:2].max(), abs=0.001)==0)
    assert(pytest.approx(days.iloc[2:5].min(), abs=0.001)==1)
    assert(pytest.approx(days.iloc[5:].max(), abs=0.001)==0)

    # -- test months - larger -> keep to months
    days = helpers.days_in_range_per_month(months, t0.replace(year=2020), t1.replace(year=2100))
    assert(pytest.approx(days.min(), abs=0.001)==1.0)
    assert(days.index.size == months.size)

    # -- test - last day of month is included
    a = dt.datetime(2030, 2, 1)
    b = dt.datetime(2030, 8, 31)
    days = helpers.days_in_range_per_month(months, a, b)

    assert(days.index[96].date() == dt.date(2030,2,28)) #first day
    assert(all(days.iloc[95:97].values == [0,1]))

    assert(days.index[102].date() == dt.date(2030,8,31)) #last day
    assert(all(days.iloc[102:104].values == [1,0]))

    # -- test - first day of month is included
    a = dt.datetime(2030, 2, 1)
    b = dt.datetime(2030, 9, 1)
    days = helpers.days_in_range_per_month(months, a, b)

    assert(days.index[103].date() == dt.date(2030,9,30)) #last day
    assert(all(days.iloc[102:105].values == [1,1/30,0]))


def test_yearfrac():


    t, target = dt.date(1981,6,14), (31+28+31+30+31+13)/365
    assert( pytest.approx( helpers.yearfrac(t), abs=0.001)==target)
    
    t, target = dt.date(1981,1,1), 0
    assert( pytest.approx( helpers.yearfrac(t), abs=0.001)==target)

    t, target = dt.date(1981,1,2), 1/365  # = 0.00273
    assert( pytest.approx( helpers.yearfrac(t), abs=0.001)==target)

    t, target = dt.date(1981,12,31), 364/365
    assert( pytest.approx( helpers.yearfrac(t), abs=0.001)==target)

    # leap year
    t, target = dt.date(1980,6,14), (31+29+31+30+31+13)/366
    assert( pytest.approx( helpers.yearfrac(t), abs=0.001)==target)

    

def test_convert_rate_yearly_to_monthly():

    
    t = pd.date_range(dt.date(2000,1,1), dt.date(2010,12,31), freq='ME')
    yearly_rate = 0.98
    monthly_rate = 0.98**(1/12) 
    found = helpers._apply_monthly_rate(t, monthly_rate) 

    my = dt.date(2000,1,31)
    assert( pytest.approx(found.loc[my:my], rel=1e-6)==1)
    my = dt.date(2001,1,31)
    assert( pytest.approx(found.loc[my:my], rel=1e-6)==yearly_rate)
    my = dt.date(2010,1,31)
    assert( pytest.approx(found.loc[my:my], rel=1e-6)==yearly_rate**10)

    my = dt.date(2008,6,30)
    assert( found.loc[my:my].values < yearly_rate**8)
    assert( found.loc[my:my].values > yearly_rate**9)

    
def test_apply_yearly_rate0():

    T0 = dt.date(2000,1,1)
    T1 = dt.date(2010,12,31)
    t = pd.date_range(T0, T1, freq='ME')

    start = dt.date(2002, 5, 14)  # included
    found = helpers.apply_yearly_rate(t, start, 0.1)

    target = 0.1**(1/12*(31-14+1)/31)
    first_incomplete_month = found.loc[dt.date(2002,5,1):dt.date(2002,6,1)].values
    assert(len(first_incomplete_month)==1)
    assert( pytest.approx(first_incomplete_month[0], rel=1e-6) == target )

    # second value, first full month
    first_complete_month = found.loc[dt.date(2002,6,1):dt.date(2002,7,1)].values
    assert( pytest.approx(first_complete_month[0], rel=1e-6) == first_incomplete_month*0.1**(1/12) )

    # end
    n_years = 8+7/12
    assert( pytest.approx(found.iloc[-1], rel=1e-6) == target*(0.1**n_years))
    assert((found>0).all())
    assert((found<=1).all())

    # all variations are negatives
    var = found.diff().loc[start:]
    assert(all(var<0))
    

def test_apply_yearly_rate1():

    T0 = dt.date(2000,1,1)
    T1 = dt.date(2010,12,31)
    t = pd.date_range(T0, T1, freq='ME')

    start = dt.date(2002, 5, 1)
    found = helpers.apply_yearly_rate(t, start, 0.1)

    # test
    target = 0.1**(1/12)  # month is complete
    first_month = found.loc[dt.date(2002,5,1):dt.date(2002,6,1)].values
    assert( pytest.approx(first_month[0], rel=1e-6) == target )


def test_split_on_cumsum_threshold():
    
    
    t = pd.date_range(dt.date(1999,1,1), dt.date(2002,12,31), freq='ME')
    s = pd.Series(1, index=t)

    f = lambda df,x:df[df.index.year==x].values
        
    found = helpers.multiply_based_on_cumsum_threshold(s, threshold=6, factor_before=1, factor_above=0)

    assert(all(f(found, 1999) == [1,1,1,1,1,1,0,0,0,0,0,0]))
    assert(all(f(found, 2000) == [1,1,1,1,1,1,0,0,0,0,0,0]))
    assert(all(f(found, 2002) == [1,1,1,1,1,1,0,0,0,0,0,0]))

    found = helpers.multiply_based_on_cumsum_threshold(s, threshold=10, factor_before=0, factor_above=1)

    assert(all(f(found, 1999) == [0,0,0,0,0,0,0,0,0,0,1,1]))
    assert(all(f(found, 2000) == [0,0,0,0,0,0,0,0,0,0,1,1]))
    assert(all(f(found, 2002) == [0,0,0,0,0,0,0,0,0,0,1,1]))


    found = helpers.multiply_based_on_cumsum_threshold(s, threshold=10, factor_before=2, factor_above=3)
    assert(all(f(found, 1999) == [2,2,2,2,2,2,2,2,2,2,3,3]))

    found = helpers.multiply_based_on_cumsum_threshold(s, threshold=10.1, factor_before=2, factor_above=3)

    assert( all(found[found.index.year==2000].iloc[:10] == [2,2,2,2,2,2,2,2,2,2]))
    assert( pytest.approx(found[found.index.year==2000].iloc[10]) == 2*3/30+3*27/30)
    assert( all(found[found.index.year==2000].iloc[11:] == [3]))


    for r in np.random.rand(10):
        found = helpers.multiply_based_on_cumsum_threshold(s, threshold=2+r, factor_before=2, factor_above=2)

        for _,g in found.groupby(found.index.year):
            assert( pytest.approx(g.values, abs=1e-6) == [2]*12)
