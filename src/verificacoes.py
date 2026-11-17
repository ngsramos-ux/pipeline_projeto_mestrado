"""
Verificações simples do painel (D43 e D46), feitas fora dos modelos de anomalia.

Uso básico:
    from src.indicadores import carregar_base
    from src.verificacoes import verificar, resumo_por_ano
    mov, sal = carregar_base()
    alertas = verificar(mov, sal, anos=range(2017, 2026))
    resumo_por_ano(alertas)

Cada verificação aplica uma regra contábil objetiva aos saldos de fim de exercício (mês 13) e ao
movimento dos meses 1 a 12. Elas existem porque uma falha comum a muitas universidades deixa de
ser rara, e um modelo de anomalia tende a não apontá-la (D42).

Verificações:
    V1  Bens móveis sem depreciação: saldo de bens móveis (1.2.3.1.1) no fim do ano e nenhuma VPD de
        depreciação de bens móveis (3.3.3.1.1.01) no ano.
    V2  Imóveis sem depreciação: saldo de imóveis (1.2.3.2.1, sem terrenos, obras em andamento,
        estudos e projetos e imóveis a classificar) e nenhuma VPD de depreciação de imóveis
        (3.3.3.1.1.02) no ano.
    V3  Bens móveis a classificar: saldo na conta 1.2.3.1.1.99.08 no fim do ano.
    V4  Imóveis a classificar ou a registrar: saldo na conta 1.2.3.2.1.99.05 no fim do ano.
    V5  Nenhuma provisão (ponto de atenção setorial): nenhum saldo em provisões de curto ou de longo
        prazo (2.1.7 e 2.2.7) no fim do ano. Não prova erro, porque só há obrigação de provisionar
        quando a perda é provável.

O resultado traz todas as universidades com movimento em cada ano. As regras de universo (UFNT,
primeiro exercício das novas) ficam a cargo de quem usa o resultado, como no painel.
"""
from __future__ import annotations

import pandas as pd

LIMITE = 1.0  # valores abaixo de R$ 1 são tratados como zero

VERIFICACOES = {
    "V1": ("Bens móveis sem depreciação", "falha"),
    "V2": ("Imóveis sem depreciação", "falha"),
    "V3": ("Bens móveis a classificar", "falha"),
    "V4": ("Imóveis a classificar ou a registrar", "falha"),
    "V5": ("Nenhuma provisão", "atenção setorial"),
}

IMOVEIS_NAO_DEPRECIAVEIS = ("123210103", "1232106", "123219905")  # terrenos, obras e estudos, a classificar


def _bases(mov: pd.DataFrame, sal: pd.DataFrame, anos: list[int]) -> pd.DataFrame:
    """Saldos e movimentos usados nas verificações, uma linha por universidade e ano."""
    m = mov[mov["ano"].isin(anos) & mov["mes"].between(1, 12)]
    indice = m[["cod_orgao", "ano"]].drop_duplicates().set_index(["cod_orgao", "ano"]).index
    fim = sal[sal["ano"].isin(anos) & (sal["mes"] == 13)]

    def saldo(prefixos, excluir=()):
        f = fim["cod_conta"].str.startswith(prefixos)
        if excluir:
            f &= ~fim["cod_conta"].str.startswith(excluir)
        return fim[f].groupby(["cod_orgao", "ano"])["saldo"].sum().reindex(indice, fill_value=0.0)

    def fluxo(prefixos):
        f = m[m["cod_conta"].str.startswith(prefixos)]
        return f.groupby(["cod_orgao", "ano"])["mov"].sum().reindex(indice, fill_value=0.0)

    return pd.DataFrame({
        "bens_moveis": saldo("12311"),
        "deprec_moveis": fluxo("333110100").abs(),
        "imoveis_depreciaveis": saldo("12321", IMOVEIS_NAO_DEPRECIAVEIS),
        "imoveis": saldo("12321"),
        "deprec_imoveis": fluxo("333110200").abs(),
        "moveis_a_classificar": saldo("123119908"),
        "imoveis_a_classificar": saldo("123219905"),
        "provisoes": saldo(("217", "227")),
    })


def verificar(mov: pd.DataFrame, sal: pd.DataFrame, anos=range(2017, 2026)) -> pd.DataFrame:
    """
    Resultado das 5 verificações, uma linha por universidade, ano e verificação.

    Colunas: ano, cod_orgao, codigo, verificacao, tipo, alerta (verdadeiro ou falso), valor (o valor
    envolvido, em reais), base (o saldo de referência) e percentual (valor sobre a base, em %).
    Em V1 e V2, o valor é o saldo dos bens sem depreciação; base e percentual ficam vazios.
    Em V3 e V4, a base é o saldo de bens móveis ou de imóveis. Em V5, só o alerta é informado.
    """
    b = _bases(mov, sal, list(anos))
    regras = {
        "V1": (b["bens_moveis"].gt(LIMITE) & b["deprec_moveis"].lt(LIMITE), b["bens_moveis"], b["bens_moveis"]),
        "V2": (b["imoveis_depreciaveis"].gt(LIMITE) & b["deprec_imoveis"].lt(LIMITE),
               b["imoveis_depreciaveis"], b["imoveis"]),
        "V3": (b["moveis_a_classificar"].abs().ge(LIMITE), b["moveis_a_classificar"], b["bens_moveis"]),
        "V4": (b["imoveis_a_classificar"].abs().ge(LIMITE), b["imoveis_a_classificar"], b["imoveis"]),
        "V5": (b["provisoes"].abs().lt(LIMITE), b["provisoes"], b["provisoes"]),
    }
    partes = []
    for codigo, (alerta, valor, base) in regras.items():
        nome, tipo = VERIFICACOES[codigo]
        p = pd.DataFrame({"alerta": alerta, "valor": valor.abs(), "base": base.abs()})
        p["percentual"] = (100 * p["valor"] / p["base"].where(p["base"] > 0)).round(3)
        p.insert(0, "tipo", tipo)
        p.insert(0, "verificacao", nome)
        p.insert(0, "codigo", codigo)
        partes.append(p.reset_index())
    resultado = pd.concat(partes, ignore_index=True)
    # V1 e V2: o valor é o próprio saldo sem depreciação, sem base de comparação; V5 não tem valor
    resultado.loc[resultado["codigo"].isin(["V1", "V2"]), ["base", "percentual"]] = None
    resultado.loc[resultado["codigo"] == "V5", ["valor", "base", "percentual"]] = None
    return resultado[["ano", "cod_orgao", "codigo", "verificacao", "tipo", "alerta", "valor", "base", "percentual"]] \
        .sort_values(["ano", "codigo", "cod_orgao"], ignore_index=True)


def resumo_por_ano(resultado: pd.DataFrame) -> pd.DataFrame:
    """Número de universidades com alerta em cada verificação e ano."""
    alertas = resultado[resultado["alerta"]]
    tabela = alertas.pivot_table(index=["codigo", "verificacao"], columns="ano", values="cod_orgao",
                                 aggfunc="count", fill_value=0)
    universidades = resultado.groupby("ano")["cod_orgao"].nunique().rename(("", "universidades"))
    return pd.concat([tabela, universidades.to_frame().T])
