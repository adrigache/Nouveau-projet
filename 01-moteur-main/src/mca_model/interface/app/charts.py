import streamlit as st
import altair as alt

from typing import List


def histogram(results:List):
    """"""
    assert(len(results) == 1)
    asset, s = results[0]
    
    margin = 0.25
    y_min = (1-margin)*s.min() if s.min()>0 else (1+margin)*s.min() 
    y_max = (1+margin)*s.max() if s.max()>0 else (1-margin)*s.max() 

    my = s.reset_index()
    names = my.columns
    my.rename(columns={names[0]:'date'}, inplace=True)

    chart = alt.Chart(my, title=names[1]).mark_point(size=8).encode(
        x=alt.X('date'),
        y=alt.Y(names[1], title=None, scale=alt.Scale(domain=[y_min, y_max]))
    )
    
    st.altair_chart(chart, width='stretch')
