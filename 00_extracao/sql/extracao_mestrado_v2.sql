-- =============================================================================
-- EXTRAÇÃO MESTRADO V2: movimento líquido mensal, 45 universidades federais
-- -----------------------------------------------------------------------------
-- Baseada na consulta usada na Versão 1, com quatro mudanças:
--   1) Todos os meses do exercício, inclusive 000 (abertura), 013
--      (encerramento) e 014. O mês 000 é necessário para calcular os saldos,
--      e o 013 para fechar o patrimônio líquido no fim do ano.
--   2) Retirada a métrica de variação cambial (não é usada no pipeline).
--   3) Retirado o filtro de órgão superior (26000). A lista das 45
--      universidades já restringe a consulta, e o filtro só poderia
--      descartar dados se o órgão superior mudasse em algum ano.
--   4) Um ano por execução, para gerar um arquivo por ano.
--
-- O saldo não é extraído: ele é calculado no Python como a soma acumulada do
-- movimento líquido a partir do mês 000. Esse cálculo foi conferido no teste
-- da UFF (2024, grupo 1.1.1) e bate centavo a centavo com a métrica
-- "Saldo - R$ (Conta Contábil)" do Tesouro Gerencial.
--
-- COMO USAR: troque o ano na linha marcada com <<< ANO e rode uma vez para
-- cada ano de 2016 a 2025 (10 execuções). Comece por 2016 e envie o arquivo
-- para conferência antes de rodar os demais. Exporte cada resultado como
-- extracao_mestrado_AAAA.csv, com as mesmas opções de exportação usadas na
-- Versão 1 (separador ponto e vírgula), e com o limite de linhas do
-- SQuirrel desligado.
--
-- Se o SQuirrel acusar que alguma tabela não existe, acrescente o prefixo
-- MS_33393_DWTG_PRO. ao nome das tabelas (ex.: MS_33393_DWTG_PRO.WD_MES).
-- =============================================================================

select	pa11.ID_ANO_LANC  ID_ANO_LANC,
	pa11.ID_MES_LANC  ID_MES_LANC,
	max(a16.SG_MES_COMPLETO)  SG_MES_COMPLETO,
	pa11.ID_ORGAO_SUPE  ID_ORGAO_SUPE,
	max(a19.CO_ORGAO_SUPE)  CO_ORGAO_SUPE,
	max(a19.NO_ORGAO_SUPE)  NO_ORGAO_SUPE,
	pa11.ID_ORGAO  ID_ORGAO,
	max(a18.CO_ORGAO)  CO_ORGAO,
	max(a18.NO_ORGAO)  NO_ORGAO,
	pa11.ID_UG_EXEC  ID_UG_EXEC,
	max(a17.CO_UG)  CO_UG,
	max(a17.NO_UG)  NO_UG,
	pa11.ID_CONTA_CONTABIL  ID_CONTA_CONTABIL,
	max(a13.NO_CONTA_CONTABIL)  NO_CONTA_CONTABIL,
	pa11.ID_GRUPO_DESPESA_NADE  ID_GRUPO_DESPESA_NADE,
	max(a15.NO_GRUPO_DESPESA_NADE)  NO_GRUPO_DESPESA_NADE,
	pa11.ID_ELEMENTO_DESPESA_NADE  ID_ELEMENTO_DESPESA_NADE,
	max(a14.CO_ELEMENTO_DESPESA_NADE)  CO_NATUREZA_DESPESA,
	max(a14.NO_ELEMENTO_DESPESA_NADE)  NO_NATUREZA_DESPESA,
	max(pa11.MOVIMLQUIDONOMSRCONTACONTBIL)  MOVIMLQUIDONOMSRCONTACONTBIL
from	(select	a16.ID_ORGAO_SUPE  ID_ORGAO_SUPE,
		a15.ID_ORGAO_UG  ID_ORGAO,
		a15.ID_UG  ID_UG_EXEC,
		a11.ID_ANO_LANC  ID_ANO_LANC,
		a11.ID_MES_LANC  ID_MES_LANC,
		a11.ID_GRUPO_DESPESA_NADE  ID_GRUPO_DESPESA_NADE,
		a11.ID_ELEMENTO_DESPESA_NADE  ID_ELEMENTO_DESPESA_NADE,
		a14.ID_CONTA_CONTABIL_DESTINO  ID_CONTA_CONTABIL,
		sum((a11.VA_MOVIMENTO_LIQUIDO * a13.PE_TAXA))  MOVIMLQUIDONOMSRCONTACONTBIL
	from	WF_LANCAMENTO_EP04	a11
		join	WD_MOEDA	a12
		  on 	(a11.ID_MOEDA_UG_EXEC_H = a12.ID_MOEDA)
		join	WD_TAXA_CAMBIO_MENSAL	a13
		  on 	(a12.ID_MOEDA = a13.ID_MOEDA_ORIGEM)
		join	WD_CONTA_CONTABIL_EXERCICIO	a14
		  on 	(a11.ID_ANO_LANC = a14.ID_ANO and
		a11.ID_CONTA_CONTABIL_LANC = a14.ID_CONTA_CONTABIL)
		join	WD_UG_EXERCICIO	a15
		  on 	(a11.ID_ANO_LANC = a15.ID_ANO and
		a11.ID_UG_EXEC = a15.ID_UG)
		join	WD_ORGAO_EXERCICIO	a16
		  on 	(a15.ID_ANO = a16.ID_ANO and
		a15.ID_ORGAO_UG = a16.ID_ORGAO)
		join	WD_CONTA_CONTABIL	a17
		  on 	(a14.ID_CONTA_CONTABIL_DESTINO = a17.ID_CONTA_CONTABIL)
	where	(a11.ID_ANO_LANC in (2016)   -- <<< ANO
	 and a17.ID_CLASSE_CCON in (1, 2, 3, 4, 6, 8)
	 and a15.ID_ORGAO_UG in (26231, 26232, 26233, 26234, 26235, 26236, 26237, 26238, 26239, 26240, 26241, 26242, 26243, 26244, 26245, 26246, 26247, 26248, 26249, 26252, 26253, 26254, 26255, 26258, 26260, 26261, 26262, 26263, 26264, 26267, 26269, 26351, 26440, 26441, 26442, 26447, 26448, 26449, 26450, 26452, 26453, 26454, 26455, 26456, 26457)
	 and a13.ID_ANO = a11.ID_ANO_LANC
	 and a13.ID_MES = a11.ID_MES_LANC)
	group by	a16.ID_ORGAO_SUPE,
		a15.ID_ORGAO_UG,
		a15.ID_UG,
		a11.ID_ANO_LANC,
		a11.ID_MES_LANC,
		a11.ID_GRUPO_DESPESA_NADE,
		a11.ID_ELEMENTO_DESPESA_NADE,
		a14.ID_CONTA_CONTABIL_DESTINO
	)	pa11
	join	WD_CONTA_CONTABIL	a13
	  on 	(pa11.ID_CONTA_CONTABIL = a13.ID_CONTA_CONTABIL)
	join	WD_ELEMENTO_DESPESA_NADE	a14
	  on 	(pa11.ID_ELEMENTO_DESPESA_NADE = a14.ID_ELEMENTO_DESPESA_NADE)
	join	WD_GRUPO_DESPESA_NADE	a15
	  on 	(pa11.ID_GRUPO_DESPESA_NADE = a15.ID_GRUPO_DESPESA_NADE)
	join	WD_MES	a16
	  on 	(pa11.ID_ANO_LANC = a16.ID_ANO and
	pa11.ID_MES_LANC = a16.ID_MES)
	join	WD_UG	a17
	  on 	(pa11.ID_UG_EXEC = a17.ID_UG)
	join	WD_ORGAO	a18
	  on 	(pa11.ID_ORGAO = a18.ID_ORGAO)
	join	WD_ORGAO_SUPE	a19
	  on 	(pa11.ID_ORGAO_SUPE = a19.ID_ORGAO_SUPE)
group by	pa11.ID_ANO_LANC,
	pa11.ID_MES_LANC,
	pa11.ID_ORGAO_SUPE,
	pa11.ID_ORGAO,
	pa11.ID_UG_EXEC,
	pa11.ID_CONTA_CONTABIL,
	pa11.ID_GRUPO_DESPESA_NADE,
	pa11.ID_ELEMENTO_DESPESA_NADE
