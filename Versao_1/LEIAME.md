# Versão 1

Cópia dos arquivos da Versão 1 do projeto, igual ao commit `37d21fb` do repositório. Ela foi guardada para registro e comparação, e a versão em uso é a Versão 2, que fica na raiz do repositório.

## Diferenças em relação à Versão 2

1. **F9 e F16 sem ajuste pelo porte.** Na Versão 1, a F9 (tendência do resultado patrimonial) e a F16 (tendência da VPD) eram inclinações em reais por mês. Na Versão 2, cada inclinação é dividida pela média mensal da própria série (média da VPA para a F9 e média da VPD para a F16), para que o porte da universidade não gere desvio por si só.
2. **Ranking com uma única semente.** Na Versão 1, o ranking usava uma única execução do Isolation Forest (`random_state=42`), e a zona de risco era formada pelas universidades com escore positivo nessa execução. Na Versão 2, o ranking usa a média de 100 execuções com sementes diferentes, e a zona de risco reúne as universidades com escore positivo em pelo menos 50% delas.
3. **Cores dos gráficos de cascata.** Na Versão 1, os gráficos do SHAP usavam as cores padrão da biblioteca, em que o vermelho indicava os fatores que reduziam o risco. Na Versão 2, o vermelho passou a indicar os fatores que aumentam o risco.

## Resultado da Versão 1

Zona de risco (19 indicadores, semente 42, escore positivo), nesta ordem: UNILA, UFNT, UFF, UNIRIO e UFRJ.

## Observações

- O arquivo de dados brutos (`Exportação_completa_mestrado.zip`) não foi copiado para esta pasta porque é o mesmo da Versão 2. Ele está em `arquivos_tabulares`, na raiz do repositório.
- O arquivo `waterfall_unila.svg` desta versão está vazio, por um erro na célula que o gerava. O erro foi corrigido na Versão 2.
- Para abrir o painel desta versão, execute o comando `streamlit run 03_dashboard_tcu.py` de dentro desta pasta.
