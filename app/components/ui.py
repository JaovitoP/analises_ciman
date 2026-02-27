import streamlit as st

with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def gradient_divider():
    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

def logo():
    st.logo(image='assets/logotipo_conjugado.svg')