import datetime as dt
from pprint import pprint
import copy
from numbers import Number

from mca_model import utils, Asset, HoldCo, TopCo, SPV
from mca_model.plumbing import build

from conftest import FNAME_MODEL_TOML


# def modify_object(objects, object_name:str, field_name:str, value:str|Number):
#     """"""
#     # print('.. calling', objects)

#     if isinstance(objects, dict):
#         _new = {}
#         for k, obj in objects.items():
#             if k == object_name:
#                 print(f'found ! {object_name}.{field_name} set to {value}')
#                 obj = copy.deepcopy(obj)
#                 setattr(obj, field_name, value)
            
#             elif isinstance(obj, (HoldCo, TopCo)):
#                 obj.children = modify_object(obj.children, object_name, field_name, value)
           
#             _new[k] = obj
            
#     elif isinstance(objects, list):
#         _new = []
#         for obj in objects:
#             if obj.name == object_name:
#                 print(f'found ! {object_name}.{field_name} set to {value}')
#                 obj = copy.deepcopy(obj)
#                 setattr( obj, field_name, value)
            
#             elif isinstance(obj, (HoldCo, TopCo)):
#                 obj.children = modify_object(obj.children, object_name, field_name, value)
#             elif isinstance(obj, (SPV)):
#                 obj._assets = modify_object(obj._assets, object_name, field_name, value )
            
#             _new.append(obj)
#     else:
#         raise Exception(f'what are you? {type(objects)}')
       
#     return _new


def test_next_month():
    assert(utils.next_month(dt.date(2000,1,1)) == dt.date(2000,2,1))
    assert(utils.next_month(dt.date(2000,1,31)) == dt.date(2000,2,1))

    
def test_model_equals():

    original = build.load(FNAME_MODEL_TOML, debug=False)
    another = build.load(FNAME_MODEL_TOML, debug=False)
    assert(original == another)

    different = copy.deepcopy(original)
    different.TopCo.name = 'another name'
    assert(original != different)

    # different = copy.copy(original)
    # different._objects = modify_object(different._objects, 'Actif_1', 'name', 'wrong name')

    # print(original)
    # print(different)

    # _attr = 'yield_portofolio_effect'
    # for k,v in different._objects.items():
    #     if isinstance(v, SPV):
    #         for ka, a in v._assets.items():
    #             if ka == 'Actif_2':
    #                 setattr(a, _attr, 1.01*getattr(a, _attr))
    #                 print('changed')
    
    # assert(original != different)

