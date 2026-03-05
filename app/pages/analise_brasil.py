import streamlit as st
from datetime import date
from utils.functions import *
from utils.biomas import *
from utils.brasil import *
from components.header import header

years = get_years()

#to do: seleção por mês e barrar seleção de meses sem dados
#to do: barrar para sempre selecionar um ano de fim

header()

with st.container(border=True):
    st.header('Analisador de focos no Brasil')

    col1, col2, col3 = st.columns(3)

    with col1:
        ano = st.selectbox(
            label="Selecione o ano",
            options=years,
            index=len(years) -1
        )

    with col2:
        default_year = 2010
        ano_i = st.selectbox(
            label="Selecione o ano de início",
            options=years,
            index=years.index(default_year)
        )
    
    available_years = [y for y in years if y >= ano_i + 2]

    with col3:
        default_year = 2024
        ano_f = st.selectbox(
            label="Selecione o ano de fim",
            options=available_years,
            index=available_years.index(default_year) if default_year in available_years else 0
        )

    if st.button('Gerar relatório'):
        st.subheader("📊 Relatório")
        cols = st.columns([4, 5])

        with st.spinner('Gerando relatório...'):
            with cols[1], st.container(border=True):
                df_focos = ajusta_serie_temporal(preparar_focos('paises/brasil.csv'))
                df_focos = df_focos[df_focos.index.year <=  date.today().year].copy()
                df_focos_var, stats = calcula_z_index(df_focos, ano_i, ano_f)
                df_focos_var = df_focos_var.drop(columns=['mean', 'mes', 'std'])
                df_anual, media_anual, desvio_anual = calcula_z_anual(df_focos, ano_i, ano_f)
                df_anual_plot = df_anual.loc[(df_anual.index >= ano_i) & (df_anual.index <= ano_f)]
                tabela = tabela_relatorio(df_focos_var, stats, ano)
                plot_annual_graph(df_anual_plot, media_anual, desvio_anual, ano_i, ano_f)
                df_brasil = pd.DataFrame(tabela)

                df_brasil[['Média histórica','Desvio histórico']] = (
                    df_brasil[['Média histórica','Desvio histórico']]
                    .round(0)
                    .astype('Int64')
                )
            with cols[0]:
                st.dataframe(df_brasil, height=456)