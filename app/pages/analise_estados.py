import streamlit as st
from utils.estados import *
from utils.brasil import *
from datetime import date
from components.header import header
from components.warnings import choose_ano_i_warning
years = get_years()

lista_estados = [
    "acre", "alagoas", "amapa", "amazonas", "bahia", "ceara", 
    "distrito_federal", "espirito_santo", "goias", "maranhao", 
    "mato_grosso_do_sul", "mato_grosso", "minas_gerais", "para", 
    "paraiba", "parana", "pernambuco", "piaui", "rio_de_janeiro", 
    "rio_grande_do_norte", "rio_grande_do_sul", "rondonia", "roraima", 
    "santa_catarina", "sao_paulo", "sergipe", "tocantins"
]

header()

with st.container(border=True):
    st.header('Analisador de focos por Estados')

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
    estados_selecionados = st.multiselect(
            label="Selecione os estados",
            placeholder="Seleciones os estados",
            options=lista_estados,
            format_func=lambda x: x.replace("_", " ").capitalize()
        )


if st.button('Gerar relatório'):
    if not estados_selecionados:
        st.warning("Selecione pelo menos um estado.")
        st.stop()
    with st.spinner('Gerando relatório...'):

        resultados = []
        dados_graficos = []

        st.subheader("📊 Relatório")
        for estado in estados_selecionados:
            df_focos = ajusta_serie_temporal(preparar_focos(f"estados/{estado}.csv"))
            df_focos = df_focos[df_focos.index.year <= date.today().year].copy()

            df_focos_var, stats = calcula_z_index(df_focos, ano_i, ano_f)
            df_anual, media_anual, desvio_anual = calcula_z_anual(df_focos, ano_i, ano_f)
            df_anual_plot = df_anual.loc[(df_anual.index >= ano_i) & (df_anual.index <= ano_f)]

            res = analisador_estado(estado, ano, ano_i, ano_f)
            resultados.append(res)

            dados_graficos.append((estado, df_anual, media_anual, desvio_anual))

        df_estados = pd.DataFrame(resultados)
        df_estados[['Média histórica','Desvio histórico']] = (
            df_estados[['Média histórica','Desvio histórico']]
            .round(0)
            .astype('Int64')
        )
        st.dataframe(df_estados)

        cols = st.columns(2)
        for i, (estado, df_anual, media_anual, desvio_anual) in enumerate(dados_graficos):
            col = cols[i % len(cols)]
            with col, st.container(border=True), st.spinner('Gerando gráfico...'):
                plot_annual_estados_graph(
                    estado,
                    df_anual_plot,
                    media_anual,
                    desvio_anual,
                    ano_i,
                    ano_f
                )