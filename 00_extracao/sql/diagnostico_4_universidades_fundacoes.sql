-- =============================================================================
-- DIAGNÓSTICO 4: DADOS DAS 24 UNIVERSIDADES FUNDAÇÕES
-- -----------------------------------------------------------------------------
-- A lista das 45 universidades da Versão 1 veio de um filtro pelo tipo
-- autarquia, que deixou de fora as 24 universidades constituídas como
-- fundação (Portaria-TCU nº 105/2026). Antes de decidir se elas entram,
-- estas duas consultas verificam se há dados de 2016 a 2025 e se eles têm a
-- mesma qualidade dos dados das 45.
--
-- As consultas não usam lista de códigos: pegam todos os órgãos do MEC
-- (26000 a 26999) com "UNIV" no nome. Assim saem as 69 universidades de uma
-- vez (as 45 servem de referência), e os códigos das 24 aparecem no resultado.
--
-- COMO USAR: rode cada consulta separadamente, com o limite de linhas do
-- SQuirrel desligado, e exporte em CSV com separador ponto e vírgula:
--   4A -> diagnostico_4a.csv   (leve: só contagens)
--   4B -> diagnostico_4b.csv   (mais pesada: somas por classe de contas)
-- Se a 4B demorar demais, troque o período na linha marcada com <<< ANOS
-- e rode em duas partes (2016 a 2020 e 2021 a 2025).
--
-- Se o SQuirrel acusar que alguma tabela não existe, acrescente o prefixo
-- MS_33393_DWTG_PRO. ao nome das tabelas (ex.: MS_33393_DWTG_PRO.WD_ORGAO).
-- =============================================================================


-- -----------------------------------------------------------------------------
-- 4A. Existência dos dados: universidade, ano, UGs, meses e lançamentos
-- (mesma lógica do diagnóstico 2, com o nome do órgão).
-- Objetivo: saber os códigos das 24 e desde que ano cada uma tem dados.
-- Uma queda no número de UGs mostra a saída de campi (UFT, UFMT e UFPI).
-- -----------------------------------------------------------------------------
select	a15.ID_ORGAO_UG  ID_ORGAO,
	max(a18.NO_ORGAO)  NO_ORGAO,
	a11.ID_ANO_LANC,
	count(distinct a15.ID_UG)  QTD_UG,
	count(distinct a11.ID_MES_LANC)  QTD_MESES,
	count(*)  QTD_LANCAMENTOS
from	WF_LANCAMENTO_EP04	a11
	join	WD_UG_EXERCICIO	a15
	  on 	(a11.ID_ANO_LANC = a15.ID_ANO and
	a11.ID_UG_EXEC = a15.ID_UG)
	join	WD_ORGAO	a18
	  on 	(a15.ID_ORGAO_UG = a18.ID_ORGAO)
where	a11.ID_ANO_LANC between 2016 and 2025
 and a15.ID_ORGAO_UG between 26000 and 26999
 and upper(a18.NO_ORGAO) like '%UNIV%'
group by	a15.ID_ORGAO_UG,
	a11.ID_ANO_LANC
order by	a15.ID_ORGAO_UG,
	a11.ID_ANO_LANC;


-- -----------------------------------------------------------------------------
-- 4B. Qualidade dos dados: somas por classe de contas, por universidade e ano
-- (mesma lógica dos diagnósticos 1 e 3B, para todas as universidades).
-- Objetivo: aplicar às 24 as conferências já feitas nas 45:
--   - equação patrimonial: ATIVO_FINAL = PASSIVO_PL_FINAL;
--   - encerramento: ENCERRAMENTO_PL (classe 2 no mês 13) = VPA - VPD;
--   - continuidade: ATIVO_FINAL de um ano = ATIVO_ABERTURA do ano seguinte;
--   - porte e completude (contas, meses 0 e 13, classes 6 e 8), comparados
--     com as 45.
-- As identidades foram conferidas nos valores de referência da UFF
-- (2016, 2017 e 2024), que fecham centavo a centavo.
-- Os saldos somam os meses 0 a 13; os fluxos (VPD e VPA), os meses 1 a 12.
-- -----------------------------------------------------------------------------
select	a15.ID_ORGAO_UG  ID_ORGAO,
	a11.ID_ANO_LANC,
	count(distinct a14.ID_CONTA_CONTABIL_DESTINO)  QTD_CONTAS,
	sum(case when a11.ID_MES_LANC = 0 then 1 else 0 end)  QTD_LANC_MES_0,
	sum(case when a11.ID_MES_LANC = 13 then 1 else 0 end)  QTD_LANC_MES_13,
	sum(case when a11.ID_MES_LANC = 14 then 1 else 0 end)  QTD_LANC_MES_14,
	sum(case when a17.ID_CLASSE_CCON = 1 and a11.ID_MES_LANC = 0 then a11.VA_MOVIMENTO_LIQUIDO else 0 end)  ATIVO_ABERTURA,
	sum(case when a17.ID_CLASSE_CCON = 2 and a11.ID_MES_LANC = 0 then a11.VA_MOVIMENTO_LIQUIDO else 0 end)  PASSIVO_PL_ABERTURA,
	sum(case when a17.ID_CLASSE_CCON = 1 and a11.ID_MES_LANC <= 13 then a11.VA_MOVIMENTO_LIQUIDO else 0 end)  ATIVO_FINAL,
	sum(case when a17.ID_CLASSE_CCON = 2 and a11.ID_MES_LANC <= 13 then a11.VA_MOVIMENTO_LIQUIDO else 0 end)  PASSIVO_PL_FINAL,
	sum(case when a17.ID_CLASSE_CCON = 3 and a11.ID_MES_LANC between 1 and 12 then a11.VA_MOVIMENTO_LIQUIDO else 0 end)  VPD,
	sum(case when a17.ID_CLASSE_CCON = 4 and a11.ID_MES_LANC between 1 and 12 then a11.VA_MOVIMENTO_LIQUIDO else 0 end)  VPA,
	sum(case when a17.ID_CLASSE_CCON = 2 and a11.ID_MES_LANC = 13 then a11.VA_MOVIMENTO_LIQUIDO else 0 end)  ENCERRAMENTO_PL,
	sum(case when a17.ID_CLASSE_CCON = 6 then 1 else 0 end)  QTD_LANC_CLASSE_6,
	sum(case when a17.ID_CLASSE_CCON = 8 then 1 else 0 end)  QTD_LANC_CLASSE_8
from	WF_LANCAMENTO_EP04	a11
	join	WD_CONTA_CONTABIL_EXERCICIO	a14
	  on 	(a11.ID_ANO_LANC = a14.ID_ANO and
	a11.ID_CONTA_CONTABIL_LANC = a14.ID_CONTA_CONTABIL)
	join	WD_UG_EXERCICIO	a15
	  on 	(a11.ID_ANO_LANC = a15.ID_ANO and
	a11.ID_UG_EXEC = a15.ID_UG)
	join	WD_CONTA_CONTABIL	a17
	  on 	(a14.ID_CONTA_CONTABIL_DESTINO = a17.ID_CONTA_CONTABIL)
	join	WD_ORGAO	a18
	  on 	(a15.ID_ORGAO_UG = a18.ID_ORGAO)
where	a11.ID_ANO_LANC between 2016 and 2025   -- <<< ANOS
 and a15.ID_ORGAO_UG between 26000 and 26999
 and upper(a18.NO_ORGAO) like '%UNIV%'
 and a17.ID_CLASSE_CCON in (1, 2, 3, 4, 6, 8)
group by	a15.ID_ORGAO_UG,
	a11.ID_ANO_LANC
order by	a15.ID_ORGAO_UG,
	a11.ID_ANO_LANC;
