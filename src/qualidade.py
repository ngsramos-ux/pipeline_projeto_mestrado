"""
Conferência de qualidade dos arquivos brutos (2016 a 2025).

Uso, a partir da pasta raiz do repositório:
    python -m src.qualidade
    python -m src.qualidade --brutos 00_extracao/dados_brutos --saida 01_conferencia_e_consolidacao

Gera 01_conferencia_e_consolidacao/relatorio_qualidade.xlsx, com uma aba de resumo e uma aba por
conferência, e imprime o resumo na tela. Nenhum arquivo bruto é alterado.

Status usados:
    OK       a conferência passou
    ATENÇÃO  há diferenças esperadas ou que precisam ser olhadas, mas não impedem seguir
    FALHA    há um problema que precisa ser resolvido antes da consolidação
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src.leitura import COLUNAS_DADOS, ler_ano, ler_cabecalho, listar_arquivos

TOLERANCIA = 0.05  # diferença máxima aceita, em reais, nas igualdades contábeis

UNIVERSIDADES_ANTIGAS = [
    26231, 26232, 26233, 26234, 26235, 26236, 26237, 26238, 26239, 26240, 26241, 26242, 26243,
    26244, 26245, 26246, 26247, 26248, 26249, 26252, 26253, 26254, 26255, 26258, 26260, 26261,
    26262, 26263, 26264, 26267, 26269, 26351, 26440, 26441, 26442, 26447, 26448, 26449, 26450,
]
UNIVERSIDADES_NOVAS = [26452, 26453, 26454, 26455, 26456, 26457]  # dados a partir de 2020
ANO_INICIO_NOVAS = 2020
CLASSES_ESPERADAS = {"1", "2", "3", "4", "6", "8"}
MESES_VALIDOS = set(range(0, 15))

# Valores de referência dos diagnósticos SQL feitos sem a tabela de câmbio (UFF, código 26236).
# Diagnósticos 1 e 3B: soma do movimento das classes 1 e 2 por mês.
UFF = 26236
REF_UFF_CLASSES = {
    2016: {0: (1322316153.02, 1322316153.02), 1: (1752476.03, -1252485.97), 2: (-9533093.94, -9487471.56), 3: (9137804.12, 22443650.86), 4: (16890435.52, -8147383.24), 5: (18209298.68, 264600.14), 6: (38904627.39, 49176251.75), 7: (1990193.01, 2794880.56), 8: (8119440.26, 9354789.09), 9: (6159672.65, -9484407.72), 10: (2361526.86, 18054774.08), 11: (25029721.96, 14455045.82), 12: (-39238789.48, -68762131.45), 13: (0.00, 60373200.70)},
    2017: {0: (1402099466.08, 1402099466.08), 1: (-142419236.87, -31427433.08), 2: (-2288214.16, -2684351.87), 3: (16079279.40, -1411477.01), 4: (1992033.37, 11680414.09), 5: (-1768799.15, 24978706.41), 6: (22142152.28, 20023741.77), 7: (1451963.89, 9268376.49), 8: (-10484263.97, -13516646.01), 9: (-35530838.80, -12208253.23), 10: (-1410376.92, 10614354.17), 11: (27094859.59, -6941621.43), 12: (-20699324.58, -99661399.46), 13: (0.00, -54555176.76)},
    2024: {0: (2401236943.63, 2401236943.63), 1: (-9151196.83, -19032500.98), 2: (-5824203.20, 10932260.28), 3: (7708439.86, 18380468.11), 4: (17187884.22, 20584317.06), 5: (56990893.16, 26920005.34), 6: (125430741.93, 36482657.84), 7: (-87853416.95, -61919407.99), 8: (25364942.46, 25874911.05), 9: (8864518.76, 14069775.00), 10: (-7353535.09, 7333356.53), 11: (47219831.09, 67787273.78), 12: (4287450.24, -149981711.45), 13: (0.00, 185440945.08)},
}
# Diagnóstico 3C: soma do movimento dos meses 1 a 12 por grupo de contas.
REF_UFF_GRUPOS = {
    2016: {"3": 2506888184.80, "4": 2567261385.50, "112": 0.00, "217": 0.00, "23": -2014865.16,
           "6212": 30727165.34, "62213": 2055935988.38, "8211": 2033287409.44},
    2017: {"3": 3001061250.29, "4": 2946506073.53, "112": 38473.02, "217": 0.00, "23": -46868386.45,
           "6212": 26539699.40, "62213": 2316989181.97, "8211": 2330159906.09},
}


def _status(problemas: int, atencao: int = 0) -> str:
    if problemas > 0:
        return "FALHA"
    if atencao > 0:
        return "ATENÇÃO"
    return "OK"


# ---------------------------------------------------------------------------------------------
# Conferências de cada arquivo
# ---------------------------------------------------------------------------------------------
def conferir_arquivo(ano: int, caminho: Path, df: pd.DataFrame, cabecalho_ref: list[str]) -> dict:
    cabecalho = ler_cabecalho(caminho)
    faltando = [c for c in COLUNAS_DADOS if c not in cabecalho]
    esperadas = set(UNIVERSIDADES_ANTIGAS) | (set(UNIVERSIDADES_NOVAS) if ano >= ANO_INICIO_NOVAS else set())
    presentes = set(df["cod_orgao"].dropna().astype(int))
    meses = set(df["mes"].dropna().astype(int))
    chave = ["ano", "mes", "cod_orgao", "cod_ug", "cod_conta", "cod_gnd", "cod_elemento"]
    return {
        "ano": ano,
        "arquivo": caminho.name,
        "linhas": len(df),
        "colunas_necessarias_faltando": ", ".join(faltando),
        "cabecalho_igual_ao_primeiro_ano": cabecalho == cabecalho_ref,
        "anos_no_arquivo": ", ".join(str(int(a)) for a in sorted(df["ano"].dropna().unique())),
        "meses_presentes": ", ".join(str(m) for m in sorted(meses)),
        "meses_fora_de_0_a_14": ", ".join(str(m) for m in sorted(meses - MESES_VALIDOS)),
        "universidades": len(presentes),
        "universidades_faltando": ", ".join(str(u) for u in sorted(esperadas - presentes)),
        "universidades_inesperadas": ", ".join(str(u) for u in sorted(presentes - esperadas)),
        "valores_nao_numericos": int(df[["mov"] + [c for c in chave if c != "cod_conta"]].isna().sum().sum()),
        "contas_fora_do_padrao_9_digitos": int((~df["cod_conta"].str.fullmatch(r"\d{9}")).sum()),
        "classes_inesperadas": ", ".join(sorted(set(df["cod_conta"].str[0]) - CLASSES_ESPERADAS)),
        "linhas_duplicadas": int(df.duplicated(chave).sum()),
        "linhas_mes_14": int((df["mes"] == 14).sum()),
    }


def _status_arquivo(linha: dict) -> str:
    falhas = sum([
        bool(linha["colunas_necessarias_faltando"]),
        linha["anos_no_arquivo"] != str(linha["ano"]),
        bool(linha["meses_fora_de_0_a_14"]),
        bool(linha["universidades_faltando"]),
        linha["valores_nao_numericos"] > 0,
        linha["contas_fora_do_padrao_9_digitos"] > 0,
        bool(linha["classes_inesperadas"]),
        linha["linhas_duplicadas"] > 0,
    ])
    atencao = sum([not linha["cabecalho_igual_ao_primeiro_ano"], bool(linha["universidades_inesperadas"])])
    return _status(falhas, atencao)


# ---------------------------------------------------------------------------------------------
# Conferências contábeis por universidade e ano
# ---------------------------------------------------------------------------------------------
def conferir_universidades(ano: int, df: pd.DataFrame) -> pd.DataFrame:
    d = df.assign(classe=df["cod_conta"].str[0])
    soma = d.pivot_table(index=["cod_orgao", "mes"], columns="classe", values="mov",
                         aggfunc="sum", fill_value=0.0)
    for c in ["1", "2", "3", "4"]:
        if c not in soma.columns:
            soma[c] = 0.0
    linhas = []
    for orgao, s in soma.groupby(level="cod_orgao"):
        s = s.droplevel("cod_orgao").sort_index()
        meses = set(s.index.astype(int))
        ate13 = s.loc[s.index <= 13]
        abertura = s.loc[0, "1"] - s.loc[0, "2"] if 0 in meses else np.nan
        fech13 = ate13["1"].sum() - ate13["2"].sum()
        fech_final = s["1"].sum() - s["2"].sum()
        vpd_fim, vpa_fim = s["3"].sum(), s["4"].sum()
        meses_mov = sorted(m for m in meses if 1 <= m <= 12)
        # No primeiro ano das universidades novas, a falta do mês 0 é esperada (não havia saldo anterior)
        primeiro_ano_nova = int(orgao) in UNIVERSIDADES_NOVAS and ano == ANO_INICIO_NOVAS
        atencao = int(primeiro_ano_nova and 0 not in meses)
        problemas = sum([
            0 not in meses and not primeiro_ano_nova,
            13 not in meses,
            not np.isnan(abertura) and abs(abertura) > TOLERANCIA,
            abs(fech_final) > TOLERANCIA,
            abs(vpd_fim) > TOLERANCIA,
            abs(vpa_fim) > TOLERANCIA,
        ])
        linhas.append({
            "ano": ano,
            "cod_orgao": int(orgao),
            "tem_mes_0": 0 in meses,
            "tem_mes_13": 13 in meses,
            "meses_1_a_12_com_movimento": len(meses_mov),
            "primeiro_mes_com_movimento": meses_mov[0] if meses_mov else np.nan,
            "abertura_ativo_menos_passivo_pl": round(abertura, 2),
            "fechamento_ate_mes_13": round(fech13, 2),
            "fechamento_final": round(fech_final, 2),
            "vpd_acumulada_fim": round(vpd_fim, 2),
            "vpa_acumulada_fim": round(vpa_fim, 2),
            "status": _status(problemas, atencao),
        })
    return pd.DataFrame(linhas)


# ---------------------------------------------------------------------------------------------
# Saldos de fechamento e de abertura (classes 1 e 2), para a continuidade entre anos
# ---------------------------------------------------------------------------------------------
def saldos_patrimoniais(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Devolve (abertura no mês 0, fechamento depois de todos os meses) por universidade e conta."""
    d = df[df["cod_conta"].str[0].isin(["1", "2"])]
    abertura = d[d["mes"] == 0].groupby(["cod_orgao", "cod_conta"])["mov"].sum()
    fechamento = d.groupby(["cod_orgao", "cod_conta"])["mov"].sum()
    return abertura, fechamento


def conferir_continuidade(saldos: dict[int, tuple[pd.Series, pd.Series]]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compara o fechamento de cada ano com a abertura do ano seguinte."""
    por_grupo, por_conta = [], []
    anos = sorted(saldos)
    for ano, seguinte in zip(anos[:-1], anos[1:]):
        if seguinte != ano + 1:
            continue
        fech = saldos[ano][1].rename("fechamento_ano")
        aber = saldos[seguinte][0].rename("abertura_ano_seguinte")
        # Só universidades presentes nos dois anos (as novas não têm ano anterior)
        comuns = set(fech.index.get_level_values("cod_orgao")) & set(aber.index.get_level_values("cod_orgao"))
        fech = fech[fech.index.get_level_values("cod_orgao").isin(comuns)]
        aber = aber[aber.index.get_level_values("cod_orgao").isin(comuns)]
        junto = pd.concat([fech, aber], axis=1).fillna(0.0).reset_index()
        junto["diferenca"] = junto["abertura_ano_seguinte"] - junto["fechamento_ano"]
        junto.insert(0, "ano", ano)
        # Nível de classe (1 = Ativo, 2 = Passivo e PL) e de grupo de 3 dígitos
        for nivel, tamanho in [("classe", 1), ("grupo", 3)]:
            g = (junto.assign(codigo=junto["cod_conta"].str[:tamanho])
                 .groupby(["ano", "cod_orgao", "codigo"])[["fechamento_ano", "abertura_ano_seguinte", "diferenca"]]
                 .sum().reset_index())
            g.insert(2, "nivel", nivel)
            por_grupo.append(g)
        contas = junto[junto["diferenca"].abs() > TOLERANCIA]
        por_conta.append(contas)
    grupos = pd.concat(por_grupo, ignore_index=True).round(2) if por_grupo else pd.DataFrame()
    contas = pd.concat(por_conta, ignore_index=True).round(2) if por_conta else pd.DataFrame()
    return grupos, contas


# ---------------------------------------------------------------------------------------------
# Confronto com os diagnósticos SQL (UFF)
# ---------------------------------------------------------------------------------------------
def conferir_diagnosticos(ano: int, df: pd.DataFrame) -> list[dict]:
    linhas = []
    u = df[df["cod_orgao"] == UFF]
    if ano in REF_UFF_CLASSES:
        classe = u["cod_conta"].str[0]
        for mes, (ref1, ref2) in REF_UFF_CLASSES[ano].items():
            for c, ref in (("1", ref1), ("2", ref2)):
                valor = u.loc[(u["mes"] == mes) & (classe == c), "mov"].sum()
                linhas.append({"ano": ano, "conferencia": f"Classe {c}, mês {mes}",
                               "extracao": round(valor, 2), "diagnostico": ref,
                               "diferenca": round(valor - ref, 2)})
    if ano in REF_UFF_GRUPOS:
        meses = u[u["mes"].between(1, 12)]
        for prefixo, ref in REF_UFF_GRUPOS[ano].items():
            valor = meses.loc[meses["cod_conta"].str.startswith(prefixo), "mov"].sum()
            linhas.append({"ano": ano, "conferencia": f"Contas {prefixo}*, meses 1 a 12",
                           "extracao": round(valor, 2), "diagnostico": ref,
                           "diferenca": round(valor - ref, 2)})
    return linhas


# ---------------------------------------------------------------------------------------------
# Execução
# ---------------------------------------------------------------------------------------------
def conferir(pasta_brutos: str | Path, pasta_saida: str | Path) -> pd.DataFrame:
    arquivos = listar_arquivos(pasta_brutos)
    print(f"Arquivos encontrados: {', '.join(p.name for p in arquivos.values())}\n")
    cabecalho_ref = ler_cabecalho(next(iter(arquivos.values())))

    tab_arquivos, tab_univ, tab_diag, saldos, volume = [], [], [], {}, []
    for ano, caminho in arquivos.items():
        print(f"Lendo {caminho.name} ...", end=" ", flush=True)
        df = ler_ano(caminho)
        linha = conferir_arquivo(ano, caminho, df, cabecalho_ref)
        linha["status"] = _status_arquivo(linha)
        tab_arquivos.append(linha)
        tab_univ.append(conferir_universidades(ano, df))
        tab_diag.extend(conferir_diagnosticos(ano, df))
        saldos[ano] = saldos_patrimoniais(df)
        volume.append(df.groupby("cod_orgao").size().rename(ano))
        print(f"{len(df):,} linhas".replace(",", ".") + f" | status do arquivo: {linha['status']}")
        del df

    arquivos_df = pd.DataFrame(tab_arquivos)
    univ_df = pd.concat(tab_univ, ignore_index=True)
    diag_df = pd.DataFrame(tab_diag)
    grupos_df, contas_df = conferir_continuidade(saldos)
    volume_df = pd.concat(volume, axis=1).fillna(0).astype(int)
    volume_df.index.name = "cod_orgao"
    volume_df = volume_df.reset_index()

    novas = univ_df[univ_df["cod_orgao"].isin(UNIVERSIDADES_NOVAS)][
        ["ano", "cod_orgao", "tem_mes_0", "meses_1_a_12_com_movimento", "primeiro_mes_com_movimento"]]

    # Anos faltando na sequência
    anos = sorted(arquivos)
    anos_faltando = sorted(set(range(anos[0], anos[-1] + 1)) - set(anos))

    # Resumo
    classe_cont = grupos_df[grupos_df["nivel"] == "classe"] if len(grupos_df) else grupos_df
    grupo_cont = grupos_df[grupos_df["nivel"] == "grupo"] if len(grupos_df) else grupos_df
    n_classe_dif = int((classe_cont["diferenca"].abs() > TOLERANCIA).sum()) if len(classe_cont) else 0
    n_grupo_dif = int((grupo_cont["diferenca"].abs() > TOLERANCIA).sum()) if len(grupo_cont) else 0
    n_diag_dif = int((diag_df["diferenca"].abs() > TOLERANCIA).sum()) if len(diag_df) else 0
    resumo = pd.DataFrame([
        {"conferencia": "Sequência de anos", "status": _status(len(anos_faltando)),
         "verificados": f"{anos[0]} a {anos[-1]} ({len(anos)} arquivos)",
         "com_problema": len(anos_faltando),
         "observacao": f"Anos faltando: {anos_faltando}" if anos_faltando else ""},
        {"conferencia": "Estrutura dos arquivos (colunas, ano, meses, universidades, tipos, contas, duplicadas)",
         "status": _status(int((arquivos_df["status"] == "FALHA").sum()), int((arquivos_df["status"] == "ATENÇÃO").sum())),
         "verificados": len(arquivos_df), "com_problema": int((arquivos_df["status"] != "OK").sum()),
         "observacao": "Ver aba Arquivos"},
        {"conferencia": "Igualdades contábeis por universidade e ano (abertura, fechamento, VPA e VPD zeradas)",
         "status": _status(int((univ_df["status"] == "FALHA").sum()), int((univ_df["status"] == "ATENÇÃO").sum())),
         "verificados": len(univ_df), "com_problema": int((univ_df["status"] != "OK").sum()),
         "observacao": "Ver aba Universidade_ano"},
        {"conferencia": "Continuidade entre anos: total de Ativo e de Passivo + PL",
         "status": _status(n_classe_dif), "verificados": len(classe_cont), "com_problema": n_classe_dif,
         "observacao": "Fechamento de um ano contra abertura do seguinte. Ver aba Continuidade_grupos"},
        {"conferencia": "Continuidade entre anos: grupos de contas (3 dígitos)",
         "status": _status(0, n_grupo_dif), "verificados": len(grupo_cont), "com_problema": n_grupo_dif,
         "observacao": "Diferenças com total igual indicam reclassificação de contas na abertura"},
        {"conferencia": "Continuidade entre anos: contas individuais",
         "status": _status(0, len(contas_df)), "verificados": "", "com_problema": len(contas_df),
         "observacao": "Informativo. Ver aba Continuidade_contas"},
        {"conferencia": "Confronto com os diagnósticos SQL (UFF)",
         "status": _status(n_diag_dif) if len(diag_df) else "ATENÇÃO",
         "verificados": len(diag_df), "com_problema": n_diag_dif,
         "observacao": "Valores calculados sem a tabela de câmbio" if len(diag_df) else "Nenhum ano de referência encontrado"},
    ])

    pasta_saida = Path(pasta_saida)
    pasta_saida.mkdir(parents=True, exist_ok=True)
    destino = pasta_saida / "relatorio_qualidade.xlsx"
    with pd.ExcelWriter(destino) as w:
        resumo.to_excel(w, sheet_name="Resumo", index=False)
        arquivos_df.to_excel(w, sheet_name="Arquivos", index=False)
        univ_df.to_excel(w, sheet_name="Universidade_ano", index=False)
        grupos_df.to_excel(w, sheet_name="Continuidade_grupos", index=False)
        contas_df.head(50000).to_excel(w, sheet_name="Continuidade_contas", index=False)
        diag_df.to_excel(w, sheet_name="Diagnosticos", index=False)
        novas.to_excel(w, sheet_name="Novas_universidades", index=False)
        volume_df.to_excel(w, sheet_name="Linhas_por_universidade", index=False)

    print("\n" + "=" * 90)
    print("RESUMO DA CONFERÊNCIA")
    print("=" * 90)
    for r in resumo.itertuples():
        print(f"[{r.status:^7}] {r.conferencia} | com problema: {r.com_problema}")
    print("=" * 90)
    print(f"Relatório completo: {destino.resolve()}")
    return resumo


def main() -> None:
    parser = argparse.ArgumentParser(description="Conferência de qualidade dos arquivos brutos.")
    parser.add_argument("--brutos", default="00_extracao/dados_brutos", help="Pasta com os arquivos anuais (.csv ou .zip)")
    parser.add_argument("--saida", default="01_conferencia_e_consolidacao", help="Pasta onde o relatório será gravado")
    args = parser.parse_args()
    conferir(args.brutos, args.saida)


if __name__ == "__main__":
    main()
