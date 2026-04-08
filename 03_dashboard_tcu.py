# ==============================================================================
# 03_DASHBOARD_TCU.py - Painel Interativo de Auditoria Contábil
# Como rodar no terminal: streamlit run 03_dashboard_tcu.py
# ==============================================================================
import streamlit as st
import pandas as pd
import os

# 1. Configuração da Página Web
st.set_page_config(
    page_title="TCU - Malha Fina Contábil IA",
    page_icon="🔎",
    layout="wide"
)

# 2. Estilização Customizada
st.markdown("""
    <style>
    .main-title {font-size: 36px; font-weight: bold; color: #004b87;}
    .sub-title {font-size: 18px; color: #555555; margin-bottom: 30px;}
    .risk-high {color: #ff0051; font-weight: bold; font-size: 24px;}
    </style>
""", unsafe_allow_html=True)

# 3. Carregando os Dados do Script 02
@st.cache_data 
def carregar_dados():
    df = pd.read_csv('arquivos_tabulares/resultados_auditoria_ia.csv', sep=';', decimal=',')
    
    # Carrega a Base Bruta original (que contém as 20 variáveis, incluindo a F7)
    df_bruta = pd.read_csv('arquivos_tabulares/df_features_consolidadas.csv', sep=';', decimal=',')
    
    # 3. O Pulo do Gato (O JOIN): Junta a F7 na tabela de scores usando o Cod_Orgao
    df = pd.merge(df, df_bruta[['Cod_Orgao', 'F7_Qtd_Deficit_Fin']], on='Cod_Orgao', how='left')

    # Ordena pelo Score (do maior risco para o menor) e cria o Ranking Geral
    df = df.sort_values(by='Score_IA_19_Features', ascending=False).reset_index(drop=True)
    df['Posicao_Ranking'] = df.index + 1
    
    # Separa quem está em risco para o menu lateral
    df_risco = df[df['Score_IA_19_Features'] > 0].copy()
    
    return df, df_risco

# Recebe as duas bases e conta o total de entidades
df_completo, df_risco = carregar_dados()
total_entidades = len(df_completo)

# 4. Carregando o Dicionário de Red Flags (Excel)
@st.cache_data 
def carregar_dicionario():
    try:
        # ATENÇÃO: Coloque o nome exato do seu arquivo Excel aqui abaixo
        df = pd.read_excel('arquivos_tabulares/dicionario_red_flags.xlsx')
        return df
    except FileNotFoundError:
        # Se o arquivo não existir, criamos uma tabela de erro temporária para o painel não quebrar
        return pd.DataFrame({"Aviso": ["Arquivo 'dicionario_red_flags.xlsx' não encontrado na pasta."]})

df_dicionario = carregar_dicionario()

# ==============================================================================
# BARRA LATERAL (MENU DE NAVEGAÇÃO DO AUDITOR)
# ==============================================================================
st.sidebar.image("https://logodownload.org/wp-content/uploads/2017/11/tcu-logo-tribunal-de-contas-da-uniao.png", width=100)
st.sidebar.title("Filtro de Auditoria")
st.sidebar.markdown("Selecione a Unidade Prestadora de Contas para visualizar as informações sobre os riscos contábeis dela.")

lista_orgaos = df_risco['Nome_Orgao'].tolist()
orgao_selecionado = st.sidebar.selectbox("Universidade Federal:", lista_orgaos)

# ==============================================================================
# TELA PRINCIPAL
# ==============================================================================
st.markdown('<p class="main-title">🔎 Painel de Anomalias Contábeis (Isolation Forest)</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Monitoramento Contínuo Multivariado das Instituições Federais de Ensino Superior</p>', unsafe_allow_html=True)

if orgao_selecionado:
    # Pega os dados da universidade escolhida
    dados_orgao = df_risco[df_risco['Nome_Orgao'] == orgao_selecionado].iloc[0]
    cod_orgao = dados_orgao['Cod_Orgao']
    score = dados_orgao['Score_IA_19_Features']
    posicao = dados_orgao['Posicao_Ranking'] # NOVO: Pega a posição real
    
    # --- CABEÇALHO DO LAUDO ---
    col1, col2, col3 = st.columns([2, 1, 1]) # Dividido em 3 colunas agora
    
    with col1:
        st.subheader(f"🏛️ {orgao_selecionado}")
        st.write(f"**Código UG:** {cod_orgao}")
        
    with col2:
        st.markdown("**Ranking de Risco (Nacional):**")
        st.markdown(f'<p style="font-size: 22px; font-weight: bold; color: #cc0000;">🚨 {posicao}º lugar</p>', unsafe_allow_html=True)
        st.write(f"*(entre {total_entidades} UGs analisadas)*")
        
    with col3:
        st.markdown(f"**Escore de Anomalia (IA):**")
        st.markdown(f'<p class="risk-high">{score:.4f}</p>', unsafe_allow_html=True)
        
    st.divider()

    # --- ABAS DE NAVEGAÇÃO INTERNA ---
    aba1, aba2, aba3, aba4 = st.tabs(["🏆 Ranking Geral", "📊 Visão Multivariada (SHAP)", "📈 Provas de Isolamento (Distribuições)", "📚 Dicionário de Red Flags"])
    
    # --- ABA 1: RANKING GERAL ---
    with aba1:
        st.markdown("### Ranking de Risco da Rede Federal (2023 a 2025)")
        st.write("Visão consolidada de todas as **45 Universidades Federais** classificadas como Unidades Prestadoras de Contas pelo TCU. Entidades na zona de risco (escore de risco > 0) estão destacadas em vermelho.")
        
        # Filtra e renomeia as colunas para ficar com cara de relatório oficial
        df_exibicao = df_completo[['Posicao_Ranking', 'Nome_Orgao', 'Cod_Orgao', 'Score_IA_19_Features']].copy()
        df_exibicao.columns = ['Posição', 'Universidade', 'Código UG', 'Escore de Risco (IA)']
        
        # --- LÓGICA DE CORES (PANDAS STYLER) ---
        def destacar_risco(row):
            # Se o score que indica risco no seu modelo for negativo, mude de "> 0" para "< 0"
            if row['Escore de Risco (IA)'] > 0:
                # Fundo vermelho bem claro, texto em vermelho escuro
                return ['background-color: #ffe6e6; color: #a30000; font-weight: bold'] * len(row)
            else:
                # Mantém a cor padrão do sistema para as entidades normais
                return [''] * len(row)
        
        # Aplica a função de cor linha por linha (axis=1)
        df_estilizado = df_exibicao.style.apply(destacar_risco, axis=1)
        
        # Opcional: Formata a coluna de Escore para mostrar apenas 4 casas decimais
        df_estilizado = df_estilizado.format({"Escore de Risco (IA)": "{:.4f}"})
        
        # Exibe a tabela formatada no Streamlit
        st.dataframe(df_estilizado, use_container_width=True, hide_index=True)

    # --- ABA 2: SHAP (Antiga Aba 1) ---
    with aba2:
        st.markdown("### A Anatomia da Anomalia")
        st.write("O gráfico abaixo (Waterfall SHAP) demonstra matematicamente quais indicadores contábeis empurraram esta entidade para fora da normalidade da rede federal. Barras **azuis** para a **esquerda** indicam fatores de agravamento do risco.")
        
        pasta_shap = "graficos_shap_risco"
        
        # --- NOVO: Botão interativo para alternar as visões ---
        # O padrão é False (Desligado = Resumido)
        mostrar_expandido = st.toggle("🔍 Mostrar Visão Expandida (Todas as 20 Variáveis)")
        
        # Define qual palavra procurar no nome do arquivo com base no botão
        tipo_grafico = "_Expandido" if mostrar_expandido else "_Resumido"
        
        try:
            # Busca especificamente o arquivo com o sufixo correto
            arquivos_shap = [f for f in os.listdir(pasta_shap) if f"Cod_{cod_orgao}{tipo_grafico}" in f]
            
            if arquivos_shap:
                caminho_imagem_shap = os.path.join(pasta_shap, arquivos_shap[0])
                st.image(caminho_imagem_shap, use_container_width=True)
            else:
                st.warning(f"⚠️ Gráfico SHAP ({tipo_grafico.replace('_', '')}) não encontrado na pasta 'graficos_shap_risco'.")
                
        except FileNotFoundError:
            st.error("A pasta 'graficos_shap_risco' não foi encontrada.")


    # --- ABA 3: DISTRIBUIÇÕES (Análise Individual de Variáveis) ---
    with aba3:
        st.markdown("### Evidências de Afastamento da Normalidade")
        
        st.write(
            "Análise isolada das variáveis que apresentaram comportamento atípico, "
            "**ordenadas da maior para a menor influência no risco (conforme Gráfico SHAP)**. "
            "A linha tracejada representa a mediana da rede federal, enquanto a linha vermelha aponta o fato registrado na entidade analisada."
        )
        
        pasta_dist = "graficos_distribuicao"
        try:
            # Captura todos os arquivos gerados para esta UG no Script 02
            todos_arquivos = [f for f in os.listdir(pasta_dist) if f.startswith(f"Dist_{cod_orgao}_")]
            todos_arquivos.sort()
            
            # SEPARAÇÃO DE LÓGICA:
            # 1. Imagens regulares (o ranking SHAP)
            arquivos_regulares = [f for f in todos_arquivos if "EXTRA_F7" not in f]
            # 2. A imagem extra da F7 (se existir)
            arquivo_f7_extra = [f for f in todos_arquivos if "EXTRA_F7" in f]
            
            # Verifica se a F5 faz parte das anomalias detectadas
            f5_detectada = any("F5_Var_Pag_Repasse" in f for f in arquivos_regulares)
            
            if arquivos_regulares:
                # Exibição padrão em duas colunas para as variáveis do ranking
                col_esq, col_dir = st.columns(2)
                
                for index, arquivo in enumerate(arquivos_regulares):
                    caminho_dist = os.path.join(pasta_dist, arquivo)
                    if index % 2 == 0:
                        col_esq.image(caminho_dist, use_container_width=True)
                    else:
                        col_dir.image(caminho_dist, use_container_width=True)
                
                # SEÇÃO FINAL: Gatilho da F7 (Apenas se F5 existir e F7 foi gerada)
                if f5_detectada and arquivo_f7_extra:
                    st.divider()
                    st.markdown("#### 🚨 Evidência Material Complementar (F7)")
                    st.info(
                        "Como a variável **F5 (Variação de Pagamento de Repasse)** foi identificada como fator de risco, "
                        "o painel exibe abaixo a distribuição da **F7 (Qtd Déficit Financeiro)**. "
                        "Embora suprimida do modelo matemático para evitar colinearidade, a F7 é apresentada aqui "
                        "para fundamentar a materialidade do déficit financeiro nesta unidade."
                    )
                    
                    caminho_f7 = os.path.join(pasta_dist, arquivo_f7_extra[0])
                    st.image(caminho_f7, use_container_width=True)
                    
            else:
                st.info("Nenhum gráfico de distribuição específico encontrado para esta entidade.")
                
        except FileNotFoundError:
            st.error("A pasta 'graficos_distribuicao' não foi encontrada.")
            
    # --- ABA 4: DICIONÁRIO DE RED FLAGS ---
    with aba4:
        st.markdown("### Dicionário de Indicadores (Features)")
        st.write("Consulte abaixo a descrição técnica de cada variável analisada pelo modelo e a justificativa para sua utilização como fator de risco.")
        
        if "Aviso" in df_dicionario.columns:
            st.warning(df_dicionario["Aviso"].iloc[0])
        else:
            # Renderiza a tabela do Excel interativa (com scroll, ordenação, etc.)
            st.dataframe(df_dicionario, use_container_width=True, hide_index=True)