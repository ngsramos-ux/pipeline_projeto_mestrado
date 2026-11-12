-- =============================================================================
-- DIAGNÓSTICO: A PARTIR DE QUE ANO OS DADOS TÊM A ESTRUTURA DO PCASP?
-- -----------------------------------------------------------------------------
-- Três consultas leves. Lembre de desligar o limite de linhas do SQuirrel.
-- Exporte cada resultado em CSV (diagnostico_3a.csv, 3b e 3c).
-- =============================================================================


-- -----------------------------------------------------------------------------
-- 3A. Quantidade de lançamentos por universidade e ano, de 2013 a 2017
-- (mesma lógica do diagnóstico 2, para os anos anteriores).
-- Objetivo: ver se há dados para as universidades antes de 2017.
-- -----------------------------------------------------------------------------
select	a15.ID_ORGAO_UG  ID_ORGAO,
	a11.ID_ANO_LANC,
	count(distinct a15.ID_UG)  QTD_UG,
	count(*)  QTD_LANCAMENTOS
from	WF_LANCAMENTO_EP04	a11
	join	WD_UG_EXERCICIO	a15
	  on 	(a11.ID_ANO_LANC = a15.ID_ANO and
	a11.ID_UG_EXEC = a15.ID_UG)
where	a11.ID_ANO_LANC between 2013 and 2017
 and a15.ID_ORGAO_UG in (26231, 26232, 26233, 26234, 26235, 26236, 26237, 26238, 26239, 26240, 26241, 26242, 26243, 26244, 26245, 26246, 26247, 26248, 26249, 26252, 26253, 26254, 26255, 26258, 26260, 26261, 26262, 26263, 26264, 26267, 26269, 26351, 26440, 26441, 26442, 26447, 26448, 26449, 26450, 26452, 26453, 26454, 26455, 26456, 26457)
group by	a15.ID_ORGAO_UG,
	a11.ID_ANO_LANC
order by	a15.ID_ORGAO_UG,
	a11.ID_ANO_LANC;


-- -----------------------------------------------------------------------------
-- 3B. Meses existentes e equação patrimonial (UFF, 2013 a 2017)
-- (mesma lógica do diagnóstico 1).
-- Objetivo: ver se cada ano tem mês 0 (abertura) e mês 13 (encerramento)
-- e se Ativo = Passivo + PL fecha no fim do ano, como em 2017 e 2024.
-- -----------------------------------------------------------------------------
select	a11.ID_ANO_LANC,
	a11.ID_MES_LANC,
	count(*)  QTD_LANCAMENTOS,
	sum(case when a17.ID_CLASSE_CCON = 1 then a11.VA_MOVIMENTO_LIQUIDO else 0 end)  SOMA_CLASSE_1,
	sum(case when a17.ID_CLASSE_CCON = 2 then a11.VA_MOVIMENTO_LIQUIDO else 0 end)  SOMA_CLASSE_2
from	WF_LANCAMENTO_EP04	a11
	join	WD_CONTA_CONTABIL_EXERCICIO	a14
	  on 	(a11.ID_ANO_LANC = a14.ID_ANO and
	a11.ID_CONTA_CONTABIL_LANC = a14.ID_CONTA_CONTABIL)
	join	WD_UG_EXERCICIO	a15
	  on 	(a11.ID_ANO_LANC = a15.ID_ANO and
	a11.ID_UG_EXEC = a15.ID_UG)
	join	WD_CONTA_CONTABIL	a17
	  on 	(a14.ID_CONTA_CONTABIL_DESTINO = a17.ID_CONTA_CONTABIL)
where	a11.ID_ANO_LANC between 2013 and 2017
 and a15.ID_ORGAO_UG = 26236
 and a17.ID_CLASSE_CCON in (1, 2)
group by	a11.ID_ANO_LANC,
	a11.ID_MES_LANC
order by	a11.ID_ANO_LANC,
	a11.ID_MES_LANC;


-- -----------------------------------------------------------------------------
-- 3C. Contas usadas pelos indicadores (UFF, 2013 a 2017)
-- Objetivo: ver se as contas que os indicadores usam existem em cada ano,
-- com valores de grandeza parecida. Se um grupo aparecer zerado ou com
-- valores muito diferentes antes de certo ano, a estrutura mudou.
-- Os intervalos supõem códigos de conta com 9 dígitos (ex.: 111122001).
-- Os valores são somas do movimento dos meses 1 a 12, com o sinal do SIAFI.
-- -----------------------------------------------------------------------------
select	a11.ID_ANO_LANC,
	count(distinct a14.ID_CONTA_CONTABIL_DESTINO)  QTD_CONTAS,
	sum(case when a14.ID_CONTA_CONTABIL_DESTINO between 300000000 and 399999999 then a11.VA_MOVIMENTO_LIQUIDO else 0 end)  CLASSE_3_VPD,
	sum(case when a14.ID_CONTA_CONTABIL_DESTINO between 400000000 and 499999999 then a11.VA_MOVIMENTO_LIQUIDO else 0 end)  CLASSE_4_VPA,
	sum(case when a14.ID_CONTA_CONTABIL_DESTINO between 112000000 and 112999999 then a11.VA_MOVIMENTO_LIQUIDO else 0 end)  CONTA_112_CREDITOS_CP,
	sum(case when a14.ID_CONTA_CONTABIL_DESTINO between 217000000 and 217999999 then a11.VA_MOVIMENTO_LIQUIDO else 0 end)  CONTA_217_PROVISOES_CP,
	sum(case when a14.ID_CONTA_CONTABIL_DESTINO between 230000000 and 239999999 then a11.VA_MOVIMENTO_LIQUIDO else 0 end)  CONTA_23_PL,
	sum(case when a14.ID_CONTA_CONTABIL_DESTINO between 621200000 and 621299999 then a11.VA_MOVIMENTO_LIQUIDO else 0 end)  CONTA_6212_RECEITA,
	sum(case when a14.ID_CONTA_CONTABIL_DESTINO between 622130000 and 622139999 then a11.VA_MOVIMENTO_LIQUIDO else 0 end)  CONTA_62213_DESPESA,
	sum(case when a14.ID_CONTA_CONTABIL_DESTINO between 821100000 and 821199999 then a11.VA_MOVIMENTO_LIQUIDO else 0 end)  CONTA_8211_DISPONIB
from	WF_LANCAMENTO_EP04	a11
	join	WD_CONTA_CONTABIL_EXERCICIO	a14
	  on 	(a11.ID_ANO_LANC = a14.ID_ANO and
	a11.ID_CONTA_CONTABIL_LANC = a14.ID_CONTA_CONTABIL)
	join	WD_UG_EXERCICIO	a15
	  on 	(a11.ID_ANO_LANC = a15.ID_ANO and
	a11.ID_UG_EXEC = a15.ID_UG)
where	a11.ID_ANO_LANC between 2013 and 2017
 and a11.ID_MES_LANC between 1 and 12
 and a15.ID_ORGAO_UG = 26236
group by	a11.ID_ANO_LANC
order by	a11.ID_ANO_LANC;
