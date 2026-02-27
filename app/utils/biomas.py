from utils.functions import *

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.patches as mpatches
import streamlit as st
import matplotlib.image as mpimg
from datetime import date

biomas_formatados = {
    'amazonia': 'Amazônia',
    'cerrado': 'Cerrado',
    'caatinga': 'Caatinga',
    'pantanal': 'Pantanal',
    'pampa': 'Pampa',
    'mata_atlantica': 'Mata Atlântica'
}

def analisador_bioma(bioma, ano, ano_i, ano_f):
    url_focos_bioma = f"biomas/{bioma}.csv"
    df_focos = ajusta_serie_temporal( preparar_focos(url_focos_bioma) )
    df_focos = df_focos[df_focos.index.year < date.today().year].copy() #até
    bioma_nome = biomas_formatados.get(bioma, bioma).title()
    df_anual, media_anual, desvio_anual = calcula_z_anual(df_focos, ano_i, ano_f) # ANUAL
    df_focos_mes, stats_mes = calcula_z_index(df_focos, ano_i, ano_f) #MENSAL

    # Tabela mensal
    tabela = tabela_relatorio(df_focos_mes, stats_mes, ano)
    num_cols = tabela.select_dtypes(include='number').columns
    tabela_bioma = (
        tabela
        .style
        .apply(cor_linha, axis=1, ano=ano)
        .format({col: formato_br for col in num_cols})
    )

    # --- pegar valores anuais ---
    focos_ano = df_anual.loc[ano, 'focos_ano'] if ano in df_anual.index else np.nan
    focos_anterior = df_anual.loc[ano-1, 'focos_ano'] if (ano-1) in df_anual.index else np.nan
    z_ano = df_anual.loc[ano, 'z_anual'] if ano in df_anual.index else np.nan

    # --- diferenças anuais ---
    dif_media = ((focos_ano - media_anual) / media_anual) * 100 if pd.notna(focos_ano) else np.nan
    dif_anterior = ((focos_ano - focos_anterior) / focos_anterior) * 100 if pd.notna(focos_anterior) else np.nan

    interpretacao = interpreta_z(z_ano)

    # --- montar resultado ---
    return {
        'Bioma': bioma_nome,
        f'Focos {ano}': focos_ano,
        'Média histórica': media_anual,
        'Desvio histórico': desvio_anual,
        'Dif. relativa (%)': dif_media,
        f'Z-score {ano}': z_ano,
        'Interpretação': interpretacao,
        f'Focos {ano-1}': focos_anterior,
        f'Dif. relativa (%) {ano-1}': dif_anterior
    }

def plot_annual_biomas_graph(bioma, df_anual, media_anual, desvio_anual, ano_i, ano_f):

    img = mpimg.imread('assets/LogoINPEQmdPeq.png')

    fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(12, 12), sharex=True) # Increased figure height significantly
    bioma_nome = biomas_formatados.get(bioma, bioma).title()
    df_anual.focos_ano.plot(kind="bar", ax=axes[0], color='indianred', label='Focos Anuais', title=f'Série Histórica de Focos de calor no bioma {bioma_nome} - Climatologia {ano_i} - {ano_f}')
    axes[0].set_ylabel('Número de Focos')
    axes[0].grid(True, axis='y', linestyle='--', alpha=0.6) # Updated grid for axes[0]
    axes[0].axhline(media_anual, color='black', linestyle='--', label='Média Histórica de Focos') # Add horizontal line for mean
    # Add standard deviation range - Changed color to a lighter blue
    # Using get_xlim() to ensure the fill spans the entire x-axis of the plot
    x_min, x_max = axes[0].get_xlim()
    axes[0].fill_between([x_min, x_max], media_anual - desvio_anual, media_anual + desvio_anual, color='grey', alpha=0.2, label='±1 Desvio Padrão Histórico', zorder=0) # zorder=0 to place it behind bars and grid
    axes[0].legend()

    df_anual.z_anual.plot(kind="bar", ax=axes[1], color='black', alpha=0.5, title=f'Z-Score de Focos no bioma {bioma_nome} - Climatologia {ano_i} - {ano_f}')
    axes[1].set_ylabel('Z-Score')
    axes[1].set_xlabel('Ano')
    axes[1].grid(True, axis='y', linestyle='--', alpha=0.6) # Updated grid for axes[1]
    axes[1].set_yticks([-4,-3,-2,-1,0,1,2,3,4]) # Corrected: use set_yticks directly on the axes object
    axes[1].axhspan(3, 4, facecolor='#A25353', alpha=0.7, zorder=0)
    axes[1].axhspan(2, 3, facecolor='#D0A9A9', alpha=0.7, zorder=0)
    axes[1].axhspan( 1, 2, facecolor='#E8D4D4', alpha=0.7, zorder=0)
    axes[1].axhspan(-1, 1, facecolor='#ffffff', alpha=0.7, zorder=0)
    axes[1].axhspan(-1, -2, facecolor='#C5E1D1', alpha=0.7, zorder=0)
    axes[1].axhspan(-2, -3, facecolor='#8AC2A2', alpha=0.7, zorder=0)
    axes[1].axhspan(-3, -4, facecolor='#468646', alpha=0.7, zorder=0)
    axes[1].set_ylim(-4, 4)

    # Create custom legend handles for Z-index significance
    legend_patches = [
        mpatches.Patch(color='black', alpha=0.5, label='Focos Anuais (Barras)'), # Added entry for bar color
        mpatches.Patch(color='#468646', alpha=0.7, label='Z < -3: Muito abaixo da média'),
        mpatches.Patch(color='#8AC2A2', alpha=0.7, label='-3 ≤ Z < -2: Consideravelmente abaixo da média'),
        mpatches.Patch(color='#C5E1D1', alpha=0.7, label='-2 ≤ Z < -1: Moderadamente abaixo da média'),
        mpatches.Patch(color='#ffffff', alpha=0.7, label='-1 ≤ Z ≤ +1: Próximo à média'),
        mpatches.Patch(color='#E8D4D4', alpha=0.7, label='+1 < Z ≤ +2: Moderadamente acima da média'),
        mpatches.Patch(color='#D0A9A9', alpha=0.7, label='+2 < Z ≤ +3: Consideravelmente acima da média'),
        mpatches.Patch(color='#A25353', alpha=0.7, label='Z > +3: Muito acima da média')
    ]

    # Add the custom legend to the Z-index subplot with horizontal layout
    # Adjusted bbox_to_anchor to align to the left and ensure it's inside the figure
    axes[1].legend(handles=legend_patches, loc='upper center', bbox_to_anchor=(0.5, -0.20),
                        fancybox=True, shadow=True, ncol=2, title='Significado do Z-Index') # Changed ncol to 3

    # Adicionar a logo à figura
    # Calculate position for bottom-right corner, with some padding in pixels
    # Adicionar a logo à figura
    # Calculate position for bottom-right corner, with some padding in pixels
    logo_ax = fig.add_axes([0.80, 0.01, 0.16, 0.10])
    logo_ax.imshow(img)
    logo_ax.axis('off')

    plt.tight_layout(rect=[0, 0.08, 1, 1]) # Adjust layout to make space for logo at bottom
    plt.subplots_adjust(hspace=0.25) # Adjust vertical spacing between subplots

    st.pyplot(fig)