import streamlit as st
from utils.regioes import *
from utils.brasil import *
from datetime import date
from components.header import header

years = get_years()

lista_regioes = ["matopiba", "map", "amazonia_legal", "norte", "nordeste", "centro_oeste", "sul", "sudeste"]

header()

with st.container(border=True):
    st.header('Analisador de focos por Regiões')

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

    regioes_selecionadas = st.multiselect(
        label="Selecione as regiões",
        placeholder="Selecione as regiões",
        options=lista_regioes,
        format_func=lambda x: x.replace("_", " ").capitalize()
    )


if st.button('Gerar relatório'):
    if not regioes_selecionadas:
        st.warning("Selecione pelo menos uma região.")
        st.stop()
    with st.spinner('Gerando relatório...'):

        resultados = []
        dados_graficos = []

        st.subheader("📊 Relatório")

        for regiao in regioes_selecionadas:
            df_focos = ajusta_serie_temporal(preparar_focos(f'regioes/{regiao}.csv'))
            df_focos = df_focos[df_focos.index.year <= date.today().year].copy()

            df_focos_var, stats = calcula_z_index(df_focos, ano_i, ano_f)
            df_anual, media_anual, desvio_anual = calcula_z_anual(df_focos, ano_i, ano_f)
            df_anual_plot = df_anual.loc[(df_anual.index >= ano_i) & (df_anual.index <= ano_f)]

            res = analisador_regiao(regiao, ano, ano_i, ano_f)
            resultados.append(res)

            dados_graficos.append((regiao, df_anual, media_anual, desvio_anual))

        df_regioes = pd.DataFrame(resultados)
        df_regioes[['Média histórica','Desvio histórico']] = (
            df_regioes[['Média histórica','Desvio histórico']]
            .round(0)
            .astype('Int64')
        )
        st.dataframe(df_regioes)

        cols = st.columns(2)
        for i, (regiao, df_anual, media_anual, desvio_anual) in enumerate(dados_graficos):
            col = cols[i % len(cols)]
            with col, st.container(border=True), st.spinner('Gerando gráfico...'):
                plot_annual_regioes_graph(
                    regiao,
                    df_anual_plot,
                    media_anual,
                    desvio_anual,
                    ano_i,
                    ano_f
                )