import streamlit as st
from utils.biomas import *
from utils.brasil import *
from datetime import date
from components.header import header
from components.warnings import choose_ano_i_warning

years = get_years()
lista_biomas = ["amazonia", "cerrado", "pantanal", "caatinga", "mata_atlantica","pampa"]

header()

st.header('Analisador de focos por Biomas')
with st.sidebar:

    ano = st.selectbox(
        label="Selecione o ano",
        options=years,
        index=len(years) -1
    )
    default_year = 2010
    ano_i = st.selectbox(
        label="Selecione o ano de início",
        options=years,
        index=years.index(default_year)
    )
    
    available_years = [y for y in years if y >= ano_i + 2]

    default_year = 2024
    ano_f = st.selectbox(
        label="Selecione o ano de fim",
        options=available_years,
        index=available_years.index(default_year) if default_year in available_years else 0
    )

    biomas_selecionados = st.multiselect(
        label="Selecione os biomas",
        placeholder="Selecione os biomas",
        options=lista_biomas,
        format_func= lambda x: x.replace("_", " ").capitalize()
    )

    if st.button('Gerar relatório'):
        st.session_state["gerar_relatorio_biomas"] = True
if st.session_state.get("gerar_relatorio_biomas"):
    if not biomas_selecionados:
        st.warning("Selecione pelo menos um bioma.")
        st.stop()
    if not ano_f:
        choose_ano_i_warning()
    with st.spinner('Gerando relatório...'):

        resultados = []
        dados_graficos = []

        st.subheader(f'📊 Relatório de {ano}')
        tabelas_biomas = {}


        # Tabela
        for bioma in lista_biomas:
            df_focos = ajusta_serie_temporal(preparar_focos(f"biomas/{bioma}.csv"))
            df_focos = df_focos[df_focos.index.year <= date.today().year].copy()

            res, tabela_bioma = analisador_bioma(bioma, ano, ano_i, ano_f)
            resultados.append(res)
            tabelas_biomas[bioma] = tabela_bioma


        # Gráficos
        for bioma in biomas_selecionados:
            df_focos = ajusta_serie_temporal(preparar_focos(f"biomas/{bioma}.csv"))
            df_focos = df_focos[df_focos.index.year <= date.today().year].copy()

            df_anual, media_anual, desvio_anual = calcula_z_anual(df_focos, ano_i, ano_f)
            df_anual_plot = df_anual

            tabela_bioma = tabelas_biomas[bioma]

            dados_graficos.append((bioma, df_anual_plot, media_anual, desvio_anual, tabela_bioma))

        df_biomas = pd.DataFrame(resultados)

        df_biomas[['Média histórica','Desvio histórico']] = (
            df_biomas[['Média histórica','Desvio histórico']]
            .round(0)
            .astype('Int64')
        )

        num_cols = df_biomas.select_dtypes(include='number').columns

        df_biomas_style = (
            df_biomas
            .style
            .apply(cor_linha, axis=1, ano=ano)
            .format({col: formato_br for col in num_cols})
        )
        st.dataframe(df_biomas_style)

        cols = st.columns(2)

        for i, (bioma, df_anual_plot, media_anual, desvio_anual, tabela_bioma) in enumerate(dados_graficos):
            col = cols[i % len(cols)]
            with col, st.container(border=True), st.spinner('Gerando gráfico...'):
                plot_annual_biomas_graph(
                    bioma,
                    df_anual_plot,
                    media_anual,
                    desvio_anual,
                    ano_i,
                    ano_f
                )

                st.dataframe(tabela_bioma, use_container_width=True)

