import streamlit as st

def gradient_divider():
    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

def logo():
    st.logo(image='assets/logotipo_conjugado.svg')