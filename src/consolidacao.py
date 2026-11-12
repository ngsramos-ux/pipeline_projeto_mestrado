"""
Consolidação dos arquivos brutos (2016 a 2025) numa base única.

Uso, a partir da pasta raiz do repositório, depois de rodar a conferência (src.qualidade):
    python -m src.consolidacao
    python -m src.consolidacao --brutos 00_extracao/dados_brutos --saida 01_conferencia_e_consolidacao/base_consolidada

A consolidação só roda se o relatório de qualidade existir e não tiver nenhuma FALHA.
Para rodar mesmo assim (não recomendado), use --forcar.

Arquivos gerados em 01_conferencia_e_consolidacao/base_consolidada:
    movimentos.parquet       movimento líquido mensal por universidade, UG, conta, GND e elemento
    saldos_mensais.parquet   saldo de cada conta no fim de cada mês, por universidade
    dimensoes.xlsx           nomes das universidades, UGs e contas
    LEIAME.md                descrição das colunas

A base é completa: nenhuma universidade ou ano é excluído aqui. As regras de inclusão
(UFNT fora, 2020 fora para as universidades novas etc.) são aplicadas na montagem de cada desenho.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from pandas.api.types import union_categoricals

from src.leitura import ler_ano, listar_arquivos

ZERO = 0.005  # valores menores que meio centavo são tratados como zero
MESES = list(range(0, 15))

LEIAME = """# Base consolidada (2016 a 2025)

Gerada por `python -m src.consolidacao` a partir dos arquivos de `00_extracao/dados_brutos`,
extraídos do Tesouro Gerencial com `00_extracao/sql/extracao_mestrado_v2.sql`. Valores em reais.

## movimentos.parquet

Movimento líquido mensal. Linhas com movimento igual a zero foram retiradas (não alteram nenhuma soma).

| Coluna | Descrição |
| --- | --- |
| ano | Exercício |
| mes | 0 = abertura, 1 a 12 = meses do ano, 13 = encerramento, 14 = mês adicional do SIAFI |
| cod_orgao | Código da universidade |
| cod_ug | Código da UG executora |
| cod_conta | Conta contábil do PCASP (9 dígitos, texto) |
| cod_gnd | Grupo de natureza de despesa (-9 = não se aplica) |
| cod_elemento | Elemento de despesa (-9 = não se aplica) |
| mov | Movimento líquido do mês, com o sinal do SIAFI |

## saldos_mensais.parquet

Saldo de cada conta no fim de cada mês, por universidade (somadas as UGs, GNDs e elementos).
Calculado como a soma acumulada do movimento a partir do mês 0, dentro de cada exercício,
da mesma forma que a métrica de saldo do Tesouro Gerencial. Linhas com saldo zero foram
retiradas: conta ausente num mês significa saldo zero.

| Coluna | Descrição |
| --- | --- |
| ano | Exercício |
| mes | Mês (0 a 14). O saldo do mês 13 é o saldo de fim de exercício, igual ao do Balanço Patrimonial |
| cod_orgao | Código da universidade |
| cod_conta | Conta contábil do PCASP |
| saldo | Saldo no fim do mês, com o sinal do SIAFI |

Regras de uso (diário de decisões, D25): indicadores de fluxo usam os meses 1 a 12; saldos
usam os meses 0 a 13.

## dimensoes.xlsx

Nomes das universidades (aba orgaos), das UGs (aba ugs) e das contas (aba contas), conforme o
ano mais recente em que aparecem.
"""


def _verificar_relatorio(pasta_qualidade: Path, forcar: bool) -> None:
    relatorio = pasta_qualidade / "relatorio_qualidade.xlsx"
    if not relatorio.exists():
        msg = f"Relatório de qualidade não encontrado em {relatorio.resolve()}. Rode antes: python -m src.qualidade"
        if forcar:
            print(f"AVISO: {msg}")
            return
        raise SystemExit(msg)
    resumo = pd.read_excel(relatorio, sheet_name="Resumo")
    falhas = resumo[resumo["status"] == "FALHA"]
    if len(falhas):
        msg = "O relatório de qualidade tem FALHA em: " + "; ".join(falhas["conferencia"])
        if forcar:
            print(f"AVISO: {msg}")
            return
        raise SystemExit(msg + ". Resolva antes de consolidar ou use --forcar.")
    print("Relatório de qualidade sem falhas. Iniciando a consolidação.\n")


def _saldos_do_ano(df: pd.DataFrame) -> pd.DataFrame:
    """Saldo no fim de cada mês = soma acumulada do movimento a partir do mês 0, por universidade e conta."""
    mensal = (df.groupby(["cod_orgao", "cod_conta", "mes"], observed=True)["mov"].sum()
              .unstack("mes").reindex(columns=MESES, fill_value=0.0).fillna(0.0))
    saldo = mensal.cumsum(axis=1)
    longo = saldo.stack().rename("saldo").reset_index()
    longo = longo[longo["saldo"].abs() >= ZERO]
    longo.insert(0, "ano", int(df["ano"].iloc[0]))
    return longo


def consolidar(pasta_brutos: str | Path, pasta_saida: str | Path,
               pasta_qualidade: str | Path, forcar: bool = False) -> None:
    _verificar_relatorio(Path(pasta_qualidade), forcar)
    arquivos = listar_arquivos(pasta_brutos)

    movimentos, saldos, orgaos, ugs, contas = [], [], [], [], []
    for ano, caminho in arquivos.items():
        print(f"Lendo {caminho.name} ...", end=" ", flush=True)
        df = ler_ano(caminho, com_nomes=True)
        total_bruto = df["mov"].sum()

        orgaos.append(df[["ano", "cod_orgao", "nome_orgao"]].drop_duplicates())
        ugs.append(df[["ano", "cod_ug", "cod_orgao", "nome_ug"]].drop_duplicates())
        contas.append(df[["ano", "cod_conta", "nome_conta"]].drop_duplicates())

        df = df.drop(columns=["nome_orgao", "nome_ug", "nome_conta"])
        df["cod_conta"] = df["cod_conta"].astype("category")
        saldos.append(_saldos_do_ano(df))

        df = df[df["mov"].abs() >= ZERO]
        df = df.astype({"ano": "int16", "mes": "int8", "cod_orgao": "int32", "cod_ug": "int32",
                        "cod_gnd": "int16", "cod_elemento": "int16"})
        # Conferência interna: retirar as linhas zeradas não muda o total
        if abs(df["mov"].sum() - total_bruto) > 1.0:
            raise SystemExit(f"{caminho.name}: o total mudou ao retirar linhas zeradas. Verifique o arquivo.")
        movimentos.append(df)
        print(f"{len(df):,} linhas com movimento".replace(",", "."))

    # Junta os anos mantendo a conta como categoria (economiza memória)
    categorias = union_categoricals([m["cod_conta"] for m in movimentos] + [s["cod_conta"] for s in saldos]).categories
    for tabela in movimentos + saldos:
        tabela["cod_conta"] = pd.Categorical(tabela["cod_conta"].astype(str), categories=categorias)
    mov = pd.concat(movimentos, ignore_index=True)
    sal = pd.concat(saldos, ignore_index=True).astype({"ano": "int16", "mes": "int8", "cod_orgao": "int32"})

    # Conferência interna: o saldo do último mês é a soma de todos os movimentos do ano
    ultimo = sal[sal["mes"] == max(MESES)].groupby(["ano", "cod_orgao"])["saldo"].sum()
    soma = mov.groupby(["ano", "cod_orgao"])["mov"].sum()
    dif = (ultimo.reindex(soma.index, fill_value=0.0) - soma).abs().max()
    if dif > 1.0:
        raise SystemExit(f"Saldos inconsistentes com os movimentos (diferença máxima de R$ {dif:,.2f}).")

    # Tabelas de nomes: fica o nome do ano mais recente
    def mais_recente(tabelas: list[pd.DataFrame], chave: list[str]) -> pd.DataFrame:
        t = pd.concat(tabelas, ignore_index=True).sort_values("ano")
        return t.drop_duplicates(chave, keep="last").drop(columns="ano").sort_values(chave)

    pasta_saida = Path(pasta_saida)
    pasta_saida.mkdir(parents=True, exist_ok=True)
    mov.to_parquet(pasta_saida / "movimentos.parquet", index=False, compression="zstd")
    sal.to_parquet(pasta_saida / "saldos_mensais.parquet", index=False, compression="zstd")
    with pd.ExcelWriter(pasta_saida / "dimensoes.xlsx") as w:
        mais_recente(orgaos, ["cod_orgao"]).to_excel(w, sheet_name="orgaos", index=False)
        mais_recente(ugs, ["cod_ug"]).to_excel(w, sheet_name="ugs", index=False)
        mais_recente(contas, ["cod_conta"]).to_excel(w, sheet_name="contas", index=False)
    (pasta_saida / "LEIAME.md").write_text(LEIAME, encoding="utf-8")

    print("\nBase consolidada:")
    for nome in ["movimentos.parquet", "saldos_mensais.parquet", "dimensoes.xlsx"]:
        tamanho = (pasta_saida / nome).stat().st_size / 1024 ** 2
        print(f"  {nome:28s} {tamanho:8.1f} MB")
    print(f"  movimentos: {len(mov):,} linhas | saldos: {len(sal):,} linhas".replace(",", "."))
    print(f"  anos: {sorted(mov['ano'].unique().tolist())} | universidades: {mov['cod_orgao'].nunique()}")
    print(f"\nArquivos gravados em {pasta_saida.resolve()}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Consolida os arquivos brutos numa base única.")
    parser.add_argument("--brutos", default="00_extracao/dados_brutos", help="Pasta com os arquivos anuais (.csv ou .zip)")
    parser.add_argument("--saida", default="01_conferencia_e_consolidacao/base_consolidada", help="Pasta onde a base será gravada")
    parser.add_argument("--qualidade", default="01_conferencia_e_consolidacao", help="Pasta do relatório de qualidade")
    parser.add_argument("--forcar", action="store_true", help="Consolida mesmo com falhas no relatório")
    args = parser.parse_args()
    consolidar(args.brutos, args.saida, args.qualidade, args.forcar)


if __name__ == "__main__":
    main()
