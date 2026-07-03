# type: ignore

import streamlit as st
import pandas as pd

from mca_model.config import FOR_HUMANS
from mca_model.model.model import Model
from mca_model.plumbing.nodes import Asset
from mca_model.model import revenues

from widgets.selectors import make_selector
from widgets.dates import date_selectors
import utils
import charts



f_skip_unit= lambda x:x[0] if isinstance(x,list) else x

def render_selectors(params: dict, asset_key: str):
    """"""
    # Reset state if asset changed
    if st.session_state.get("selector_asset") != asset_key:
        st.session_state.selector_asset   = asset_key
        st.session_state.selector_defaults = params.copy()
        
        for k, v in params.items():
            st.session_state[f"selector_{k}"] = f_skip_unit(v)

        
    # Reset button
    if st.button("↺ Reset", type="secondary"):
        for k, v in st.session_state.selector_defaults.items():
            st.session_state[f"selector_{k}"] =  f_skip_unit(v)
            print(k,v)

    # Render sliders with keyed session state
    return {k: make_selector(k, f_skip_unit(v)) for k, v in params.items()}



def select_values(m:Model, asset:Asset):
    """"""
    params = asset.parameters
    my = {k:v for k,v in params.items() if k not in ['type', 'typology']}        
    with st.container(height=500, border=False):
        return render_selectors(my, asset_key=asset.name)


def select_function():
    """"""
    functions = [
        revenues.electricity_production_contracted_period_in_MW
        ]

    f = lambda s:[
        name for k,v in FOR_HUMANS['functions'].items()
        if (name:=v.get(s.__name__,None))][0]
    
    return st.selectbox('choose function', functions, format_func=f, index=None)
    
def select_dates(m:Model, a:Asset):
    """"""
    dates = {
        'model': ( pd.to_datetime(m.time[0]), pd.to_datetime(m.time[-1])),
        'construction': (a.construction_start, a.construction_end),
        'operation': (a.operation_contract_start, a.operation_contract_end)}
    
    return date_selectors(dates)
    



def draw_stuff(m:Model, a:Asset, params:dict, dates:dict):
    """"""
    _model, _asset = utils.build_fake_objects(m, a, params, dates)

    func = select_function()
    st.space('small')
    if func:
        st.caption(f"calling: {func.__module__.rsplit('.',1)[1]}.{func.__name__}")
        x = func(_model)
        charts.histogram(x)
    


    
   

    
def process(m:Model, a:Asset):

    if a:

        container0 = st.container(border=True)
        tabs = st.tabs(['**dates**', '**parameters**'])
        
        with tabs[0]:
            st.markdown('##### dates')
            dates = select_dates(m, a)
        with tabs[1]:
            current = select_values(m, a)
            
        with container0:
            if dates:
                draw_stuff(m, a, current, dates )
        
        
