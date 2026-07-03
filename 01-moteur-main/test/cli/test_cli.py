import pytest


from mca_model import Model
from mca_model.interface.cli import cli

from conftest import (
    FNAME_MODEL_XLS,
    FNAME_MODEL_TOML)


def test_action_tag():

    args = cli.parse_args(['tag', str(FNAME_MODEL_XLS)])
    flag, found = cli.main(args)

    assert(flag)
    assert(isinstance(found, Model))
    assert(found.TopCo is not None)
    assert(found.n_assets > 0)


    
def test_action_compute_xls():
    """"""
    args = cli.parse_args(['compute', str(FNAME_MODEL_XLS)])
    flag, (model, _, _) = cli.main(args)

    assert(flag)
    assert(isinstance(model, Model))


    
def test_action_compute_toml():
    """"""
    args = cli.parse_args(['compute', str(FNAME_MODEL_TOML)])
    flag, (model, by_assets, agg) = cli.main(args)

    assert(flag)
    assert(isinstance(model, Model))
    assert(isinstance(by_assets, dict))

    

