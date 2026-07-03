import streamlit as st
from mca_model.model.model import Model


def select_asset(m: Model):
    with st.sidebar:
        st.subheader("Selection")
        format_func = lambda x: x.name

        spv = st.selectbox('SPV', m.spv, format_func=format_func, index=None)

        if spv:
            if len(spv.assets) > 1:
                return st.selectbox('Asset', spv.assets, format_func=format_func, index=None)
            else:
                return spv.assets[0]
