"""
Leitura dos arquivos brutos extraídos do Tesouro Gerencial (consulta extracao_mestrado_v2.sql).

Cada arquivo traz um ano: exportacao_AAAA.csv, ou o mesmo CSV compactado em exportacao_AAAA.zip.
Quando os dois existem para o mesmo ano, o zip é usado, porque é ele que vai para o GitHub.
"""
from __future__ import annotations

import re
import zipfile
from pathlib import Path

import pandas as pd

# Colunas usadas no pipeline e o nome que recebem depois da leitura
COLUNAS_DADOS = {
    "ID_ANO_LANC": "ano",
    "ID_MES_LANC": "mes",
    "ID_ORGAO": "cod_orgao",
    "ID_UG_EXEC": "cod_ug",
    "ID_CONTA_CONTABIL": "cod_conta",
    "ID_GRUPO_DESPESA_NADE": "cod_gnd",
    "ID_ELEMENTO_DESPESA_NADE": "cod_elemento",
    "MOVIMLQUIDONOMSRCONTACONTBIL": "mov",
}
# Colunas de nomes, usadas só para montar as tabelas de nomes (dimensões)
COLUNAS_NOMES = {
    "NO_ORGAO": "nome_orgao",
    "NO_UG": "nome_ug",
    "NO_CONTA_CONTABIL": "nome_conta",
}
COLUNAS_INTEIRAS = ["ano", "mes", "cod_orgao", "cod_ug", "cod_gnd", "cod_elemento"]


def listar_arquivos(pasta: str | Path) -> dict[int, Path]:
    """Retorna {ano: caminho} para os arquivos da pasta. O ano é o último grupo de 4 dígitos do nome."""
    pasta = Path(pasta)
    if not pasta.is_dir():
        raise FileNotFoundError(f"Pasta não encontrada: {pasta.resolve()}")
    encontrados: dict[int, Path] = {}
    for caminho in sorted(pasta.iterdir()):
        if caminho.suffix.lower() not in (".csv", ".zip"):
            continue
        anos = re.findall(r"(20\d{2})", caminho.stem)
        if not anos:
            continue
        ano = int(anos[-1])
        # Se houver CSV e zip do mesmo ano, fica o zip
        if ano in encontrados and encontrados[ano].suffix.lower() == ".zip":
            continue
        encontrados[ano] = caminho
    if not encontrados:
        raise FileNotFoundError(f"Nenhum arquivo .csv ou .zip com ano no nome em {pasta.resolve()}")
    return dict(sorted(encontrados.items()))


def _abrir_binario(caminho: Path):
    """Abre o CSV em modo binário, de dentro do zip quando for o caso."""
    if caminho.suffix.lower() == ".zip":
        arquivo_zip = zipfile.ZipFile(caminho)
        csvs = [n for n in arquivo_zip.namelist() if n.lower().endswith(".csv")]
        if len(csvs) != 1:
            raise ValueError(f"{caminho.name}: o zip deve conter exatamente um CSV (encontrados: {csvs})")
        return arquivo_zip.open(csvs[0])
    return open(caminho, "rb")


def _detectar_formato(caminho: Path) -> tuple[str, str]:
    """Lê a primeira linha e devolve (codificação, separador)."""
    with _abrir_binario(caminho) as f:
        primeira = f.readline()
    try:
        texto = primeira.decode("utf-8-sig")
        codificacao = "utf-8-sig"
    except UnicodeDecodeError:
        texto = primeira.decode("latin1")
        codificacao = "latin1"
    separador = ";" if texto.count(";") > texto.count(",") else ","
    return codificacao, separador


def ler_cabecalho(caminho: str | Path) -> list[str]:
    caminho = Path(caminho)
    codificacao, separador = _detectar_formato(caminho)
    with _abrir_binario(caminho) as f:
        return pd.read_csv(f, sep=separador, encoding=codificacao, nrows=0).columns.tolist()


def _para_numero(serie: pd.Series, separador: str) -> pd.Series:
    """Converte o valor do movimento para número. No formato com ';' usa vírgula decimal."""
    if separador == ";":
        serie = (serie.astype(str).str.strip()
                 .str.replace(".", "", regex=False)
                 .str.replace(",", ".", regex=False))
    return pd.to_numeric(serie, errors="coerce")


def ler_ano(caminho: str | Path, com_nomes: bool = False) -> pd.DataFrame:
    """
    Lê um arquivo anual e devolve as colunas do pipeline com nomes curtos.

    Valores que não puderem ser convertidos ficam como ausentes (NaN). A conferência
    de qualidade conta esses casos; a leitura não descarta nenhuma linha.
    """
    caminho = Path(caminho)
    codificacao, separador = _detectar_formato(caminho)
    colunas = dict(COLUNAS_DADOS)
    if com_nomes:
        colunas.update(COLUNAS_NOMES)
    with _abrir_binario(caminho) as f:
        df = pd.read_csv(
            f,
            sep=separador,
            encoding=codificacao,
            usecols=list(colunas),
            dtype=str,
            low_memory=False,
        )
    df = df.rename(columns=colunas)
    for coluna in COLUNAS_INTEIRAS:
        df[coluna] = pd.to_numeric(df[coluna], errors="coerce")
    df["mov"] = _para_numero(df["mov"], separador)
    df["cod_conta"] = df["cod_conta"].astype(str).str.strip()
    return df
