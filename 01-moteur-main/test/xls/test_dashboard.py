import pytest
import datetime as dt



def test_read_xls_dashboard(model_xls):
    """check all types"""
    
    my = model_xls['dashboard']
    assert(my['sensitivity'] == 2)
    assert(my['scenario'] == 'lender')


    
def test_read_xls_model(model_xls):

    my = model_xls['model']
    assert(my['t_start'] == dt.date(2025,1,1))
    assert(my['t_end'] == dt.date(2062,12,30))
    assert(my['inflation_start'] == dt.date(2026,1,1))
