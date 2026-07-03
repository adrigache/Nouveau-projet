import re

from mca_model.config import ALLOW_UNITS_PRICE
# def electric_power(s):
#     assert( re.sub(r'\s', '', unit1) == '€/MWh')


def price_of_electricity(s):
    assert( re.sub(r'\s', '', s) == '€/MWh')

    
def price(s):
    assert( re.sub(r'\s', '', s) in  ALLOW_UNITS_PRICE)
