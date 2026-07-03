from typing import List

from mca_model import Asset
from mca_model.utils import next_month


def in_MWh(results:List):
    """"""
    
    for a, df in results:

        assert(isinstance(a, Asset))
    
        before_construction = df[:a.construction_start]
        assert(before_construction.index.size==12)
        assert(before_construction.abs().max()==0)

        t0, t1 = a.construction_start, next_month(a.construction_end)
        during_construction = df[t0:t1]
        assert(during_construction.index.size==24)
        assert(during_construction.abs().max()==0)

        t2 = a.operation_contract_start
        before_operation = df[t1:t2]

        assert(before_operation.index.size==1)
        assert(before_operation.abs().max()==0)

        t3 = next_month(a.operation_contract_end)

        during_operation = df[t2:t3]
        assert(during_operation.index.size==(48-33+1)*12-1)
        assert(during_operation.abs().min()>0)

        # should be always decreasing
        # print( during_operation.values)
        assert( (during_operation.diff().iloc[2:]<=0).all())

        after_operation = df[t3:]
        assert(after_operation.index.size==24)
        assert(after_operation.abs().max()==0)

        steps = [before_construction, during_construction, before_operation, during_operation, after_operation]
        assert(df.index.size == sum([x.index.size for x in steps]))
