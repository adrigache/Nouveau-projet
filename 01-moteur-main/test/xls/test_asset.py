import pytest
import datetime as dt

    
def test_read_asset(model_xls):
    my = model_xls['vehicle']

    asset = my['SPV_1']['assets']['Actif_1']
    asset['installed_capacity'] == (159.705, 'kWc')
    asset = my['SPV_3']['assets']['Actif_4']
    asset['installed_capacity'] == (31.05, 'kWc')


    opex = my['SPV_1']['assets']['Actif_1']['OPEX']
    assert(len(opex)==2)
    assert(opex[0]['name'] == 'OPEX €/MWh (period 1)')
    assert(opex[0]['index_xls'] == 1)
    assert(pytest.approx(opex[0]['price'][0], abs=0.01) == 1)
    

    assert(opex[1]['name'] == 'OPEX k€ /Year')
    assert(opex[1]['index_xls'] == 3)
    assert(opex[1]["start date"] == dt.date(2026, 3, 26))
    assert(opex[1]["end date"] == dt.date(2051,11,1))
    assert(opex[1]['inflation'] == "IPC")
    assert(pytest.approx(opex[1]['price'][0], abs=0.01) == 1.19 )
    assert(opex[1]['price'][1] == "k€/year" )

    opex = my['SPV_3']['assets']['Actif_3']['OPEX']
    assert(len(opex)==3)    
    assert(opex[0]['name'] == 'OPEX €/MWh (period 1)')
    assert(opex[0]['index_xls'] == 1)

    assert(opex[1]['name'] == 'OPEX €/MWh (period 2)')
    assert(opex[1]['index_xls'] == 2)

    assert(opex[2]['name'] == 'OPEX k€ /Year')
    assert(opex[2]['index_xls'] == 3)
    assert(opex[2]['name'] == 'OPEX k€ /Year')
    assert(opex[2]['index_xls'] == 3)
    assert(opex[2]["start date"] == dt.date(2026, 5, 31))
    assert(opex[2]["end date"] == dt.date(2052, 1,6))
    assert(opex[2]['inflation'] == "IPC")
    assert(pytest.approx(opex[2]['price'][0], abs=0.01) == 0.48 )
    assert(opex[2]['price'][1] == "k€/year" )

    opex = my['SPV_3']['assets']['Actif_4']['OPEX']
    assert(len(opex)==3)    
    assert(opex[0]['name'] == 'OPEX €/MWh (period 1)')
    assert(opex[0]['index_xls'] == 1)

    assert(opex[1]['name'] == 'OPEX €/MWh (period 2)')
    assert(opex[1]['index_xls'] == 2)

    assert(opex[2]['name'] == 'OPEX k€ /Year')
    assert(opex[2]['index_xls'] == 3)
