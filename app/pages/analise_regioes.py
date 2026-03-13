import streamlit as st
from utils.regioes import *
from utils.brasil import *
from datetime import date
from components.header import header
from components.warnings import choose_ano_i_warning

years = get_years()

lista_regioes = ["matopiba", "map", "amazonia_legal", "norte", "nordeste", "centro_oeste", "sul", "sudeste"]

header()

st.header('Analisador de focos por Regiões')
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

    regioes_selecionadas = st.multiselect(
        label="Selecione as regiões",
        placeholder="Selecione as regiões",
        options=lista_regioes,
        format_func=lambda x: x.replace("_", " ").capitalize()
    )


    if st.button('Gerar relatório'):
        st.session_state["gerar_relatorio_regioes"] = True

if st.session_state.get("gerar_relatorio_regioes"):
    if not regioes_selecionadas:
        st.warning("Selecione pelo menos uma região.")
        st.stop()
    if not ano_f:
            choose_ano_i_warning()
    with st.spinner('Gerando relatório...'):

        resultados = []
        dados_graficos = []

        st.subheader(f'📊 Relatório de {ano}')
        tabelas_regioes = {}

        for regiao in lista_regioes:
            df_focos = ajusta_serie_temporal(preparar_focos(f'regioes/{regiao}.csv'))
            df_focos = df_focos[df_focos.index.year <= date.today().year].copy()

            res, tabela_regiao = analisador_regiao(regiao, ano, ano_i, ano_f)
            resultados.append(res)
            tabelas_regioes[regiao] = tabela_regiao

        for regiao in regioes_selecionadas:
            df_focos = ajusta_serie_temporal(preparar_focos(f'regioes/{regiao}.csv'))
            df_focos = df_focos[df_focos.index.year <= date.today().year].copy()

            df_focos_var, stats = calcula_z_index(df_focos, ano_i, ano_f)
            df_anual, media_anual, desvio_anual = calcula_z_anual(df_focos, ano_i, ano_f)
            df_anual_plot = df_anual

            tabela_regiao = tabelas_regioes[regiao]

            dados_graficos.append((regiao, df_anual_plot, media_anual, desvio_anual, tabela_regiao))

        df_regioes = pd.DataFrame(resultados)
        df_regioes[['Média histórica','Desvio histórico']] = (
            df_regioes[['Média histórica','Desvio histórico']]
            .round(0)
            .astype('Int64')
        )
        num_cols = df_regioes.select_dtypes(include='number').columns

        df_regioes_style = (
                    df_regioes
                    .style
                    .apply(cor_linha, axis=1, ano=ano)
                    .format({col: formato_br for col in num_cols})
                )
        st.dataframe(df_regioes_style)

        cols = st.columns(2)
        for i, (regiao, df_anual_plot, media_anual, desvio_anual, tabela_regiao) in enumerate(dados_graficos):
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

                st.dataframe(tabela_regiao, use_container_width=True)