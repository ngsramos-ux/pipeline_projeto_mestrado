# Diagnóstico 4: dados das universidades fundações

Data: 19/11/2026. Consultas: `diagnostico_4_universidades_fundacoes.sql` (4A e 4B), executadas no SQuirrel sobre o banco do Tesouro Gerencial. Decisão resultante: D51 do diário de decisões.

Arquivos nesta pasta: as consultas (`diagnostico_4_universidades_fundacoes.sql`), os resultados exportados do SQuirrel (`diagnostico_4a.csv` e `diagnostico_4b.csv`) e o script que faz as conferências abaixo (`diagnostico_4_analise.py`). Para refazer a análise, a partir da raiz do repositório: `python 00_extracao/sql/diagnostico_4_analise.py`.

## Por que foi feito

A lista das 45 universidades usada desde a Versão 1 veio de um filtro pelo tipo autarquia, que deixou de fora as 24 universidades constituídas como fundação. A Portaria-TCU nº 105/2026 relaciona 69 universidades federais (45 autarquias e 24 fundações). Antes de incluir as 24, era preciso saber se os dados delas existem de 2016 a 2025 e se têm a mesma qualidade dos dados das 45.

## O que as consultas fazem

As duas consultas selecionam todos os órgãos do MEC (códigos 26000 a 26999) com "UNIV" no nome, de modo que as 69 universidades saem juntas e as 45 servem de referência.

- **4A** conta, por universidade e ano, as UGs, os meses com lançamentos e o total de lançamentos.
- **4B** soma o movimento por classe de contas, por universidade e ano. Com essas somas, aplicam-se às 24 as conferências já feitas nas 45: Ativo igual a Passivo mais PL na abertura e no fim do ano (meses 0 a 13); encerramento do mês 13 (classe 2) igual a VPA menos VPD (meses 1 a 12); e saldo final de um ano igual à abertura do ano seguinte. As três igualdades foram antes conferidas nos valores de referência da UFF (2016, 2017 e 2024), que fecham ao centavo.

## Resultados

| Conferência | Resultado |
| --- | --- |
| Órgãos encontrados | 70: as 45 da lista atual, as 24 fundações e o órgão 26257 (ver pontos de atenção) |
| A consulta reproduz a base consolidada? | Sim. Nas 45 universidades (426 registros de universidade e ano), ativo, passivo e PL, VPD, VPA e abertura batem com a base, com diferença máxima abaixo de R$ 0,000001 |
| Anos e meses | As 24 têm os 10 anos (2016 a 2025), com os meses 0 a 13 em todos. Nenhuma universidade tem lançamento no mês 14 |
| Igualdades contábeis (tolerância de R$ 0,05) | Nenhuma diferença nos 240 registros das 24 |
| Completude | Medianas anuais parecidas: 380 contas nas 24 e 397 nas 45; 41 lançamentos por R$ 1 milhão de VPD nos dois grupos; 79% e 78% dos lançamentos nas classes 6 e 8. Nenhuma das 24 fica fora da faixa das 45 no número de contas ou de lançamentos de abertura e de encerramento. Os poucos registros fora da faixa em outras medidas se explicam pelos picos de VPD (item 1 dos pontos de atenção), pela UFCSPA, com proporção nas classes 6 e 8 até 1 ponto acima do máximo das 45, e pela UNIFAP em 2020, com número de lançamentos 1% abaixo do mínimo das 45 |
| Porte | As 24 se espalham pela distribuição das 69: em VPD de 2025, vão da UnB (5ª maior) à UFCSPA (57ª) |

As 24 universidades e os códigos de órgão no SIAFI:

| Código | Universidade | Código | Universidade |
| --- | --- | --- | --- |
| 26230 | UNIVASF | 26276 | UFMT |
| 26250 | UFRR | 26277 | UFOP |
| 26251 | UFT | 26278 | UFPel |
| 26266 | UNIPAMPA | 26279 | UFPI |
| 26268 | UNIR | 26280 | UFSCar |
| 26270 | UFAM | 26281 | UFS |
| 26271 | UnB | 26282 | UFV |
| 26272 | UFMA | 26283 | UFMS |
| 26273 | FURG | 26284 | UFCSPA |
| 26274 | UFU | 26285 | UFSJ |
| 26275 | UFAC | 26286 | UNIFAP |
| 26350 | UFGD | 26352 | UFABC |

## Pontos de atenção

Nenhum dos pontos abaixo é falha de qualidade, porque as igualdades contábeis fecham em todos os anos.

1. **Picos de VPD em anos isolados.** Cinco anos têm VPD acima de duas vezes a mediana dos demais anos da própria universidade: UnB em 2016 (R$ 8,6 bilhões, contra R$ 2,2 a 3,2 bilhões nos demais anos), UFOP em 2016 (R$ 2,2 bilhões, contra R$ 0,4 a 1,0 bilhão), UFMA em 2017 (R$ 3,5 bilhões, contra R$ 1,0 a 1,6 bilhão), UFAM em 2023 (R$ 2,1 bilhões, contra R$ 0,8 a 1,4 bilhão) e UFABC em 2023 (R$ 0,9 bilhão, contra R$ 0,2 a 0,5 bilhão). São eventos do tipo que os modelos devem apontar. Como 2016 é só ano base, os picos da UnB e da UFOP aparecem na variação de 2017 do desenho D.
2. **Saída de campi para universidades novas.** A UFPI teve queda de 29% na VPD em 2020, ano de início da UFDPar, contra queda mediana de 13% nas universidades antigas (sem UFG e UFRPE, que também perderam campi); a quebra é de 2019 para 2020, como na UFRPE. A UFMT teve quedas de 17% em 2020 e de 9% em 2021, enquanto a mediana caiu 13% em 2020 e subiu 3% em 2021, e as UGs passaram de 3 para 2 em 2021; a quebra fica entre 2020 e 2021. Na UFT, a transição para a UFNT foi gradual: depois de alta de 47% em 2022, a VPD caiu 18% em 2023 e 12% em 2024, enquanto a mediana subiu cerca de 7% em cada ano. Os anos de transição serão definidos com a mesma regra da D41.
3. **Órgão 26257.** Aparece com o nome de Universidade Federal de Ciência e Inovação de Minas Gerais. É o antigo CEFET-MG, transformado em universidade pela Lei nº 15.521, de 24/09/2026, segundo notícia da imprensa (a confirmar no texto oficial). Na lista de UPCs de 2026 ainda consta como CEFET (categoria 4), e de 2016 a 2025 não era universidade. Fica fora do universo.

## Conclusões

Os dados das 24 universidades fundações existem para todo o período e têm a mesma qualidade dos dados das 45. Por isso, elas foram incluídas no universo (D51), que passa a ter 69 universidades: 68 na análise principal (sem a UFNT) e 63 na versão balanceada (as 39 antigas e as 24).

A inclusão ainda depende de três passos: extrair os dados das 24 de 2016 a 2025, sem alterar os arquivos já conferidos das 45; rodar de novo as etapas 1 e 2, com as listas de universidades, as contagens esperadas e as regras de desmembramento atualizadas; e definir os anos de transição da UFPI, da UFMT e da UFT.
