import pytest

import tomllib # read
import tomli_w # write

import pandas as pd
import numpy as np
import datetime as dt

from functools import partial

from conftest import FNAME_MODEL_XLS

from mca_model.repository.filesystem import xls_utils as u
from mca_model.repository.filesystem import read_xls
from mca_model.repository.filesystem import xls_dashboard
from mca_model.repository.filesystem import xls_asset


T0 = dt.date(1981, 6, 14)
T1 = dt.date(2016, 12, 16)


def test_read_xls(model_xls):
    
    # done
    dump = tomli_w.dumps(model_xls)
    tomllib.loads(dump)
    
    # print(model_xls)



    
def test_utils_walk():

    f_walk = partial(u.walk, validate=[])
    
    assert(([], None) == f_walk([], str, first=True))
    assert(('a', 0) == f_walk(['a'], str, first=True))
    assert(('a', 2) == f_walk([None, 0, 'a'], str, first=True))
    assert(('a', 1) == f_walk([None, 'a', 1, 'b'], str, first=True))
    assert(('a', 2) == f_walk([None, np.nan, 'a', 1, 'b'], str, first=True))
    assert(('b', 4) == u.walk([None, np.nan, 'a', 1, 'b'], str, validate=['b'], first=True))

    assert((42, 1) == f_walk([None, 42, 1], int, first=True))
    assert((42, 1) == f_walk([None, 42, 1], float, first=True))
    assert((42, 1) == f_walk([np.nan, 42, 1], float, first=True))
    assert(([42., 17.], 1) == f_walk([np.nan, 42, 17, 'a'], float, first=False))
    assert(([42, 17], 1) == f_walk([np.nan, 42, 17, 'a'], int, first=False))
    assert(([17], 2) == u.walk([np.nan, 42, 17, 'a'], int, validate=[16,17,28], first=False))

    assert((T0, 3) == f_walk([np.nan, None, 42, T0, T1], dt.date, first=True))
    assert(([T0,T1], 3) == f_walk([np.nan, None, 42, T0, T1], dt.date, first=False))

    assert((True, 0) == f_walk([True], bool, first=True))
    assert(([True, False], 2) == f_walk([None, -1, True, False], bool, first=False))


def test_utils_try_to_detect_type() :

    assert(None is u.try_to_detect_type([], None))
    assert(None is u.try_to_detect_type([1], None))
    assert(None is u.try_to_detect_type([1,2,3,], None))
    assert(None is u.try_to_detect_type(['int'], None))
    assert(None is u.try_to_detect_type(['int'], int))
    assert('#' == u.try_to_detect_type(['#'], int))
    assert('#' == u.try_to_detect_type(['#', None], int))
    assert('#' == u.try_to_detect_type(['#', None, None], int))
    assert('#' == u.try_to_detect_type(['#', None, None, None], int))
    assert('#' == u.try_to_detect_type(['foo', '#'], int))
    assert(None is u.try_to_detect_type(['#', 'foo'], int))
    assert(None is u.try_to_detect_type(['int', None], dt.date))
    assert('date' == u.try_to_detect_type(['date', None], dt.date))
    assert('bar' == u.try_to_detect_type(['foo', 'bar'], str))
    assert('bool' == u.try_to_detect_type(['VRAI/FAUX', None], bool))
           
    # assert('date' == u.try_to_detect_type(['date', None], dt.date))

    
def test_utils_find_value_from_line():

    f = partial(u.find_value_from_line, validate=[], debug=True)
    
    assert( ([], None) == f([], None, str,  first=False))
    assert( ([], None) == f([None], None, str,  first=False))

    assert( (1, 'list') == f([None, 'list', None, 1,2,3], 2, int,  first=True))
    assert( ([1,2,3], 'list') == f([None, 'list', np.nan, 1,2,3], 2, int,  first=False))
    assert( ([1,2,3], None) == f([None, 'list', None, None, 1,2,3], 3, int,  first=False))
    assert( ([1,3], 'list') == f([None, 'list', None,  1,'a',3], 2, int,  first=False))
    assert( ([2,3], None) == f([None, 'list', None, 'a',2, 3], 2, int,  first=False))

    assert( (['a', 'b'], 'foo') == f([None, 'foo', None, 'a', 'b'], 2, str,  first=False))
    assert( ([T0, T1], 'date') == f([None, 'date', None, T0, T1], 3, dt.date,  first=False))

        


    
def test_read_value():
    df = pd.DataFrame(
        {'a':[2, 3, '14/06/2001'], 'b':[20, 30, 40], 'c':[200, 300,400]},
        index=pd.Index(['foo','bar', 'date']))

    assert(u.get_type(df, 'foo', int, offset=0) == 2)
    with pytest.raises(Exception):
        u.get_type(df, 'not here', str, offset=0)

    assert(u.get_type(df, 'date', dt.date, offset=0) == dt.date(2001, 6, 14))


def test_read_value_output_unit():
    assert( 'kW' == u.try_to_detect_type(['kW', 2, 20, 200], int))
    assert( None is u.try_to_detect_type(['not_listed', 2, 20, 200], int))



def test_get_type_with_return_field_name():

    raw = pd.read_excel(FNAME_MODEL_XLS, 'Dashboard')
    raw = read_xls.rename_first_column(raw)

    found = xls_dashboard.load(raw, {}, return_field_name=True, return_field_name_offset=1 )

    # ecart de deux lignes
    assert(found['DASHBOARD_SENSITIVITY'][1:] ==  ('Sensitives mode', 135) )
    assert(found['DASHBOARD_SCENARIO'][1:] ==  ('Scenario', 138) )

    
