from __future__ import annotations

import pandas as pd
import numpy as np
import datetime as dt
from calendar import monthrange

from functools import cache
from typing import List, Callable

from pandas.tseries.offsets import MonthEnd
from dateutil.relativedelta import relativedelta

from mca_model.config import rc
from mca_model.utils import next_month


ONE_DAY = relativedelta(days=1)
ONE_YEAR = relativedelta(years=1)
MIDNIGHT = dt.time(hour=0, minute=0)


def generate_month_range(t0:dt.date, t1:dt.date):
    """"""
    t0 = dt.datetime.combine(t0, dt.time(hour=23, minute=59))
    t1 = next_month(t1)
    return pd.date_range(t0, t1, freq='ME', unit='s', normalize=False)



def yearfrac(t:dt.date) -> float:
    """fraction of year (elasped time)"""
    
    start = pd.Timestamp(t.replace(day=1, month=1))
    end = pd.Timestamp(t)

    assert(start <= end)

    days = (end-start).days
    year_days = 366 if start.is_leap_year else 365

    return days / year_days



def monthfrac(*args, **kwargs):
    """helper"""
    if len(args) == 1:
        return _monthfrac(args[0].replace(day=1), args[0], **kwargs)
    if len(args) in [2,3]:
        if not isinstance(args[1], bool):
            return _monthfrac(*args, **kwargs)

    raise Exception(f'monthfrac: wrong arguments ({args}, {kwargs})')


        
def _monthfrac(start:dt.date, end:dt.date, included:bool) -> float:
    """fraction of months (elasped time) - end date might be included"""

    assert(start.month, start.year) == (end.month, end.year)

    if start <= end:
        incl = 1 if included else 0
        days_in_month = monthrange(start.year, start.month)[1]
        return (( end-start).days + incl)/days_in_month
    
    return 0


def days_in_range_per_month(month_index: pd.DatetimeIndex, t_start:dt.date, t_end:dt.date, debug:bool=False):
    """as fraction, t_start is included but not t_end"""

    rc.debug(f'days_in_range_per_month: months range from {month_index[0]:%m/%Y} to {month_index[-1]:%m/%Y}, range: {t_start:%Y-%m-%d} to {t_end:%Y-%m-%d}', debug=debug)

    if isinstance(t_start, dt.datetime):
        t_start = t_start.date()
    if isinstance(t_end, dt.datetime):
        t_end = t_end.date()

    # fenetre vide (ex: phase merchant desactivee, fin = debut - 1 jour) => 0 partout
    if t_start > t_end:
        return pd.Series(0.0, index=month_index)

    out = []
    for m in month_index:
        month_start = (m - pd.offsets.MonthBegin(1)).date()
        month_end = (m + pd.offsets.MonthEnd(0)).date()

        t0 = max(month_start, t_start)
        t1 = min(month_end, t_end)

        frac = 0
        if t1 >= t0:
            frac = monthfrac(t0, t1, included=True)
            
        out.append(frac)
            
        
    return pd.Series(out, index=month_index)




def transform_yearly_rate_to_monthly(r, degradation:bool=False):
    if degradation:
        return transform_yearly_rate_to_monthly(r, degradation=False)
    return r**(1/12)



def _apply_monthly_rate(t:pd.DatetimeIndex, rate:float) -> pd.Series:
    """"""
    assert( isinstance(t.freq, (MonthEnd)))
    values = [ float(x) for x in rate**np.arange(t.size)]
    return pd.Series(values, index=t)



def apply_yearly_rate(t:pd.DatetimeIndex, t0:dt.date, rate:float, debug:bool=False) -> pd.Series:
    """starts on t0, included"""
    assert( isinstance(t.freq, (MonthEnd)))
    _t0 = dt.datetime.combine(t0, dt.time(0,0)) # midnight
    monthly_rate = transform_yearly_rate_to_monthly(rate)

    # nothing before t0
    out = pd.Series(index=t, dtype=float)
    mask = out.index >= _t0
    out.loc[:_t0] = 1

    # special case - first month might not be complete
    if _t0.day != 1:
        one_day_before_t0 = _t0-ONE_DAY
        frac = 1 - monthfrac(t[mask][0].replace(day=1), one_day_before_t0, included=True)
        value0 = monthly_rate**frac
    else:
        value0 = monthly_rate

    # then full months
    values = _apply_monthly_rate(out.index[mask], monthly_rate)
    out.loc[mask] = (value0*values).tolist()
    # out.loc[mask][1:]] = convert_rate_yearly_to_monthly(out.index[mask[1:]], rate)

    rc.debug(f'apply yearly rate of {rate/100:.3%} convert to monthly rate of {monthly_rate/100:.5%}', debug=debug)
    
    return out





def multiply_based_on_cumsum_threshold(s:pd.Series, threshold:float, factor_before:float, factor_above:float, debug:bool=False ):
    """"""

    def _apply_by_year(s:pd.Series):

        # on daily basis - add first point of month
        first_day_of_month = s.index[0].replace(day=1)
        assert(first_day_of_month not in s.index)

        # first_point = pd.Series([0], index=[s.index[0].replace(day=1)])
        agg = pd.concat( [ pd.Series([0], index=[first_day_of_month]), s])
        daily = agg.cumsum().resample('d').interpolate()

        #
        above = daily[daily>threshold]
        if above.empty:
            # nothing above threshold
            return s*factor_before
      
        # on that day, cumsum is above thresold
        day_cut = above.index[0] 

        # build result
        _result = pd.concat([ 
            s[s.index <  day_cut]*factor_before,
            s[s.index >= day_cut]*factor_above, ])

        _result = _result.astype(float)

        # adapt transition month if needed
        if day_cut.day > 1:
            frac = monthfrac(day_cut, included=False)
            i = [d for d in _result.index if d.month==day_cut.month][0]
            _result.loc[i] = s.loc[i]*(frac*factor_before + (1-frac)*factor_above)
        #
        return _result
    #

    assert(s.index.freq=='ME')

    out = [ _apply_by_year(g) for _,g in s.groupby(s.index.year)]
    out = pd.concat(out)
    assert s.index.equals(out.index)
    return out



from mca_model import Model

