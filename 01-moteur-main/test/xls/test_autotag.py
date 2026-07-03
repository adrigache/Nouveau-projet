import pytest
from pathlib import Path
from pprint import pprint

from mca_model.service import actions

from conftest import FNAME_MODEL_BASIC_XLS


def test_full(fname:Path=FNAME_MODEL_BASIC_XLS):
    """"""

    my = actions.tag(fname)
    print(my)
   
