import streamlit as st

from mca_model.model.model import Model


def render_asset(asset):
    """"""
    cols, i = st.columns(2), -1
    for attr, value in asset.parameters.items():
        with cols[(i:=i+1)%2]:
            if isinstance(value, list):
                text = f'`{attr}`: {value[0]} ({value[1]})'
            elif value in [None, []]:
                text = f'`{attr}`: (empty)'
            else:
                text = f'`{attr}`: {value}'
            st.markdown(text)


def render_spv(spv):
    """"""
    with st.expander(spv.name):
        tabs = st.tabs(list(spv._assets))
        for asset, tab in zip(spv.assets, tabs):
            with tab:
                render_asset(asset)


def render_holdco(holdco):
    """"""
    with st.expander(holdco.name, expanded=True):
        for spv in holdco.children:
            render_spv(spv)


def render_topco(topco):
    """"""
    with st.expander(topco.name, expanded=True):
        for holdco in topco.children:
            render_holdco(holdco)


def process(m:Model):
    render_topco(m.TopCo)
