from __future__ import annotations

from dataclasses import dataclass
import numpy as np

import datetime as dt
from typing import Callable, List, Tuple, Any

from rich.tree import Tree
from rich.text import Text

from mca_model.config import (
    rc, GREY)    


# colors
# https://rich.readthedocs.io/en/stable/appendix/colors.html#appendix-colors

class Node:
    """common class for parent/children"""
    
    debug: bool
    type: str 
    name: str
    children: List[Node]
    parent: Node | None
    
    
    def __init__(self, name:str, data:dict, debug:bool=False):
        """"""
        self.name = name
        self.children = []
        
        for k,v in data.items():
            if k not in ['type', 'assets']:
                assert(not hasattr(self, k))
                rc.debug(f'.set {k}: {v}', debug)
                setattr(self, k, v)

        rc.debug(f"Node created, class: `{self.__class__.__name__}` name: `{self.name}`", debug)

    # redefine because of __eq__
    __hash__ = object.__hash__
    
    def __eq__(self, other:Any):
        """"""
        if not isinstance(other, type(self)):
            return False

        # print(f'({self.name}, {self.__class__}) == ({self.name}, {self.__class__})')
        return (self.name, self.__class__) == (other.name, other.__class__)

        
    def clear_children(self):
        self.children = []
        # keep parent in children
        
        
    def add_child(self, child:Node):
        assert(child not in self.children)
        self.children.append(child)
        
        if child.parent != self:  # might be useless
            child.parent = self

        
    def set_parent(self, parent:Node, allow_existing:bool=False):
        """"""
        assert(allow_existing or not isinstance(self.parent, self.__class__))
        self.parent = parent
        self.parent.add_child(self)


    def count_children(self):
        return len(self.children) + np.sum([c.count_children() for c in self.children])
    
    
    def count_SPV(self):
        c = 1 if self.__class__.__name__ == 'SPV' else 0
        return c + np.sum([c.count_SPV() for c in self.children])

    
    def __str__(self):
        s = Text(f"{self.name} ")
        s.append(f"({self.__class__.__name__})", style=GREY)
        return console_to_str(s, end="")

    
    def dump(self):
        rc.p('')
        rc.header(self.type, self.name)
        for k,v in self.__dict__.items():
            if k not in ['name', 'parent']:
                if k in ['children', '_assets']:
                    rc.shift(f"{k}: {[ getattr(x, 'name', x) for x in v]}",i=3)
                else:
                    rc.shift(f'{k}: {v}',i=3)

                    
            
    def tree(self, parent:Tree|None=None) -> Tree:
        """Recursively build a Rich Tree from this node."""

        # s = f"{self.name} [{GREY}]({self.__class__.__name__})[/{GREY}]"

        my = Tree(str(self)) if parent is None else parent.add(str(self))
        for child in self.children:
            child.tree(my)
            
        return my


    
    def walk(self, acc:List[Node|None]|None=None) -> List[Node|None]:

        if acc is None:
            acc = []
        acc.append(self)
        
        for child in self.children:
            child.walk(acc)
        return acc

    
    
    def apply(self, f:Callable, *args, **kwargs):
        """apply given function to all children"""

        if isinstance(self, SPV):
            return self.apply_on_assets(f, **kwargs) 
        else:
            return [ x for c in self.children for x in c.apply(f, **kwargs)]

        
    
class TopCo(Node):
    """higher level"""
    type = 'TopCo'

        
class HoldCo(Node):
    """intermediate level"""
    type = 'HoldCo'



class SPV(Node):
    """lower level - special purpose vehicle"""
    type = 'SPV'
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initialized : bool= False
        
        self.name:str
        self.type:str 

        _, raw = args
        debug = kwargs.get('debug',False)
        if 'assets' in raw:
            self._assets = { k:Asset(k, self, v, debug=debug) for k,v in raw['assets'].items()}

            
    def __str__(self) -> str:
        s = Text(f"{self.name} ")
        s.append(f"({self.__class__.__name__})\n", style=GREY)

        for k,v in self._assets.items():
            s.append(f".{v}")
        return console_to_str(s, end="")


    def __eq__(self, other:Any):
        """test object and assets"""

        if not Node.__eq__(self, other):
            return False

        # test assets
        _assets_here = {k:v for k,v in self._assets.items() }
        _assets_other = {k:v for k,v in other._assets.items() }
        
        for k,a in _assets_here.items():
            b = _assets_other.get(k, None)
            if a != b:
                return False
            
        return True
    
    
    @property
    def assets(self):
        return list(self._assets.values())

    def apply_on_assets(self, f:Callable, **kwargs):
        m: Model = kwargs.pop('model')
        return [ (a, f(m, a, **kwargs)) for a in self.assets ]
            
    

@dataclass
class Asset():
    """"""

    type: str
    construction_start: dt.date
    construction_end: dt.date
    operation_contract_start: dt.date
    operation_contract_end: dt.date
    yield_portofolio_effect: float
    capacity_degradation_start_date: dt.date
    installed_capacity: Tuple[float,str]
    contracted_revenues_bonus_tariff: Tuple[float,str]
  
    def __init__(self, name:str, parent:SPV, d:dict, debug:bool=False):
        self.name:str = name
        self.parent: SPV = parent
        self.typology:str
        self.construction_start: dt.date
        self.construction_end: dt.date 
        self.operation_contract_start: dt.date
        self.operation_contract_end: dt.date
        
        rc.debug(f"Asset is being created: {self.name}", debug=debug)
        for k,v in d.items():
            assert(not hasattr(self, k))
            rc.debug(f'.set {k}: {v}', debug)

            # if isinstance(v, dt.datetime):
            #     v = v.date()
                
            setattr(self, k, v)
            # print(k, v, type(v))


    def dump(self):
        rc.p('')
        rc.header(self.type, self.name)
        for k,v in self.__dict__.items():
            if k not in ['name', 'parent']:
                # if k in ['children', '_assets']:
                #     rc.shift(f"{k}: {[ getattr(x, 'name', x) for x in v]}",i=3)
                # else:
                if isinstance(v, tuple):
                    rc.shift(f'{k}: {v[0]} {v[1]}',i=3)
                else:
                    rc.shift(f'{k}: {v}',i=3)


            
    # redefine because of __eq__
    __hash__ = object.__hash__
        
    def __eq__(self, other:Any):
        """test object and assets"""

        if not isinstance(other, Asset):
            return False

        print('--EQ ASSET', self.name, other.name)
        
        return all([ v == getattr(other, k, np.nan) for k,v in self.__dict__.items() if k !='parent'])

            
    def __str__(self) -> str:
        s = Text(f"{self.name} ")
        s.append(f".{self.type} | {self.typology} | {'activated' if self.master_activation else 'deactivated'} \t")
        s.append(f"{self.installed_capacity}\t")
        s.append(f"op:{self.operation_contract_start:%Y-%m-%d} → {self.operation_contract_end:%Y-%m-%d}")

        return console_to_str(s, end="")

    
    def check(self):
        assert(self.construction_start < self.construction_end)
        assert(self.operation_contract_start < self.operation_contract_end)
        assert(self.construction_end <= self.operation_contract_start)

    @property
    def parameters(self):
        """"""
        not_params = ['name','parent']
        return {k:v for k,v in self.__dict__.items() if k not in not_params}


    @property
    def estimated_electricity_production_p90(self):
        return self.installed_capacity[0]*self.yield_excl_capacity_p90/12/1000 # MWh
    @property
    def estimated_electricity_production_p50(self):
        return self.installed_capacity[0]*self.yield_excl_capacity_p50/12/1000 # MWh
    @property
    def estimated_electricity_contracted_price_bonus(self): 
        return self.contracted_revenues_ref_tariff[0] + self.contracted_revenues_bonus_tariff[0] # euros / MWh

    @property
    def estimated_revenues_from_electricity_contracted(self): 
        return \
        self.estimated_electricity_production_p90 *\
        self.estimated_electricity_contracted_price_bonus
                
from mca_model.utils import console_to_str
        
          
    
