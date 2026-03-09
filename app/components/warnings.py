import streamlit as st

def choose_ano_i_warning():
    st.warning("Selecione o ano de fim. É preciso que o ano de início e de fim tenham um intervalode no mínimo 2 anos")
    st.stop()