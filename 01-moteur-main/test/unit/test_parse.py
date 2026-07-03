import re
from mca_model.service import parse


def functest(x):
    f = lambda x:x
    g = lambda x:x
    h = lambda x:x
    
    return h(x)*(g(x)+f(x))

def functest_zero():
    return 0

def functest_none():
    return None

def functest_dummy():
    a = 1
    a += 1
    return "foo"


def test_parse():
    
    found = parse.function_calls_and_expr(functest)
    assert(found['functions called'] == set(['f', 'g', 'h']))
    assert( re.sub(r'\s+', '', found['expression']) == "h(x)*(g(x)+f(x))")
    
    found = parse.function_calls_and_expr(functest_none)
    assert(found['functions called'] == set([]))
    assert( found['expression'] == "None")

    found = parse.function_calls_and_expr(functest_zero)
    assert(found['functions called'] == set([]))
    assert( found['expression'] == "0")

    
    found = parse.function_calls_and_expr(functest_dummy)
    assert(found['functions called'] == set([]))
    assert( found['expression'] == "'foo'")
