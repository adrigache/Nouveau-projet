from pprint import pprint

from mca_model import Model, Asset





def get_price_euros_by_MWh(m:Model, a:Asset, opex:dict):
    """"""
    return 0


def get_price_euros_by_year(m:Model, a:Asset, opex:dict):
    """"""
    return 0


def get_price(m:Model, a:Asset, **kwargs):
    """entry point"""


    out = []
    for opex in a.OPEX:
        match opex['price'][1]:
            case '€/MWh':
                out.append(get_price_euros_by_MWh(m, a, opex))
            case 'k€/year':
                out.append(get_price_euros_by_year(m, a, opex))
            case _:
                raise NotImplementedError(f"unit unknown: {opex['price']['unit']}")

                           
    print(out)

    return



