"""
Resumo estatístico dos indicadores de cada desenho, gravado em 02_indicadores/resumo_indicadores.xlsx.

Uso básico:
    from src.resumo import gravar_resumo
    gravar_resumo("02_indicadores/resumo_indicadores.xlsx", tabelas, verificacoes)

As estatísticas usam os registros da análise principal com 44 universidades (src.desenhos.selecionar).
Elas alimentam a etapa 3, que fixa a regra do padrão comum (indicadores em que muitas universidades
têm o mesmo valor) e o limite de correlação entre indicadores. Os textos que explicam cada indicador
ficam em dicionario_indicadores.xlsx, editado à mão (D49).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.desenhos import colunas_indicadores, resumo_registros, selecionar
from src.verificacoes import resumo_por_ano

CASAS = 6  # casas decimais usadas para decidir se dois valores são iguais


def estatisticas(tabela: pd.DataFrame) -> pd.DataFrame:
    """Estatísticas de cada indicador nos registros da tabela, com a maior correlação com outro indicador."""
    colunas = colunas_indicadores(tabela)
    dados = tabela[colunas]
    rho = dados.corr(method="spearman").abs()
    for c in colunas:
        rho.loc[c, c] = np.nan
    linhas = []
    for c in colunas:
        x = dados[c].dropna()
        contagem = x.round(CASAS).value_counts(normalize=True)
        par = rho[c].idxmax() if rho[c].notna().any() else ""
        linhas.append({
            "indicador": c,
            "registros": len(x),
            "media": x.mean(),
            "mediana": x.median(),
            "p10": x.quantile(0.10),
            "p90": x.quantile(0.90),
            "minimo": x.min(),
            "maximo": x.max(),
            "valor_mais_comum": contagem.index[0] if len(contagem) else np.nan,
            "pct_valor_mais_comum": 100 * contagem.iloc[0] if len(contagem) else np.nan,
            "pct_zeros": 100 * (x.round(CASAS) == 0).mean() if len(x) else np.nan,
            "maior_correlacao": rho.loc[par, c] if par else np.nan,
            "indicador_mais_correlacionado": par,
        })
    return pd.DataFrame(linhas)


def pares_correlacionados(tabela: pd.DataFrame, quantidade: int = 15, limite: float = 0.75) -> pd.DataFrame:
    """Pares de indicadores com as maiores correlações de Spearman (em módulo), marcando os acima do limite."""
    colunas = colunas_indicadores(tabela)
    rho = tabela[colunas].corr(method="spearman")
    pares = [(a, b, rho.loc[a, b]) for i, a in enumerate(colunas) for b in colunas[i + 1:]]
    p = pd.DataFrame(pares, columns=["indicador_1", "indicador_2", "correlacao_spearman"]).dropna()
    p["modulo"] = p["correlacao_spearman"].abs()
    p = p.sort_values("modulo", ascending=False).head(quantidade)
    p["acima_de_" + str(limite).replace(".", "_")] = p["modulo"] >= limite
    return p.drop(columns="modulo").reset_index(drop=True)


def gravar_resumo(caminho: str | Path, tabelas: dict[str, pd.DataFrame],
                  verificacoes: pd.DataFrame | None = None) -> dict[str, pd.DataFrame]:
    """
    Grava o resumo em Excel e devolve as tabelas gravadas.

    Abas: registros (contagens por desenho), estatisticas_<desenho>, pares_<desenho> e, se as
    verificações forem passadas, verificacoes (universidades com alerta por ano, sem a UFNT e sem
    o primeiro exercício das universidades novas).
    """
    from src.desenhos import NOVAS, PRIMEIRO_EXERCICIO_NOVAS, UFNT

    abas = {"registros": resumo_registros(tabelas)}
    for d, t in tabelas.items():
        principal = selecionar(t, universo=44)
        abas[f"estatisticas_{d}"] = estatisticas(principal)
        abas[f"pares_{d}"] = pares_correlacionados(principal)
    if verificacoes is not None:
        v = verificacoes[(verificacoes["cod_orgao"] != UFNT)
                         & ~(verificacoes["cod_orgao"].isin(NOVAS) & (verificacoes["ano"] <= PRIMEIRO_EXERCICIO_NOVAS))]
        r = resumo_por_ano(v)
        r.index = [" ".join(str(p) for p in i if p != "").strip() if isinstance(i, tuple) else i for i in r.index]
        abas["verificacoes"] = r.reset_index(names="verificacao")

    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(caminho, engine="openpyxl") as escritor:
        for nome, tabela in abas.items():
            tabela.to_excel(escritor, sheet_name=nome, index=False)
            planilha = escritor.sheets[nome]
            for coluna in planilha.columns:
                largura = max(len(str(c.value)) if c.value is not None else 0 for c in coluna)
                planilha.column_dimensions[coluna[0].column_letter].width = min(max(largura + 2, 10), 45)
            planilha.freeze_panes = "B2"
    return abas
