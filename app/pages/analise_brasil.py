import streamlit as st
from datetime import date
from utils.functions import *
from utils.biomas import *
from utils.brasil import *
from components.header import header
from components.warnings import choose_ano_i_warning

years = get_years()

header()

#todo: Add mensagem informando que o mês é o mês corrente e ainda não tem valores completos para comparação
    # se for o ano atual e o mês atual, mostrar uma mensagem

#todo: Add opção "Todos os meses"
    # Quando essa opção for selecionada, exibir gráficos de todas as opções

#todo: (APLICAR PARA ESTADOS E REGIÕES) converter média histórica e desvio histório nas tabela_bioma para inteiro

st.header('Analisador de focos no Brasil')
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

    if st.button('Gerar relatório'):
        st.session_state["gerar_relatorio_brasil"] = True

if st.session_state.get("gerar_relatorio_brasil"):
    if not ano_f:
        choose_ano_i_warning()
    st.subheader(f'📊 Relatório de {ano}')
    cols = st.columns([4, 5])

    with st.spinner('Gerando relatório...'):
            df_focos = ajusta_serie_temporal(preparar_focos('paises/brasil.csv'))
            df_focos = df_focos[df_focos.index.year <=  date.today().year].copy()

            df_focos_var, stats = calcula_z_index(df_focos, ano_i, ano_f)
            df_focos_var = df_focos_var.drop(columns=['mean', 'mes', 'std'])

            df_anual, media_anual, desvio_anual = calcula_z_anual(df_focos, ano_i, ano_f)
            df_anual_plot = df_anual

            tabela = tabela_relatorio(df_focos_var, stats, ano)
            df_brasil = pd.DataFrame(tabela)

            df_brasil[['Média histórica','Desvio histórico']] = (
                df_brasil[['Média histórica','Desvio histórico']]
                .round(0)
                .astype('Int64')
            )

            num_cols = df_brasil.select_dtypes(include='number').columns

            df_brasil_style = (
                df_brasil
                .style
                .apply(cor_linha, axis=1, ano=ano)
                .format({col: formato_br for col in num_cols})
            )
            st.dataframe(df_brasil_style)

            with st.container(border=True):
                plot_annual_graph(df_anual_plot, media_anual, desvio_anual, ano_i, ano_f)