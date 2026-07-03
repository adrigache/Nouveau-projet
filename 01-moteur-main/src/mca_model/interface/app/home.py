# type: ignore

import streamlit as st
import utils
from widgets import sidebar


st.set_page_config(
    page_title='Monte Cristo Advisory - moteur',
    page_icon=':material/sunny:',
    layout='wide',
    )



def page_object():
    from pages.objects import process
    return process(m)

def page_production():
    from pages.production import process
    return process(m, asset)

pages = [
    st.Page(page_object, title="Objets", icon="📦"),
    st.Page(page_production, title="Production", icon="🌞"),
]


# load
m = utils.load()
pg = st.navigation(pages)

# Show sidebar only on the Objects page
if pg == pages[1]:
    asset = sidebar.select_asset(m)
else:
    asset = None

pg.run()
