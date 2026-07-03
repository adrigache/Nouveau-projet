from __future__ import annotations

import numpy as np
import pandas as pd
import datetime as dt
from typing import List

from rich.console import Console
from rich.text import Text
from collections.abc import Iterable


from mca_model.config import (
    rc, BLUE, GREY)    

from mca_model.plumbing.nodes import Node, TopCo, HoldCo, SPV

            
            
class Model:
    """"""
    
    scenario: str
    t_start: dt.date
    t_end: dt.date
    t_freq: str
    
    def __init__(self, d:dict, debug:bool=False):
        """"""

        if debug:
            rc.p('init model')
            
        self._objects = {}

        for name in ['dashboard', 'model', 'market']:
            if debug:
                rc.squared(name)
                
            for k,v in d[name].items():
                # key = f'{name}_{k}' if name != 'model' else k
                assert(not hasattr(self, k))
                if debug:
                    rc.debug(f'.set {k}: {v}', debug)
                setattr(self, k, v)

        #
        self.set_time()


    @property
    def n_objects(self):
        return len(self.list_objects())
    
    @property
    def spv(self):
        return self.list_objects(t='SPV')

    @property
    def n_activated_assets(self):
        return len(self.list_assets(activated=True))

    @property
    def n_assets(self):
        return len(self.list_assets())

    @property
    def TopCo(self):
        obj = [ x for x in self.list_objects('TopCo')]
        assert(len(obj)==1)
        return obj[0]


    def set_time(self):
        """"""
        from mca_model.service.helpers import generate_month_range
        
        assert(self.t_freq=='ME')
        self.time = generate_month_range(self.t_start, self.t_end)

        
    def clear_objects(self):
        self._objects = {}

                
    def add_object(self, s, obj:Node):
        assert(s not in self._objects)
        self._objects[s] = obj

        
    def get_object(self, s):
        return self._objects[s]

    
    def link_objects(self):
        for obj in self._objects.values():
            if (parent := getattr(obj, 'parent', False)):
                obj.set_parent(self._objects[parent])

        


    def list_assets(self, activated:bool|None=None):
        _assets = [ a for spv in self.spv for a in spv.assets]
        if activated is not None:
            return [a for a in _assets if a.master_activation == activated]
        return _assets

            
    def list_objects(self, t:str|None=None):
        """"""
        if t:
            target = {'TopCo':TopCo, 'HoldCo':HoldCo, 'SPV':SPV}[t]
            return [ obj for obj in self._objects.values() if isinstance(obj,target)]
            # return [ obj for obj in self._objects.values() if type(obj) == target]
        else:
            return list(self._objects.values())

            
    def compute(self, f, **kwargs):
        """apply given function on all nodes"""
        return self.TopCo.apply(f, model=self, **kwargs)
        
    
        
        
    def __str__(self):
        """nice string"""

        c = Console(record=True)

        with c.capture() as capture:
            c.print( Text('[model]', style=f'bold {BLUE}'))
            c.print( Text(f'.objects: {self.n_objects}', style=GREY))
            c.print( Text('\n[structure]', style='bold'))
            tree = self.TopCo.tree()
            c.print(tree)
            
        return capture.get()
    
    __hash__ = object.__hash__

    def __eq__(self, other:Model):
        """test equality"""

        if not isinstance(other, Model):
            return False

        objects_a = { x.name:x for x in self.list_objects()}
        objects_b = { x.name:x for x in other.list_objects()}

        a, b = set(list(objects_a.keys())), set(list(objects_b.keys()))
        if a != b:
            rc.fail(f'differences: {a.symmetric_difference(b)}')
            return False
        
        return True

        to_be_compared = [ (a, objects_b[name]) for name, a in objects_a.items()]
        for a,b in to_be_compared:
            for k, value_a in a.__dict__.items():
                value_b = getattr(b, k)
                        
                if isinstance(value_a, (str, int, bool)):
                    if value_a != value_b:
                        return False
                elif isinstance(value_a, (float)):
                    if pytest.approx(value_a, rel=1e-6) != value_b:
                        return False
                elif isinstance(value_a, Node):
                    if value_a != value_b:
                        return False
                elif isinstance(value_a, Iterable):
                    if not all([x==y for x,y in zip(value_a, value_b)]):
                        return False
                else:
                    print(f'.skipping {k}, type: {type(value_a)}')

        return True

    
    def dump(self):
        """"""

        rc.header('general', 'parameters')
        for k,v in self.__dict__.items():
            if not k.startswith('_'):
                if isinstance(v, (List, tuple)):
                    if len(v) > 10:
                        rc.shift(f'{k}: {v[:3]} ... {v[-3:]} ({len(v)} values)', 1)
                        continue
                    
                if isinstance(v, pd.DatetimeIndex):
                    rc.shift(f'{k}: {v[0]} -> {v[-1]} ({v.size} indexes)', 1)
                    continue

                rc.shift(f'{k}: {v}', 1)
        #
        
        TopCo = self.list_objects('TopCo')[0]
        TopCo.dump()

        for obj in self.list_objects('HoldCo'):
            obj.dump()
        for obj in self.list_objects('SPV'):
            obj.dump()
        for obj in self.list_assets():
            obj.dump()


        
#






