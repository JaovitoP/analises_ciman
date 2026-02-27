import streamlit as st
from utils.biomas import *
from utils.brasil import *
from datetime import date
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
    st.header('Analisador de focos por Biomas')

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
            options=available_years
        )

    if st.button('Gerar relatório'):
        with st.spinner('Gerando relatório...'):

            lista_biomas = ["amazonia", "cerrado", "pantanal", "caatinga", "mata_atlantica","pampa"]
            resultados = []

            st.subheader("📊 Relatório")

            cols = st.columns(2)

            for i, bioma in enumerate(lista_biomas):
                col = cols[i % len(cols)] 
                with col, st.container(border=True), st.spinner('Gerando gráfico...'):
                    df_focos = ajusta_serie_temporal(preparar_focos(f"biomas/{bioma}.csv"))
                    df_focos = df_focos[df_focos.index.year < date.today().year].copy()  # até o ano anterior
                    df_focos_var, stats = calcula_z_index(df_focos, ano_i, ano_f)  # Período da climatologia
                    df_focos_var = df_focos_var.drop(columns=['mean', 'mes', 'std'])
                    df_anual, media_anual, desvio_anual = calcula_z_anual(df_focos, ano_i, ano_f)
                    res = analisador_bioma(bioma, ano, ano_i, ano_f)
                    resultados.append(res)
                    plot_annual_biomas_graph(bioma, df_anual, media_anual, desvio_anual, ano_i, ano_f)

            df_biomas = pd.DataFrame(resultados)

            df_biomas[['Média histórica','Desvio histórico']] = (
                df_biomas[['Média histórica','Desvio histórico']]
                .round(0)
                .astype('Int64')
            )
            st.dataframe(df_biomas)

