from io import BytesIO
from pathlib import Path
import tempfile
from urllib.request import urlopen

import pandas as pd


URL_BASE = "https://data.inpe.br/queimadas/portal/csv/download/historico-mensal/"

ESTADOS = (
    "acre", "alagoas", "amapa", "amazonas", "bahia", "ceara",
    "distrito_federal", "espirito_santo", "goias", "maranhao",
    "mato_grosso", "mato_grosso_do_sul", "minas_gerais", "para",
    "paraiba", "parana", "pernambuco", "piaui", "rio_de_janeiro",
    "rio_grande_do_norte", "rio_grande_do_sul", "rondonia", "roraima",
    "santa_catarina", "sao_paulo", "sergipe", "tocantins",
)

BIOMAS = (
    "amazonia", "cerrado", "pantanal", "caatinga", "mata_atlantica", "pampa",
)

REGIOES = (
    "matopiba", "map", "amazonia_legal", "norte", "nordeste",
    "centro_oeste", "sul", "sudeste",
)

DATASETS = (
    "paises/brasil.csv",
    *(f"biomas/{bioma}.csv" for bioma in BIOMAS),
    *(f"estados/{estado}.csv" for estado in ESTADOS),
    *(
        f"{'regioes_especiais' if regiao in {'matopiba', 'map', 'amazonia_legal'} else 'regioes'}/{regiao}.csv"
        for regiao in REGIOES
    ),
)

DATA_DIRECTORY = Path(__file__).resolve().parents[1] / "data" / "processed"

MONTHS = {
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
}


def processed_data_path(dataset: str) -> Path:
    if dataset not in DATASETS:
        raise ValueError(f"Dataset não reconhecido: {dataset}")
    return DATA_DIRECTORY / dataset


def process_source_csv(content: bytes) -> pd.DataFrame:
    source = pd.read_csv(BytesIO(content))
    if source.shape[0] <= 3 or source.shape[1] <= 1 or "Ano" not in source.columns:
        raise ValueError("O CSV recebido não possui o formato histórico esperado.")

    processed = source.iloc[:-3, :-1].melt(
        id_vars=["Ano"], var_name="mes", value_name="focos"
    )
    processed = processed.rename(columns={"Ano": "ano"})
    processed["ano"] = pd.to_numeric(processed["ano"], errors="raise")
    processed["focos"] = pd.to_numeric(processed["focos"], errors="coerce")

    if processed.empty or not set(processed["mes"].dropna()).issubset(MONTHS):
        raise ValueError("O CSV recebido possui meses inválidos ou não contém dados.")

    return processed


def update_datasets() -> None:
    DATA_DIRECTORY.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix=".update-", dir=DATA_DIRECTORY) as temporary:
        staging_directory = Path(temporary)

        for dataset in DATASETS:
            url = URL_BASE + dataset
            with urlopen(url, timeout=60) as response:
                processed = process_source_csv(response.read())

            staged_file = staging_directory / dataset
            staged_file.parent.mkdir(parents=True, exist_ok=True)
            processed.to_csv(staged_file, index=False)
            print(f"Processado: {dataset}")

        for dataset in DATASETS:
            staged_file = staging_directory / dataset
            destination = DATA_DIRECTORY / dataset
            destination.parent.mkdir(parents=True, exist_ok=True)
            staged_file.replace(destination)

    print(f"Atualização concluída: {len(DATASETS)} arquivos em {DATA_DIRECTORY}")
