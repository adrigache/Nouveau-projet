import pytest
import pandas as pd
import datetime as dt

    
def test_read_market(model_xls):
    my = model_xls['market']

    assert(my['ipc_years'][-1]==2076)
    assert(all([ pytest.approx(x)==0.02 for x in my['ipc_base_rate']]))
    assert(my['ipc_percentage'] == [1, 0.2, 0.3, 0.4])
    assert(my['ipc_scenario'] == ['IPC', '20% IPC', '30% IPC', '40% IPC'])

    
