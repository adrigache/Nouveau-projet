import pandas as pd

from functools import partial, reduce

from mca_model import Asset, Model
from mca_model.config import rc

# import QuantLib as ql


# def yearfrac(start, end):
#     """
#     Returns the period between two dates as a fraction of year
    
#     """

#     # start = ql.Date(1, 1, 2023)
#     # end = ql.Date(1, 7, 2023)
    
#     dc = ql.ActualActual()
#     return dc.yearFraction(start, end)



log_number = lambda s,i:rc.number(s.rjust(40), i, 'grey46')
log_str = lambda s, a:rc.p(f'{s.rjust(40)}\t{a}', 'grey46')
log_header = lambda a,s:rc.step(f'{a.name} | {s}')

zeros = lambda m,a:pd.Series(0, index=m.time)


def f_activation(m:Model, a:Asset) -> int:
    """"""
    return 1 if a.master_activation is True else 0
