-- =============================================================================
-- CONSULTAS DE DIAGNÓSTICO (rodar antes da extração completa)
-- São consultas leves, só com contagens e somas.
-- =============================================================================


-- -----------------------------------------------------------------------------
-- DIAGNÓSTICO 1: quais meses existem na tabela de lançamentos?
-- Objetivo: saber se há um "mês 0" (saldo de abertura do exercício) ou um
-- "mês 13" (encerramento). Isso define se o saldo pode ser reconstruído
-- somando os movimentos mês a mês.
-- Exemplo com a UFF (26236) em dois anos. As colunas mostram, por mês,
-- quantos lançamentos há e a soma do movimento nas classes 1 (Ativo) e 2 (Passivo e PL).
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
where	a11.ID_ANO_LANC in (2017, 2024)
 and a15.ID_ORGAO_UG = 26236
 and a17.ID_CLASSE_CCON in (1, 2)
group by	a11.ID_ANO_LANC,
	a11.ID_MES_LANC
order by	a11.ID_ANO_LANC,
	a11.ID_MES_LANC;


-- -----------------------------------------------------------------------------
-- DIAGNÓSTICO 2: a partir de que ano cada universidade tem lançamentos?
-- Objetivo: saber quantos anos de dados existem para cada uma das 45
-- universidades, sobretudo as criadas a partir de 2018 (26452 a 26457).
-- O resultado tem uma linha por universidade e por ano.
-- -----------------------------------------------------------------------------
select	a15.ID_ORGAO_UG  ID_ORGAO,
	a11.ID_ANO_LANC,
	count(distinct a15.ID_UG)  QTD_UG,
	count(*)  QTD_LANCAMENTOS
from	WF_LANCAMENTO_EP04	a11
	join	WD_UG_EXERCICIO	a15
	  on 	(a11.ID_ANO_LANC = a15.ID_ANO and
	a11.ID_UG_EXEC = a15.ID_UG)
where	a11.ID_ANO_LANC between 2017 and 2025
 and a15.ID_ORGAO_UG in (26231, 26232, 26233, 26234, 26235, 26236, 26237, 26238, 26239, 26240, 26241, 26242, 26243, 26244, 26245, 26246, 26247, 26248, 26249, 26252, 26253, 26254, 26255, 26258, 26260, 26261, 26262, 26263, 26264, 26267, 26269, 26351, 26440, 26441, 26442, 26447, 26448, 26449, 26450, 26452, 26453, 26454, 26455, 26456, 26457)
group by	a15.ID_ORGAO_UG,
	a11.ID_ANO_LANC
order by	a15.ID_ORGAO_UG,
	a11.ID_ANO_LANC;
