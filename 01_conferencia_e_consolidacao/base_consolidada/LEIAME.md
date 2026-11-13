# Base consolidada (2016 a 2025)

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
