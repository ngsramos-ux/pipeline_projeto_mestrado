"""
Cálculo dos indicadores (F1 a F23) para qualquer período, a partir da base consolidada.

Uso básico:
    from src.indicadores import carregar_base, calcular_indicadores, calcular_indicadores_anuais
    mov, sal = carregar_base()
    ind = calcular_indicadores(mov, sal, anos=[2023, 2024, 2025])   # um período (desenhos A a C)
    anual = calcular_indicadores_anuais(mov, sal, anos=range(2017, 2026))   # desenho D

Regras disponíveis (parâmetro `regras`):
    "v3"  regras da Versão 3 (padrão):
          - F10, F11, F14, F15 e F20 usam o saldo das contas no fim de cada mês (D35);
          - as séries mensais têm todos os meses do período, com zero nos meses sem movimento (D36);
          - F10 inclui os estoques (1.1.5) e os demais créditos (1.1.3), e F15 usa os créditos
            1.1.2 + 1.1.3, porque as universidades quase não usam a conta 1.1.2 (D37);
          - F21 a F23, adaptados de Martins (2019), usam os saldos de fim de exercício (D44, D45);
          - F5, F7 e F12 medem os pagamentos pela conta 6.2.2.1.3.04 (crédito empenhado liquidado
            pago), e não pelo grupo 6.2.2.1.3, cujo movimento é o valor empenhado (D47);
          - a F19 usa a inscrição de restos a pagar do ano anterior a cada ano do período, mesmo
            que esse ano anterior esteja fora do período.
    "v2"  reprodução exata da Versão 2, usada só no teste de regressão: tudo calculado com o
          movimento do mês e só com os dados do próprio período.

Convenções:
    - Indicadores de fluxo usam os meses 1 a 12 de cada ano do período (D25).
    - Saldos são os do fim de cada mês, já calculados na consolidação com os meses 0 a 13.
    - O resultado tem uma linha por universidade com dados no período. As regras de inclusão do
      universo (UFNT, primeiro exercício das universidades novas) são aplicadas na montagem dos
      desenhos, e não aqui.
    - Valores impossíveis de calcular (divisão por zero, série constante) viram 0, como na Versão 2.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

PASTA_BASE = Path("01_conferencia_e_consolidacao/base_consolidada")
CHAVE = ["cod_orgao", "ano", "mes"]

NOMES = [
    "F1_Cor_VPA_RecArr", "F2_Cor_VPA_Cred", "F3_Volatilidade_VPA", "F4_Volatilidade_VPD",
    "F5_Var_Pag_Repasse", "F6_Var_RPE_PL", "F7_Qtd_Deficit_Fin", "F8_Var_Margem_Pat",
    "F9_Ang_RPE", "F10_Volatilidade_NFCP", "F11_Ang_Passivo", "F12_Cor_FCO_RPE",
    "F13_Var_Inv_Custeio", "F14_Var_Disp_Caixa", "F15_Var_Creditos", "F16_Ang_VPD",
    "F17_Sazonalidade_Dez", "F18_Indice_DEA", "F19_Max_Cancel_RAP", "F20_Volatilidade_Provisoes",
]
# Indicadores adaptados de Martins (2019), só nas regras v3 (D44 e D45)
NOMES_MARTINS = ["F21_Liquidez_Corrente", "F22_Imobilizado_Ativo", "F23_Taxa_Deprec_Moveis"]
NOMES_V3 = NOMES + NOMES_MARTINS

# Desenho D (D38): três indicadores de tendência ganham uma versão anual, com nome próprio
NOMES_ANUAIS = {
    "F9_Ang_RPE": "F9_RPE_sobre_VPA_Ano",
    "F11_Ang_Passivo": "F11_Passivo_Ativo_Fim_Ano",
    "F16_Ang_VPD": "F16_Cresc_VPD_Ano",
}
SEM_DELTA = ["F16_Cresc_VPD_Ano", "F19_Max_Cancel_RAP"]  # F16 já é variação; F19 de 2017 exigiria 2015 (D38)


# ---------------------------------------------------------------------------------------------
# Leitura
# ---------------------------------------------------------------------------------------------
def carregar_base(pasta: str | Path = PASTA_BASE) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Lê movimentos e saldos da base consolidada, com a conta como texto."""
    pasta = Path(pasta)
    mov = pd.read_parquet(pasta / "movimentos.parquet")
    sal = pd.read_parquet(pasta / "saldos_mensais.parquet")
    for t in (mov, sal):
        t["cod_conta"] = t["cod_conta"].astype(str)
    return mov, sal


# ---------------------------------------------------------------------------------------------
# Séries mensais
# ---------------------------------------------------------------------------------------------
def _fluxo(mov: pd.DataFrame, prefixos, nome: str, mascara=None, grade: pd.DataFrame | None = None) -> pd.DataFrame:
    """
    Soma mensal do movimento das contas com os prefixos dados, mantendo o sinal do SIAFI.

    Com `grade`, a série tem todos os meses da grade, com zero nos meses sem movimento (regras v3).
    Sem `grade`, só os meses com algum lançamento entram na série (regras v2).
    """
    filtro = mov["cod_conta"].str.startswith(prefixos)
    if mascara is not None:
        filtro &= mascara
    serie = mov[filtro].groupby(CHAVE)["mov"].sum().rename(nome).reset_index()
    if grade is not None:
        serie = grade.merge(serie, on=CHAVE, how="left").fillna({nome: 0.0})
    return serie


def _juntar(*tabelas: pd.DataFrame) -> pd.DataFrame:
    """Junta séries mensais pelos meses em que alguma delas tem valor (como na Versão 2)."""
    resultado = tabelas[0]
    for t in tabelas[1:]:
        resultado = resultado.merge(t, on=CHAVE, how="outer")
    return resultado.fillna(0.0).sort_values(CHAVE)


def _saldo(sal: pd.DataFrame, grade: pd.DataFrame, prefixos, nome: str) -> pd.DataFrame:
    """Saldo no fim de cada mês das contas com os prefixos dados, em todos os meses da grade."""
    s = sal[sal["cod_conta"].str.startswith(prefixos)].groupby(CHAVE)["saldo"].sum().rename(nome)
    return grade.merge(s.reset_index(), on=CHAVE, how="left").fillna({nome: 0.0})


def _grade(mov: pd.DataFrame) -> pd.DataFrame:
    """Meses 1 a 12 de cada ano em que a universidade tem movimento no período."""
    anos = mov[["cod_orgao", "ano"]].drop_duplicates()
    return anos.merge(pd.DataFrame({"mes": range(1, 13)}), how="cross").sort_values(CHAVE)


# ---------------------------------------------------------------------------------------------
# Estatísticas por universidade (mesmas travas da Versão 2)
# ---------------------------------------------------------------------------------------------
def _cv(df: pd.DataFrame, coluna: str, absoluto: bool = True) -> pd.Series:
    def f(g):
        media, desvio = g[coluna].mean(), g[coluna].std()
        if media == 0 or pd.isna(media):
            return 0.0
        return abs(desvio / media) if absoluto else desvio / media
    return df.groupby("cod_orgao")[[coluna]].apply(f)


def _correlacao(df: pd.DataFrame, a: str, b: str) -> pd.Series:
    def f(g):
        if g[a].std() == 0 or g[b].std() == 0:
            return 0.0
        return g[a].corr(g[b])
    return df.groupby("cod_orgao")[[a, b]].apply(f)


def _inclinacao(df: pd.DataFrame, coluna: str, divisor: str | None = None) -> pd.Series:
    """Coeficiente angular da série mensal (eixo x = 1 a n), dividido pela média do divisor."""
    def f(g):
        y = g[coluna].to_numpy()
        if len(y) < 2:
            return 0.0
        inclinacao = np.polyfit(np.arange(1, len(y) + 1), y, 1)[0]
        if divisor is None:
            return inclinacao
        media = g[divisor].mean()
        return 0.0 if media == 0 or pd.isna(media) else inclinacao / media
    colunas = list(dict.fromkeys([coluna] + ([divisor] if divisor else [])))
    return df.sort_values(CHAVE).groupby("cod_orgao")[colunas].apply(f)


def _razao(numerador: pd.Series, denominador: pd.Series) -> pd.Series:
    return pd.Series(np.where(denominador == 0, 0.0, numerador / denominador.where(denominador != 0, 1)),
                     index=numerador.index)


# ---------------------------------------------------------------------------------------------
# Indicadores
# ---------------------------------------------------------------------------------------------
def calcular_indicadores(mov: pd.DataFrame, sal: pd.DataFrame, anos: list[int],
                         regras: str = "v3") -> pd.DataFrame:
    """
    Calcula F1 a F20 para o período formado pelos anos indicados (meses 1 a 12 de cada ano).

    Retorna um DataFrame com cod_orgao e as 20 colunas, uma linha por universidade com
    movimento no período.
    """
    if regras not in ("v2", "v3"):
        raise ValueError("regras deve ser 'v2' ou 'v3'")
    anos = sorted(anos)
    m = mov[mov["ano"].isin(anos) & mov["mes"].between(1, 12)]
    universidades = pd.Index(sorted(m["cod_orgao"].unique()), name="cod_orgao")
    r = pd.DataFrame(index=universidades)
    grade = _grade(m)
    g = grade if regras == "v3" else None  # v3: séries mensais completas, com zero nos meses sem movimento

    def fluxo(prefixos, nome, mascara=None):
        return _fluxo(m, prefixos, nome, mascara, g)

    vpa_bruta = fluxo("4", "vpa")
    vpd_bruta = fluxo("3", "vpd")
    vpa_abs = vpa_bruta.assign(vpa=vpa_bruta["vpa"].abs())
    vpd_abs = vpd_bruta.assign(vpd=vpd_bruta["vpd"].abs())

    # F1: correlação entre VPA e receita arrecadada (6212 + 8211), contas credoras com sinal invertido
    rec = fluxo(("6212", "8211"), "rec")
    t = _juntar(vpa_bruta.assign(vpa=-vpa_bruta["vpa"]), rec.assign(rec=-rec["rec"]))
    r["F1_Cor_VPA_RecArr"] = _correlacao(t, "vpa", "rec")

    # F2: correlação entre VPA e créditos de curto prazo (112)
    t = _juntar(vpa_bruta.assign(vpa=-vpa_bruta["vpa"]), fluxo("112", "cred"))
    r["F2_Cor_VPA_Cred"] = _correlacao(t, "vpa", "cred")

    # F3 e F4: volatilidade da VPA e da VPD
    r["F3_Volatilidade_VPA"] = _cv(vpa_abs, "vpa", absoluto=False)
    r["F4_Volatilidade_VPD"] = _cv(vpd_abs, "vpd", absoluto=False)

    # F5: volatilidade de pagamentos sobre repasses (8211). Os pagamentos também entram na F7 e na F12.
    # v3 (D47): só a conta de crédito empenhado liquidado pago (6.2.2.1.3.04).
    # v2: o grupo 6.2.2.1.3 inteiro, cujo movimento líquido é o crédito empenhado do mês, e não o pago.
    pag = fluxo("6221304" if regras == "v3" else "62213", "pag")
    rep = fluxo("8211", "rep")
    t = _juntar(pag.assign(pag=pag["pag"].abs()), rep.assign(rep=rep["rep"].abs()))
    t["razao"] = _razao(t["pag"], t["rep"])
    r["F5_Var_Pag_Repasse"] = _cv(t, "razao", absoluto=False)

    # F6: volatilidade do resultado patrimonial sobre o PL (movimento do grupo 2.3)
    pl = fluxo("23", "pl")
    t = _juntar(_juntar(vpa_abs, vpd_abs), pl.assign(pl=pl["pl"].abs()))
    t["razao"] = _razao(t["vpa"] - t["vpd"], t["pl"])
    r["F6_Var_RPE_PL"] = _cv(t, "razao")

    # F7: meses com déficit financeiro (pagamentos maiores que entradas)
    ent = fluxo(("6212", "8211"), "ent")
    t = _juntar(ent.assign(ent=ent["ent"].abs()), pag.assign(pag=pag["pag"].abs()))
    r["F7_Qtd_Deficit_Fin"] = (t["pag"] > t["ent"]).groupby(t["cod_orgao"]).sum()

    # F8: volatilidade da margem patrimonial (resultado / VPA)
    t = _juntar(vpa_abs, vpd_abs)
    t["margem"] = _razao(t["vpa"] - t["vpd"], t["vpa"])
    r["F8_Var_Margem_Pat"] = _cv(t, "margem")

    # F9: tendência do resultado patrimonial, dividida pela média mensal da VPA (D06)
    t = _juntar(vpa_abs, vpd_abs)
    t["rpe"] = t["vpa"] - t["vpd"]
    r["F9_Ang_RPE"] = _inclinacao(t, "rpe", divisor="vpa")

    # F10, F11, F14, F15 e F20: movimento (v2) ou saldo no fim do mês (v3, D35)
    if regras == "v2":
        def mov_abs(prefixos, nome):
            f = fluxo(prefixos, nome)
            return f.assign(**{nome: f[nome].abs()})
        t = _juntar(mov_abs("112", "c112"), mov_abs("113", "c113"), mov_abs("213", "c213"), mov_abs("1", "c1"))
        t["razao"] = _razao(t["c112"] + t["c113"] - t["c213"], t["c1"])
        r["F10_Volatilidade_NFCP"] = _cv(t, "razao")
        t = _juntar(mov_abs("21", "c21"), mov_abs("1", "c1"))
        t["razao"] = _razao(t["c21"], t["c1"])
        r["F11_Ang_Passivo"] = _inclinacao(t, "razao")
        r["F14_Var_Disp_Caixa"] = _cv(mov_abs("111", "c111"), "c111")
        r["F15_Var_Creditos"] = _cv(mov_abs("112", "c112"), "c112")
        prov = mov_abs(("217", "227"), "prov")
    else:
        s = grade
        for prefixos, nome in [("1", "c1"), ("111", "c111"), ("112", "c112"), ("113", "c113"),
                               ("115", "c115"), ("21", "c21"), ("213", "c213"), (("217", "227"), "prov")]:
            s = _saldo(sal, s, prefixos, nome)
        # F10 (D37): créditos (1.1.2 + 1.1.3) + estoques (1.1.5) - fornecedores e contas a pagar (2.1.3)
        s["nfcp"] = _razao(s["c112"] + s["c113"] + s["c115"] - s["c213"], s["c1"])
        s["passivo_ativo"] = _razao(s["c21"], s["c1"])
        r["F10_Volatilidade_NFCP"] = _cv(s, "nfcp")
        r["F11_Ang_Passivo"] = _inclinacao(s, "passivo_ativo")
        r["F14_Var_Disp_Caixa"] = _cv(s, "c111")
        # F15 (D37): créditos de curto prazo das universidades ficam quase todos em 1.1.3
        s["creditos"] = s["c112"] + s["c113"]
        r["F15_Var_Creditos"] = _cv(s, "creditos")
        prov = s[CHAVE + ["prov"]]

    def cv_f20(g):
        v = g["prov"].to_numpy()
        if len(v) < 2 or np.mean(v) == 0:
            return 0.0
        return abs(np.std(v, ddof=1) / np.mean(v))
    r["F20_Volatilidade_Provisoes"] = prov.groupby("cod_orgao")[["prov"]].apply(cv_f20)

    # F12: correlação entre fluxo de caixa (entradas - pagamentos) e resultado patrimonial (VPA - VPD)
    t = _juntar(vpa_bruta, vpd_bruta, fluxo(("6212", "8211"), "ent"), pag)
    t["rpe"] = t["vpa"] - t["vpd"]
    t["fco"] = t["ent"] - t["pag"]
    r["F12_Cor_FCO_RPE"] = _correlacao(t, "rpe", "fco")

    # F13: volatilidade de investimento (GND 4) sobre custeio (GND 3), pelos pagamentos (6221304)
    cus = fluxo("6221304", "cus", m["cod_gnd"] == 3)
    inv = fluxo("6221304", "inv", m["cod_gnd"] == 4)
    t = _juntar(cus.assign(cus=cus["cus"].abs()), inv.assign(inv=inv["inv"].abs()))
    t["razao"] = _razao(t["inv"], t["cus"])
    r["F13_Var_Inv_Custeio"] = _cv(t, "razao")

    # F16: tendência da VPD, dividida pela média mensal da VPD (D06)
    r["F16_Ang_VPD"] = _inclinacao(vpd_abs, "vpd", divisor="vpd")

    # F17: média, entre os anos, da razão entre a VPD de dezembro e a média de janeiro a novembro
    def f17(g):
        razoes = []
        for _, a in g.groupby("ano"):
            media = a.loc[a["mes"] <= 11, "vpd"].mean()
            if pd.notna(media) and media > 0:
                razoes.append(a.loc[a["mes"] == 12, "vpd"].sum() / media)
        return float(np.mean(razoes)) if razoes else 0.0
    r["F17_Sazonalidade_Dez"] = vpd_abs.groupby("cod_orgao")[["ano", "mes", "vpd"]].apply(f17)

    # F18: despesas de exercícios anteriores (elemento 92) sobre o total pago (6221304)
    pagos = _fluxo(m, "6221304", "pagos")
    dea = _fluxo(m, "6221304", "dea", m["cod_elemento"] == 92)
    total = pagos["pagos"].abs().groupby(pagos["cod_orgao"]).sum()
    total_dea = dea["dea"].abs().groupby(dea["cod_orgao"]).sum().reindex(total.index, fill_value=0.0)
    r["F18_Indice_DEA"] = _razao(total_dea, total)

    # F19: maior taxa anual de cancelamento de restos a pagar não processados (6319) sobre a
    # inscrição do ano anterior (6221305 e 6221306)
    if regras == "v2":
        base_inscricao = m
    else:
        base_inscricao = mov[mov["ano"].isin([a - 1 for a in anos] + anos) & mov["mes"].between(1, 12)]
    insc = _fluxo(base_inscricao, ("6221305", "6221306"), "insc")
    canc = _fluxo(m, "6319", "canc")
    insc_ano = insc.assign(insc=insc["insc"].abs()).groupby(["cod_orgao", "ano"])["insc"].sum().reset_index()
    canc_ano = canc.assign(canc=canc["canc"].abs()).groupby(["cod_orgao", "ano"])["canc"].sum().reset_index()
    insc_ano["ano"] = insc_ano["ano"] + 1  # a inscrição do ano X é a base do cancelamento do ano X + 1
    t = canc_ano.merge(insc_ano, on=["cod_orgao", "ano"], how="left").fillna(0.0)
    t["taxa"] = _razao(t["canc"], t["insc"])
    r["F19_Max_Cancel_RAP"] = t.groupby("cod_orgao")["taxa"].max()

    nomes = NOMES
    if regras == "v3":
        r = r.join(_indicadores_balanco(mov, sal, grade))
        nomes = NOMES_V3
    r = r[nomes].replace([np.inf, -np.inf], np.nan).fillna(0.0)
    r["F7_Qtd_Deficit_Fin"] = r["F7_Qtd_Deficit_Fin"].astype(int)
    return r.reset_index()


def _indicadores_balanco(mov: pd.DataFrame, sal: pd.DataFrame, grade: pd.DataFrame) -> pd.DataFrame:
    """
    F21 a F23, adaptados de Martins (2019), com os saldos de fim de exercício (mês 13).

    F21: média, entre os anos do período, da liquidez corrente (ativo circulante 1.1 / passivo circulante 2.1).
    F22: média, entre os anos do período, do imobilizado (1.2.3, líquido da depreciação) sobre o ativo total.
    F23: depreciação de bens móveis do período (VPD 3.3.3.1.1.01, meses 1 a 12) sobre a soma dos saldos
         de bens móveis (1.2.3.1.1) no fim de cada ano. Zero quando a universidade não registrou depreciação.
    """
    anos_univ = grade[["cod_orgao", "ano"]].drop_duplicates().set_index(["cod_orgao", "ano"]).index
    anos = sorted(anos_univ.get_level_values("ano").unique())
    fim = sal[(sal["mes"] == 13) & sal["ano"].isin(anos)]

    def saldo(prefixos):
        f = fim[fim["cod_conta"].str.startswith(prefixos)]
        return f.groupby(["cod_orgao", "ano"])["saldo"].sum().abs().reindex(anos_univ, fill_value=0.0)

    m = mov[mov["ano"].isin(anos) & mov["mes"].between(1, 12) & mov["cod_conta"].str.startswith("333110100")]
    # Total líquido do ano: estornos de depreciação reduzem o valor, e não o aumentam
    depreciacao = m.groupby(["cod_orgao", "ano"])["mov"].sum().abs().reindex(anos_univ, fill_value=0.0)

    liquidez = _razao(saldo("11"), saldo("21"))
    imobilizado = _razao(saldo("123"), saldo("1"))
    moveis = saldo("12311")
    return pd.DataFrame({
        "F21_Liquidez_Corrente": liquidez.groupby("cod_orgao").mean(),
        "F22_Imobilizado_Ativo": imobilizado.groupby("cod_orgao").mean(),
        "F23_Taxa_Deprec_Moveis": _razao(depreciacao.groupby("cod_orgao").sum(), moveis.groupby("cod_orgao").sum()),
    })


# ---------------------------------------------------------------------------------------------
# Desenho D: um registro por universidade e ano
# ---------------------------------------------------------------------------------------------
def _total_anual(mov: pd.DataFrame, prefixo: str) -> pd.Series:
    """Soma, no ano, do valor absoluto de cada mês (meses 1 a 12), como as séries v3 da VPA e da VPD."""
    m = mov[mov["mes"].between(1, 12) & mov["cod_conta"].str.startswith(prefixo)]
    return m.groupby(["cod_orgao", "ano", "mes"])["mov"].sum().abs().groupby(["cod_orgao", "ano"]).sum()


def calcular_indicadores_anuais(mov: pd.DataFrame, sal: pd.DataFrame, anos: list[int]) -> pd.DataFrame:
    """
    Indicadores do desenho D: uma linha por universidade e ano, com o valor do ano e a variação (Δ).

    Regras (D38, D39 e D44):
    - cada indicador é calculado com os 12 meses do ano, pelas regras v3;
    - F9 vira o resultado patrimonial do ano sobre a VPA do ano;
    - F11 vira o passivo circulante sobre o ativo no fim do ano (mês 13);
    - F16 vira o crescimento da VPD em relação ao ano anterior;
    - cada indicador ganha a coluna Delta_<nome>, diferença simples em relação ao ano anterior,
      menos F16 e F19.

    O ano anterior ao primeiro ano pedido também é calculado, só como base. Quando a universidade não
    tem o ano anterior na base, a F16 e as colunas Delta ficam vazias (NaN). As regras de inclusão do
    universo (UFNT, primeiro exercício das novas, desmembramentos) são aplicadas na montagem dos
    desenhos, e não aqui.
    """
    anos = sorted(anos)
    disponiveis = set(mov["ano"].unique())
    calculo = [a for a in [anos[0] - 1] + anos if a in disponiveis]

    niveis = []
    for ano in calculo:
        mov_ano = mov[mov["ano"].isin([ano - 1, ano])]  # o ano anterior entra só na F19
        r = calcular_indicadores(mov_ano, sal[sal["ano"] == ano], [ano], regras="v3")
        r.insert(1, "ano", ano)
        niveis.append(r)
    t = pd.concat(niveis, ignore_index=True).set_index(["cod_orgao", "ano"])

    # Versões anuais de F9, F11 e F16
    vpa = _total_anual(mov[mov["ano"].isin(calculo)], "4").reindex(t.index, fill_value=0.0)
    vpd = _total_anual(mov[mov["ano"].isin(calculo)], "3").reindex(t.index, fill_value=0.0)
    t["F9_Ang_RPE"] = _razao(vpa - vpd, vpa)

    fim = sal[(sal["mes"] == 13) & sal["ano"].isin(calculo)]
    def saldo(prefixo):
        f = fim[fim["cod_conta"].str.startswith(prefixo)]
        return f.groupby(["cod_orgao", "ano"])["saldo"].sum().abs().reindex(t.index, fill_value=0.0)
    t["F11_Ang_Passivo"] = _razao(saldo("21"), saldo("1"))

    vpd_todos = _total_anual(mov, "3")
    anterior = vpd_todos.rename(lambda a: a + 1, level="ano").reindex(t.index)  # VPD do ano anterior
    crescimento = _razao(vpd, anterior.fillna(0.0)) - 1
    t["F16_Ang_VPD"] = crescimento.where(anterior.notna() & (anterior != 0), np.nan)
    t.loc[anterior.notna() & (anterior == 0), "F16_Ang_VPD"] = 0.0
    t = t.rename(columns=NOMES_ANUAIS)

    # Δ: diferença simples em relação ao ano anterior (D39)
    com_delta = [c for c in t.columns if c not in SEM_DELTA]
    ano_anterior = t[com_delta].rename(lambda a: a + 1, level="ano").reindex(t.index)
    delta = (t[com_delta] - ano_anterior).add_prefix("Delta_")
    t = t.join(delta)

    t = t[t.index.get_level_values("ano").isin(anos)]
    return t.reset_index().sort_values(["ano", "cod_orgao"], ignore_index=True)
