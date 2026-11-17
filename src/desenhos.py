"""
Montagem das tabelas de indicadores dos desenhos A, B, C e D.

Uso básico:
    from src.indicadores import carregar_base
    from src.desenhos import montar_desenho, selecionar, padronizar_por_periodo
    mov, sal = carregar_base()
    tab_b = montar_desenho("B", mov, sal)            # todos os registros, com a marcação do universo
    principal_44 = selecionar(tab_b, universo=44)    # registros da análise principal

Cada tabela traz todos os registros possíveis do desenho, inclusive os que ficam fora da análise
principal, com a coluna `motivo_fora` explicando por quê. Assim, as regras de inclusão ficam
visíveis nos próprios dados, e os testes de sensibilidade usam a mesma tabela.

Desenhos (D13, D20, D27, D38):
    A  um registro por universidade, com o triênio 2023 a 2025
    B  um registro por universidade e janela de 2 anos: 2017-2018 a 2024-2025 (8 janelas)
    C  um registro por universidade e janela de 3 anos: 2017-2019 a 2023-2025 (7 janelas)
    D  um registro por universidade e ano, de 2017 a 2025, com a variação em relação ao ano anterior

Regras de inclusão na análise principal:
    - UFNT fora (D29); entra só no teste de sensibilidade, nos períodos dentro de 2024 e 2025.
    - Universidades novas: 2020 fica fora, por ser o primeiro exercício, sem saldo de abertura (D28).
      No desenho D, 2021 serve só de base para a variação (D40).
    - Período incompleto: a universidade precisa ter movimento em todos os anos do período.
    - Desmembramentos (D41): ficam fora, e entram num teste de sensibilidade, os registros que
      atravessam a saída de campi da UFG (de 2021 para 2022) e da UFRPE (de 2019 para 2020).
    - Universo de 39 (D26): só as universidades antigas, que têm dados em todos os anos.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.indicadores import NOMES_V3, calcular_indicadores, calcular_indicadores_anuais

UFNT = 26457
NOVAS = {26452: "UFCAT", 26453: "UFJ", 26454: "UFR", 26455: "UFDPar", 26456: "UFAPE"}
PRIMEIRO_EXERCICIO_NOVAS = 2020
# Universidade de origem: (último ano antes da saída dos campi, primeiro ano depois)
DESMEMBRAMENTOS = {26235: (2021, 2022), 26248: (2019, 2020)}  # UFG (UFCAT e UFJ); UFRPE (UFAPE)
ANOS_SENSIBILIDADE_UFNT = {2024, 2025}

PERIODOS = {
    "A": [(2023, 2025)],
    "B": [(a, a + 1) for a in range(2017, 2025)],
    "C": [(a, a + 2) for a in range(2017, 2024)],
    "D": [(a, a) for a in range(2017, 2026)],
}

COLUNAS_ID = ["desenho", "periodo", "ano_inicio", "ano_fim", "cod_orgao", "universo_39", "motivo_fora"]


def _rotulo(inicio: int, fim: int) -> str:
    return str(inicio) if inicio == fim else f"{inicio}-{fim}"


def _anos_com_movimento(mov: pd.DataFrame) -> pd.Series:
    """Conjunto de anos com movimento nos meses 1 a 12, por universidade."""
    m = mov[mov["mes"].between(1, 12)][["cod_orgao", "ano"]].drop_duplicates()
    return m.groupby("cod_orgao")["ano"].apply(set)


def _motivo_fora(desenho: str, cod: int, inicio: int, fim: int, anos_univ: set) -> str:
    """Motivo pelo qual o registro fica fora da análise principal (vazio quando entra)."""
    anos = set(range(inicio, fim + 1))
    if desenho == "D":
        anos_usados = {inicio - 1, inicio}  # o ano e o ano anterior, base da variação
    else:
        anos_usados = anos
    if cod == UFNT:
        return "UFNT (D29)"
    if cod in NOVAS:
        if PRIMEIRO_EXERCICIO_NOVAS in anos:
            return "primeiro exercício da universidade nova (D28)"
        if desenho == "D" and PRIMEIRO_EXERCICIO_NOVAS in anos_usados:
            return "ano base da variação da universidade nova (D40)"
    if not anos <= anos_univ:
        return "período incompleto"
    if desenho == "D" and (inicio - 1) not in anos_univ:
        return "sem ano anterior para a variação"
    if cod in DESMEMBRAMENTOS and set(DESMEMBRAMENTOS[cod]) <= anos_usados:
        return "desmembramento (D41)"
    return ""


def montar_desenho(desenho: str, mov: pd.DataFrame, sal: pd.DataFrame) -> pd.DataFrame:
    """
    Tabela do desenho com todos os registros possíveis e a marcação do universo.

    Colunas: desenho, periodo, ano_inicio, ano_fim, cod_orgao, universo_39, motivo_fora e os
    indicadores. No desenho D, os indicadores incluem as colunas Delta_<nome>.
    """
    desenho = desenho.upper()
    if desenho not in PERIODOS:
        raise ValueError("desenho deve ser A, B, C ou D")
    anos_univ = _anos_com_movimento(mov)

    if desenho == "D":
        anos = [inicio for inicio, _ in PERIODOS["D"]]
        t = calcular_indicadores_anuais(mov, sal, anos)
        t.insert(0, "periodo", t.pop("ano").astype(str))
        t["ano_inicio"] = t["periodo"].astype(int)
        t["ano_fim"] = t["ano_inicio"]
    else:
        partes = []
        for inicio, fim in PERIODOS[desenho]:
            r = calcular_indicadores(mov, sal, list(range(inicio, fim + 1)), regras="v3")
            r.insert(0, "periodo", _rotulo(inicio, fim))
            r["ano_inicio"], r["ano_fim"] = inicio, fim
            partes.append(r)
        t = pd.concat(partes, ignore_index=True)

    t["desenho"] = desenho
    t["universo_39"] = ~t["cod_orgao"].isin(set(NOVAS) | {UFNT})
    t["motivo_fora"] = [
        _motivo_fora(desenho, c, i, f, anos_univ.get(c, set()))
        for c, i, f in zip(t["cod_orgao"], t["ano_inicio"], t["ano_fim"])
    ]
    indicadores = [c for c in t.columns if c not in COLUNAS_ID]
    return t[COLUNAS_ID + indicadores].sort_values(["ano_inicio", "cod_orgao"], ignore_index=True)


def montar_todos(mov: pd.DataFrame, sal: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Tabelas dos quatro desenhos."""
    return {d: montar_desenho(d, mov, sal) for d in PERIODOS}


def colunas_indicadores(tabela: pd.DataFrame) -> list[str]:
    """Colunas de indicadores da tabela (sem as de identificação)."""
    return [c for c in tabela.columns if c not in COLUNAS_ID]


def selecionar(tabela: pd.DataFrame, universo: int = 44, sensibilidade: str | None = None) -> pd.DataFrame:
    """
    Registros de uma rodada.

    universo: 44 (todas as universidades do universo) ou 39 (só as antigas, D26).
    sensibilidade: None (análise principal), "ufnt" (acrescenta a UFNT nos períodos dentro de 2024
    e 2025) ou "desmembramentos" (acrescenta os registros retirados pela D41).
    """
    if universo not in (44, 39):
        raise ValueError("universo deve ser 44 ou 39")
    entra = tabela["motivo_fora"] == ""
    if sensibilidade == "ufnt":
        # Só períodos inteiros dentro de 2024 e 2025: janela 2024-2025 no B e anos 2024 e 2025 no D.
        # No A e no C, nenhum período cabe nesse intervalo.
        dentro = tabela["ano_inicio"].ge(min(ANOS_SENSIBILIDADE_UFNT)) & tabela["ano_fim"].le(max(ANOS_SENSIBILIDADE_UFNT))
        entra |= (tabela["cod_orgao"] == UFNT) & dentro
    elif sensibilidade == "desmembramentos":
        entra |= tabela["motivo_fora"] == "desmembramento (D41)"
    elif sensibilidade is not None:
        raise ValueError("sensibilidade deve ser None, 'ufnt' ou 'desmembramentos'")
    if universo == 39:
        entra &= tabela["universo_39"]
    return tabela[entra].reset_index(drop=True)


def padronizar_por_periodo(tabela: pd.DataFrame, metodo: str = "padrao") -> pd.DataFrame:
    """
    Padroniza cada indicador dentro de cada período (D19), com os registros da própria rodada.

    metodo "padrao": (x - média) / desvio padrão, como o StandardScaler.
    metodo "robusto": (x - mediana) / intervalo interquartil, como o RobustScaler.
    A escolha entre os dois é do protocolo (etapa 3). Indicador constante no período vira zero.
    """
    if metodo not in ("padrao", "robusto"):
        raise ValueError("metodo deve ser 'padrao' ou 'robusto'")
    t = tabela.copy()
    colunas = colunas_indicadores(t)
    grupos = t.groupby("periodo")[colunas]
    if metodo == "padrao":
        centro, escala = grupos.transform("mean"), grupos.transform(lambda x: x.std(ddof=0))
    else:
        centro = grupos.transform("median")
        escala = grupos.transform(lambda x: x.quantile(0.75) - x.quantile(0.25))
    t[colunas] = ((t[colunas] - centro) / escala.replace(0, np.nan)).fillna(0.0)
    return t


def resumo_registros(tabelas: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Número de registros por desenho: análise principal (44 e 39) e testes de sensibilidade."""
    linhas = []
    for d, t in tabelas.items():
        linhas.append({
            "desenho": d,
            "periodos": t["periodo"].nunique(),
            "principal_44": len(selecionar(t, 44)),
            "principal_39": len(selecionar(t, 39)),
            "com_ufnt": len(selecionar(t, 44, "ufnt")),
            "com_desmembramentos": len(selecionar(t, 44, "desmembramentos")),
            "indicadores": len(colunas_indicadores(t)),
        })
    return pd.DataFrame(linhas)
