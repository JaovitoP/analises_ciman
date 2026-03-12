import streamlit as st
from components.ui import gradient_divider, logo

def header():

    st.set_page_config(
        layout='wide',
        page_icon='🗺️',
        initial_sidebar_state="expanded"
    )

    with open('style.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

    gradient_divider()
    logo()