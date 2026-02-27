#bibliotecas
import pandas as pd
import matplotlib.image as mpimg
import urllib.request
import os # Import os module to handle file cleanup
import pandas as pd
import numpy as np
import matplotlib.patches as mpatches

url_base = 'https://data.inpe.br/queimadas/portal/csv/download/historico-mensal/'

def preparar_focos(link):
  # Faz a leitura do arquivo CSV direto da URL
  df_focos = pd.read_csv(url_base+link)

  # Eliminar as 3 ultimas linhas
  df_focos = df_focos.iloc[:-3, :-1].copy()

  # converter o dataframe para tres colunas utilizando o melt
  df_focos = df_focos.melt(id_vars=["Ano"], var_name="mes", value_name="focos")
  df_focos.columns = df_focos.columns.str.lower()

  return df_focos

def ajusta_serie_temporal(df_focos):
  # Mapear os nomes dos meses em português para números
  dic_mes = {
      'Janeiro': '01', 'Fevereiro': '02', 'Março': '03', 'Abril': '04',
      'Maio': '05', 'Junho': '06', 'Julho': '07', 'Agosto': '08',
      'Setembro': '09', 'Outubro': '10', 'Novembro': '11', 'Dezembro': '12'
  }

  df_focos['mes_num'] = df_focos['mes'].map(dic_mes)

  # Combinar 'ano' e 'mes_num' para criar a coluna de data no formato YYYY-MM
  df_focos['data_str'] = df_focos['ano'].astype(str) + '-' + df_focos['mes_num']

  # Ordena pela data_str
  df_focos = df_focos.sort_values(by="data_str")

  # Criar o PeriodIndex e definir como índice do DataFrame
  df_focos = df_focos.set_index(pd.PeriodIndex(df_focos['data_str'], freq='M'))

  # Filtro Temporal
  df_focos = df_focos[df_focos.index >= '1998-06']

  # Remover as colunas auxiliares
  df_focos = df_focos.drop(columns=['ano', 'mes', 'mes_num', 'data_str'])

  return df_focos


def tabela_relatorio(df_focos_var, stats, ano):

    df = df_focos_var.copy()

    # extrair mês e ano do PeriodIndex
    df['mes'] = df.index.month
    df['ano'] = df.index.year

    # dados do ano atual
    atual = df[df['ano'] == ano].set_index('mes')

    # dados do ano anterior
    anterior = df[df['ano'] == (ano - 1)].set_index('mes')

    # base com todos os meses
    df_tab = pd.DataFrame(index=range(1, 13))

    # adicionar dados
    df_tab[f'Focos {ano}'] = atual['focos']
    df_tab[f'Z-score {ano}'] = atual['z_index']
    df_tab[f'Focos {ano-1}'] = anterior['focos']

    # adicionar stats (mean e std já por mês)
    df_tab['Média histórica'] = stats['mean']
    df_tab['Desvio histórico'] = stats['std']

    # diferença relativa vs média
    df_tab['Dif. relativa (%)'] = (
        (df_tab[f'Focos {ano}'] - df_tab['Média histórica'])
        / df_tab['Média histórica']
    ) * 100

    # diferença relativa vs ano anterior
    df_tab[f'Dif. relativa (%) {ano-1}'] = (
        (df_tab[f'Focos {ano}'] - df_tab[f'Focos {ano-1}'])
        / df_tab[f'Focos {ano-1}']
    ) * 100

    # nomes dos meses
    meses_nome = [
        'Janeiro','Fevereiro','Março','Abril','Maio','Junho',
        'Julho','Agosto','Setembro','Outubro','Novembro','Dezembro'
    ]
    df_tab['Mês'] = meses_nome

    df_tab['Interpretação do Z-score'] = df_tab[f'Z-score {ano}'].apply(interpreta_z)

    # organizar colunas
    df_tab = df_tab[[
        'Mês',
        f'Focos {ano}',
        'Média histórica',
        'Desvio histórico',
        'Dif. relativa (%)',
        f'Z-score {ano}',
        'Interpretação do Z-score',
        f'Focos {ano-1}',
        f'Dif. relativa (%) {ano-1}'
    ]]

    return df_tab


def interpreta_z(z):
    if pd.isna(z):
        return 'Sem dados'
    elif z < -3:
        return 'Muito abaixo da média'
    elif -3 <= z < -2:
        return 'Consideravelmente abaixo da média'
    elif -2 <= z < -1:
        return 'Moderadamente abaixo da média'
    elif -1 <= z <= 1:
        return 'Próximo à média'
    elif 1 < z <= 2:
        return 'Moderadamente acima da média'
    elif 2 < z <= 3:
        return 'Consideravelmente acima da média'
    else:
        return 'Muito acima da média'
    
def cor_z(z):
    if pd.isna(z):
        return ''
    elif z < -3:
        return 'background-color: #468646'
    elif -3 <= z < -2:
        return 'background-color: #8AC2A2'
    elif -2 <= z < -1:
        return 'background-color: #C5E1D1'
    elif -1 <= z <= 1:
        return 'background-color: #FEFEFE'
    elif 1 < z <= 2:
        return 'background-color: #E8D4D4'
    elif 2 < z <= 3:
        return 'background-color: #D0A9A9'
    else:
        return 'background-color: #A25353'
    
def cor_linha(row, ano):
    cor = cor_z(row[f'Z-score {ano}'])
    return [cor] * len(row)

def formato_br(x):
    if pd.isna(x):
        return ""
    if isinstance(x, int) or float(x).is_integer():
        return f"{int(x):,}".replace(",", ".")
    return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def calcula_z_index(df_focos, ano_inicio, ano_fim):

    df = df_focos.copy()

    # garantir coluna de mês
    df['mes'] = df.index.month

    # 🔹 definir período histórico
    df_hist = df[(df.index.year >= ano_inicio) & (df.index.year <= ano_fim)]

    # 🔹 calcular média e desvio por mês (baseline)
    stats = df_hist.groupby('mes')['focos'].agg(['mean', 'std'])

    # 🔹 juntar com a série completa
    df = df.join(stats, on='mes')

    # 🔹 calcular z-score para TODOS os anos
    df['z_index'] = (df['focos'] - df['mean']) / df['std']

    return df, stats

def calcula_z_anual(df_focos, ano_inicio, ano_fim):
    """
    df_focos: DataFrame com índice datetime/PeriodIndex e coluna 'focos'
    """

    df = df_focos.copy()

    # garantir ano
    anos = df.index.year

    # 1. somar focos por ano (toda a série)
    anual = df.groupby(anos)['focos'].sum().to_frame(name='focos_ano')

    # 2. definir baseline histórico
    hist = anual.loc[(anual.index >= ano_inicio) & (anual.index <= ano_fim)]

    # 3. média e desvio do histórico
    media_anual = hist['focos_ano'].mean()
    desvio_anual = hist['focos_ano'].std()

    # 4. calcular z-score para todos os anos
    anual['z_anual'] = (anual['focos_ano'] - media_anual) / desvio_anual

    return anual, media_anual, desvio_anual
