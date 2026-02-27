import streamlit as st
from datetime import date
from utils.functions import *
from utils.biomas import *

from utils.brasil import *
from components.ui import gradient_divider, logo


st.set_page_config(
    layout='wide',
    page_icon='🗺️'
)

years = [year for year in range(1998, 2026)]

with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

logo_col, menu_col = st.columns([1, 3])

gradient_divider()
logo()

with st.container(border=True):
    st.header('Analisador de focos no Brasil')

    col1, col2, col3 = st.columns(3)

    with col1:
        ano = st.selectbox(
            label="Selecione o ano",
            options=years,
        )

    with col2:
        ano_i = st.selectbox(
            label="Selecione o ano de início",
            options=years
        )
    
    available_years = [y for y in years if y >= ano_i + 2]

    with col3:
        ano_f = st.selectbox(
            label="Selecione o ano de fim",
            options=available_years,
        )

    if st.button('Gerar relatório'):
        st.subheader("📊 Relatório")
        cols = st.columns([4, 5])

        with cols[0], st.container(border=True), st.spinner('Gerando relatório...'):
            df_focos = ajusta_serie_temporal( preparar_focos('paises/brasil.csv') )
            df_focos = df_focos[df_focos.index.year <  date.today().year].copy() #até ano anterior
            df_focos_var, stats = calcula_z_index(df_focos, ano_i, ano_f) #Definir qual o período da climatologia
            df_focos_var = df_focos_var.drop(columns=['mean', 'mes', 'std'])
            df_anual, media_anual, desvio_anual = calcula_z_anual(df_focos, ano_i, ano_f)
            tabela = tabela_relatorio(df_focos_var, stats, ano)
            plot_annual_graph(df_anual, media_anual, desvio_anual, ano_i, ano_f)
            df_brasil = pd.DataFrame(tabela)

            df_brasil[['Média histórica','Desvio histórico']] = (
                df_brasil[['Média histórica','Desvio histórico']]
                .round(0)
                .astype('Int64')
            )
        with cols[1]:
            st.dataframe(df_brasil, height=456)

