# Versão 2

Arquivos da Versão 2 do projeto, iguais ao commit `4bf5288` (10/11/2026), que é a versão mostrada no painel publicado enquanto a Versão 3 estiver em desenvolvimento. A Versão 3 é a estrutura numerada da raiz do repositório.

Painel publicado: https://pipelineprojetomestrado-5fthcuwmapxgk5ymjo99wl.streamlit.app/

## O que é a Versão 2

Classificação das 45 universidades federais da Portaria-TCU nº 58/2025 segundo o risco de distorção contábil, com 20 indicadores calculados sobre a movimentação contábil mensal de 2023 a 2025. O modelo é um Isolation Forest com 19 indicadores (a F7 foi retirada pelo filtro de colinearidade), e cada alerta é explicado com SHAP.

Mudanças em relação à Versão 1:

1. F9 e F16 passaram a ser inclinações relativas, divididas pela média mensal da própria série, para corrigir o viés de porte.
2. O ranking passou a usar a média de 100 execuções do Isolation Forest com sementes diferentes. A zona de risco reúne as universidades com escore positivo em pelo menos 50% das execuções, e os valores SHAP são a média das 100 execuções.
3. Os gráficos de cascata do SHAP passaram a usar vermelho para os fatores que aumentam o risco e azul para os que o reduzem.

Resultado: zona de risco formada por UFNT, UNILA e UFF (escore positivo em 100% das execuções) e UNIRIO (56%).

## Arquivos

- `01_pipeline_redflags.ipynb`: leitura dos dados brutos e cálculo dos 20 indicadores.
- `02_modelagem_ml_novo.ipynb`: filtro de colinearidade, Isolation Forest, ranking com 100 sementes, SHAP e gráficos.
- `03_dashboard_tcu.py`: painel em Streamlit.
- `Iniciar_Painel_TCU.bat`: atalho para abrir o painel no Windows, usando o ambiente virtual da raiz do repositório.
- `arquivos_tabulares/`: dados brutos compactados, indicadores, resultados, valores SHAP e dicionário dos indicadores.
- `graficos_shap_risco/` e `graficos_distribuicao/`: gráficos das universidades na zona de risco.
- `waterfall_top1_semente42.svg`: gráfico de cascata do modelo de semente única.
- `link_dashboard.txt`: endereço do painel publicado.

## Como executar

Todos os caminhos são relativos a esta pasta. Os comandos devem ser rodados de dentro dela:

1. Descompacte `arquivos_tabulares/Exportação_completa_mestrado.zip`.
2. Execute `01_pipeline_redflags.ipynb` e depois `02_modelagem_ml_novo.ipynb`.
3. Abra o painel com `streamlit run 03_dashboard_tcu.py`.
