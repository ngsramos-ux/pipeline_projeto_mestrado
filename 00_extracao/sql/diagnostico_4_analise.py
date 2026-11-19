"""
Análise do diagnóstico 4: dados das 24 universidades fundações.

Uso, a partir da pasta raiz do repositório:
    python 00_extracao/sql/diagnostico_4_analise.py

Lê os resultados das consultas 4A e 4B (diagnostico_4a.csv e diagnostico_4b.csv, nesta pasta,
exportados do SQuirrel) e a base consolidada da etapa 1, e imprime na tela as conferências
descritas em diagnostico_4_resultados.md. Nenhum arquivo é gravado.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

PASTA = Path(__file__).resolve().parent
RAIZ = PASTA.parents[1]
sys.path.insert(0, str(RAIZ))
from src.qualidade import UNIVERSIDADES_ANTIGAS, UNIVERSIDADES_NOVAS  # noqa: E402

QUARENTA_E_CINCO = set(UNIVERSIDADES_ANTIGAS) | set(UNIVERSIDADES_NOVAS)
UFNT = 26457
ANTIGO_CEFET_MG = 26257  # universidade só a partir de 2026; fica fora do universo
DESMEMBRAMENTOS = {26251: "UFT", 26276: "UFMT", 26279: "UFPI", 26235: "UFG", 26248: "UFRPE"}
TOLERANCIA = 0.05  # reais, como em src/qualidade.py

pd.set_option("display.width", 250)
pd.set_option("display.max_rows", 200)
pd.set_option("display.max_columns", 30)


def titulo(texto: str) -> None:
    print(f"\n{'=' * 80}\n{texto}\n{'=' * 80}")


def carregar() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Lê as duas consultas, com as colunas de órgão e ano renomeadas."""
    nomes = {"ID_ORGAO_UG": "org", "ID_ANO_LANC": "ano"}
    a = pd.read_csv(PASTA / "diagnostico_4a.csv").rename(columns=nomes)
    b = pd.read_csv(PASTA / "diagnostico_4b.csv").rename(columns=nomes)
    tabela = b.merge(a, on=["org", "ano"], how="outer").sort_values(["org", "ano"])
    tabela["grupo"] = np.select(
        [tabela["org"].isin(QUARENTA_E_CINCO), tabela["org"] == ANTIGO_CEFET_MG], ["45", "26257"], "24")
    return a, tabela


def orgaos(a: pd.DataFrame) -> None:
    titulo("1. Órgãos encontrados")
    nomes = a.groupby("org")["NO_ORGAO"].first()
    anos = a.groupby("org")["ano"].agg(primeiro="min", ultimo="max", anos="count")
    print(f"Total: {len(nomes)} | das 45: {len(set(nomes.index) & QUARENTA_E_CINCO)} | "
          f"faltam das 45: {sorted(QUARENTA_E_CINCO - set(nomes.index))}")
    fora = nomes[~nomes.index.isin(QUARENTA_E_CINCO)]
    print("\nÓrgãos fora das 45:")
    print(pd.concat([fora, anos.loc[fora.index]], axis=1).to_string())


def regressao(t: pd.DataFrame) -> None:
    titulo("2. A consulta reproduz a base consolidada das 45?")
    mov = pd.read_parquet(RAIZ / "01_conferencia_e_consolidacao/base_consolidada/movimentos.parquet",
                          columns=["ano", "mes", "cod_orgao", "cod_conta", "mov"])
    mov["classe"] = mov["cod_conta"].str[0]

    def soma(classe: str, meses) -> pd.Series:
        x = mov[(mov["classe"] == classe) & mov["mes"].isin(meses)]
        return x.groupby(["cod_orgao", "ano"])["mov"].sum()

    base = pd.DataFrame({
        "ATIVO_ABERTURA": soma("1", [0]),
        "ATIVO_FINAL": soma("1", range(0, 14)),
        "PASSIVO_PL_FINAL": soma("2", range(0, 14)),
        "VPD": soma("3", range(1, 13)),
        "VPA": soma("4", range(1, 13)),
    }).fillna(0.0)
    base.index.names = ["org", "ano"]
    consulta = t[t["grupo"] == "45"].set_index(["org", "ano"])[base.columns]
    comum = consulta.index.intersection(base.index)
    print(f"Registros comparados: {len(comum)} | só na consulta: {len(consulta.index.difference(base.index))} | "
          f"só na base: {len(base.index.difference(consulta.index))}")
    print("Diferença máxima, em reais:")
    print((consulta.loc[comum] - base.loc[comum]).abs().max().to_frame("diferenca_maxima").T)


def igualdades(t: pd.DataFrame) -> pd.DataFrame:
    titulo(f"3. Anos, meses e igualdades contábeis (tolerância de R$ {TOLERANCIA})")
    t = t.copy()
    t["dif_abertura"] = t["ATIVO_ABERTURA"] - t["PASSIVO_PL_ABERTURA"]
    t["dif_balanco"] = t["ATIVO_FINAL"] - t["PASSIVO_PL_FINAL"]
    t["dif_encerramento"] = t["ENCERRAMENTO_PL"] - (t["VPA"] - t["VPD"])
    anterior = t.groupby("org")[["ano", "ATIVO_FINAL"]].shift()
    seguido = anterior["ano"] == t["ano"] - 1
    t["dif_continuidade"] = np.where(seguido, t["ATIVO_ABERTURA"] - anterior["ATIVO_FINAL"], np.nan)

    v24 = t[t["grupo"] == "24"]
    print(f"Universidades fundações: {v24['org'].nunique()} | registros: {len(v24)} | "
          f"anos por universidade: {sorted(v24.groupby('org')['ano'].count().unique())} | "
          f"meses distintos: {sorted(v24['QTD_MESES'].unique())}")
    print(f"Lançamentos no mês 14 (todas as universidades): {int(t['QTD_LANC_MES_14'].sum())}")
    for c in ["dif_abertura", "dif_balanco", "dif_encerramento", "dif_continuidade"]:
        ruim = t[t[c].abs() > TOLERANCIA]
        print(f"{c}: {len(ruim)} registros acima da tolerância")
        if len(ruim):
            print(ruim[["org", "ano", "grupo", c]].to_string(index=False))
    return t


def completude(t: pd.DataFrame) -> None:
    titulo("4. Completude e porte: as 24 comparadas com as 45")
    # Mesmo universo da análise: sem a UFNT e sem o primeiro exercício das universidades novas.
    x = t[(t["org"] != UFNT) & ~(t["org"].isin(UNIVERSIDADES_NOVAS) & (t["ano"] <= 2020))].copy()
    x["lanc_por_milhao_vpd"] = x["QTD_LANCAMENTOS"] / (x["VPD"] / 1e6)
    x["pct_classes_6_8"] = 100 * (x["QTD_LANC_CLASSE_6"] + x["QTD_LANC_CLASSE_8"]) / x["QTD_LANCAMENTOS"]
    medidas = ["QTD_LANCAMENTOS", "QTD_CONTAS", "QTD_LANC_MES_0", "QTD_LANC_MES_13", "lanc_por_milhao_vpd",
               "pct_classes_6_8"]
    dois = x[x["grupo"].isin(["24", "45"])]
    print("Medianas anuais:")
    print(dois.groupby("grupo")[medidas].median().T.round(1))

    faixa = x[x["grupo"] == "45"].groupby("ano")[medidas].agg(["min", "max"])
    print("\nRegistros das 24 fora da faixa (mínimo a máximo) das 45 no mesmo ano:")
    for c in medidas:
        y = x[x["grupo"] == "24"].join(faixa[c], on="ano")
        fora = y[(y[c] < y["min"]) | (y[c] > y["max"])]
        print(f"  {c}: {len(fora)} de {len(y)}",
              fora[["org", "ano", c, "min", "max"]].round(1).to_dict("records") if len(fora) else "")

    v = t[(t["ano"] == 2025) & (t["grupo"] != "26257")].set_index("org")
    posicao = v["VPD"].rank(ascending=False).astype(int)
    print(f"\nPosição das 24 em VPD de 2025, entre as {len(v)} universidades:")
    print(pd.DataFrame({"nome": v["NO_ORGAO"], "VPD_bilhoes": (v["VPD"] / 1e9).round(2), "posicao": posicao})
          [v["grupo"] == "24"].sort_values("posicao").to_string())


def picos(t: pd.DataFrame, limite: float = 2.0) -> None:
    titulo(f"5. Picos de VPD nas 24: anos com VPD acima de {limite} vezes a mediana dos demais anos")
    linhas = []
    for org, g in t[t["grupo"] == "24"].groupby("org"):
        g = g.set_index("ano")["VPD"]
        for ano, valor in g.items():
            demais = g.drop(ano)
            if valor > limite * demais.median():
                linhas.append({"org": org, "ano": ano, "VPD_bilhoes": round(valor / 1e9, 2),
                               "demais_min": round(demais.min() / 1e9, 2), "demais_max": round(demais.max() / 1e9, 2),
                               "vezes_a_mediana": round(valor / demais.median(), 1)})
    print(pd.DataFrame(linhas).to_string(index=False))


def desmembramentos(t: pd.DataFrame) -> None:
    titulo("6. Saída de campi: VPD, variação anual e UGs")
    antigas = t[t["org"].isin(set(UNIVERSIDADES_ANTIGAS) - {26235, 26248})].copy()
    antigas["var"] = antigas.groupby("org")["VPD"].pct_change() * 100
    print("Variação mediana da VPD nas universidades antigas, sem UFG e UFRPE (%):")
    print(antigas.groupby("ano")["var"].median().round(1).to_frame("mediana").T.to_string())
    for org, sigla in DESMEMBRAMENTOS.items():
        g = t[t["org"] == org].set_index("ano")
        print(f"\n{sigla} ({org}):")
        print(pd.DataFrame({"VPD_milhoes": (g["VPD"] / 1e6).round(0),
                            "variacao_%": (g["VPD"].pct_change() * 100).round(1),
                            "UGs": g["QTD_UG"], "lancamentos": g["QTD_LANCAMENTOS"]}).T.to_string())


if __name__ == "__main__":
    a, tabela = carregar()
    orgaos(a)
    regressao(tabela)
    tabela = igualdades(tabela)
    completude(tabela)
    picos(tabela)
    desmembramentos(tabela)
