# Malha Fina Contábil - TCU (Inteligência Artificial)

Repositório com o pipeline de dados, a modelagem (Isolation Forest e SHAP) e o painel interativo em Streamlit desenvolvidos para a dissertação de mestrado de Nelson G. S. Ramos no Mestrado Profissional em Controle da Administração Pública do Instituto Serzedello Corrêa (ISC/TCU).

O modelo classifica as 45 universidades federais relacionadas como Unidades Prestadoras de Contas na Portaria-TCU nº 58/2025 segundo o risco de distorção contábil, a partir de indicadores calculados com a movimentação contábil mensal de 2023 a 2025, extraída do Tesouro Gerencial. O resultado é um critério de priorização para o planejamento de auditorias e não constitui juízo de irregularidade.

Painel publicado: https://pipelineprojetomestrado-5fthcuwmapxgk5ymjo99wl.streamlit.app/

## Versões

| Versão | Local | Situação |
|---|---|---|
| Versão 2 (Atual) | raiz do repositório | Em uso |
| Versão 1 | pasta `Versao_1` | Guardada para registro e comparação (ver `Versao_1/LEIAME.md`) |

Mudanças da Versão 2 em relação à Versão 1:

1. F9 e F16 passaram a ser inclinações relativas, divididas pela média mensal da própria série, para corrigir o viés de porte.
2. O ranking passou a usar a média de 100 execuções do Isolation Forest com sementes diferentes. A zona de risco reúne as universidades com escore positivo em pelo menos 50% das execuções, e os valores SHAP são a média das 100 execuções.
3. Os gráficos de cascata do SHAP passaram a usar vermelho para os fatores que aumentam o risco e azul para os que o reduzem.

Resultado da Versão 2: zona de risco formada por UFNT, UNILA e UFF (escore positivo em 100% das execuções) e UNIRIO (56%).

## Estrutura do projeto

- `01_pipeline_redflags.ipynb`: leitura dos dados brutos e cálculo dos 20 indicadores (F1 a F20).
- `02_modelagem_ml_novo.ipynb`: filtro de colinearidade de Spearman (retirada da F7), Isolation Forest com 19 indicadores, ranking com 100 sementes, valores SHAP e geração dos gráficos.
- `03_dashboard_tcu.py`: painel interativo em Streamlit.
- `Iniciar_Painel_TCU.bat`: atalho para abrir o painel localmente no Windows.
- `arquivos_tabulares/`: dados brutos compactados, indicadores calculados, resultados do ranking, valores SHAP e dicionário dos indicadores.
- `graficos_shap_risco/`: gráficos de cascata do SHAP das universidades na zona de risco.
- `graficos_distribuicao/`: gráficos de distribuição dos indicadores que mais contribuíram para cada alerta.
- `waterfall_top1_semente42.svg`: gráfico de cascata da primeira colocada no modelo de semente única, usado na explicação do funcionamento do modelo.
- `Versao_1/`: arquivos da Versão 1.

## Como executar

1. Descompacte `arquivos_tabulares/Exportação_completa_mestrado.zip`.
2. Execute o notebook `01_pipeline_redflags.ipynb` e informe o caminho do CSV bruto quando solicitado. Ele gera `arquivos_tabulares/df_features_consolidadas.csv`.
3. Execute o notebook `02_modelagem_ml_novo.ipynb`. Ele gera os resultados, os valores SHAP e os gráficos.
4. Abra o painel com `streamlit run 03_dashboard_tcu.py`, a partir da raiz do repositório.

O painel usa as bibliotecas listadas em `requirements.txt`. Os notebooks usam também `numpy`, `scikit-learn`, `shap`, `matplotlib` e `seaborn`.
