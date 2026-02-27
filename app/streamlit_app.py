import streamlit as st

pg = st.navigation(
    [
        st.Page('./pages/analise_brasil.py', title='Brasil'),
        st.Page('./pages/analise_biomas.py', title='Biomas'),
        st.Page('./pages/analise_estados.py', title='Estados'),
        st.Page('./pages/analise_regioes.py', title='Regiões'),
    ],
    position='top'
)

pg.run()
