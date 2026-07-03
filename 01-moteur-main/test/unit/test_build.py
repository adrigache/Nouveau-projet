import pytest
import datetime as dt



def test_build_model(model):

    assert(model.scenario == 'lender')
    assert(model.t_start == dt.date(2025,1,1))
    assert(model.t_end == dt.date(2062,12,30))

    assert(len(model.list_objects())==6)
    assert(len(model.list_objects('HoldCo'))==2)
    assert(len(model.list_objects('SPV'))==3)

    with pytest.raises(KeyError):
        model.list_objects('do not exist')


    

def test_model_time(model):

    found = model.time
    assert(found[0].date() == dt.date(2025,1,31))
    assert(found[-1].date() == dt.date(2062,12,31))

    assert((found[0].hour==23) and (found[0].minute==59))
    assert((found[-1].hour==23) and (found[-1].minute==59))
    
    
