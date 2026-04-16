import streamlit as st
from components.ui import gradient_divider, logo

def header():

    st.set_page_config(
        layout='wide',
        page_icon='🗺️',
        initial_sidebar_state="expanded"
    )

    gradient_divider()
    logo()