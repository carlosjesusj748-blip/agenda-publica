import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from mlxtend.frequent_patterns import apriori, association_rules
import sqlite3
import database
from camara_api import CamaraAPIService

# Garante que o banco de dados existe e tem os cadastros iniciais
database.init_db()

# Função para conectar ao banco
def get_db_connection():
    conn = sqlite3.connect('sad_database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Configurações da página
st.set_page_config(
    page_title="SAD-AgendaPública | MTE",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ──────────────────────────────────────────────────────────────────────────────
# CONTROLE DE SESSÃO E LOGIN COM BANCO DE DADOS
# ──────────────────────────────────────────────────────────────────────────────
if 'usuario' not in st.session_state:
    st.session_state['usuario'] = None
    st.session_state['perfil'] = None

with st.sidebar:
    st.title("SAD-AgendaPública")
    st.markdown("---")
    
    if st.session_state['usuario'] is None:
        tab_login, tab_criar, tab_recuperar = st.tabs(["Login", "Criar Conta", "Recuperar Senha"])
        
        with tab_login:
            st.subheader("Login de Acesso")
            nome_input = st.text_input("Usuário (Ex: Decisor MTE, Data Analyst, Admin Dominio)", key="login_nome")
            senha_input = st.text_input("Senha (Ex: 123, admin)", type="password", key="login_senha")
            
            if st.button("Acessar o Sistema"):
                conn = get_db_connection()
                user = conn.execute("SELECT * FROM usuarios WHERE nome = ? AND senha = ?", (nome_input, senha_input)).fetchone()
                conn.close()
                
                if user:
                    st.session_state['usuario'] = user['nome']
                    st.session_state['perfil'] = user['perfil']
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")
                    
        with tab_criar:
            st.subheader("Criar Nova Conta")
            c_nome = st.text_input("Nome de Usuário", key="criar_nome")
            c_senha = st.text_input("Senha", type="password", key="criar_senha")
            c_perfil = st.selectbox("Perfil de Acesso", ["Usuário Decisor", "Analista de Dados", "Analista de Domínio"], key="criar_perfil")
            
            if st.button("Cadastrar Conta"):
                if c_nome and c_senha:
                    conn = get_db_connection()
                    # Verifica se já existe o nome de usuário
                    existe = conn.execute("SELECT id FROM usuarios WHERE nome = ?", (c_nome,)).fetchone()
                    if existe:
                        st.error("Nome de usuário já existe. Tente outro.")
                    else:
                        conn.execute("INSERT INTO usuarios (nome, senha, perfil) VALUES (?, ?, ?)", (c_nome, c_senha, c_perfil))
                        conn.commit()
                        st.success("Conta criada com sucesso! Faça o login na aba 'Login'.")
                    conn.close()
                else:
                    st.warning("Preencha todos os campos.")
                    
        with tab_recuperar:
            st.subheader("Recuperar Senha")
            r_nome = st.text_input("Nome de Usuário para recuperação", key="recuperar_nome")
            
            if st.button("Buscar Senha"):
                if r_nome:
                    conn = get_db_connection()
                    user = conn.execute("SELECT senha FROM usuarios WHERE nome = ?", (r_nome,)).fetchone()
                    conn.close()
                    
                    if user:
                        st.info(f"Sua senha é: {user['senha']}")
                    else:
                        st.error("Usuário não encontrado.")
                else:
                    st.warning("Informe o nome de usuário.")
    else:
        st.write(f"Conectado como: **{st.session_state['usuario']}**")
        st.write(f"Perfil de Acesso: *{st.session_state['perfil']}*")
        if st.button("Sair / Logout"):
            st.session_state['usuario'] = None
            st.session_state['perfil'] = None
            st.rerun()
            
    st.markdown("---")
    st.markdown("**Sistema de Apoio à Decisão Híbrido**")
    st.markdown("Trabalho da Disciplina (SAD)")

# Se não estiver logado, para a execução da tela
if st.session_state['usuario'] is None:
    st.title("SAD-AgendaPública 📊")
    st.subheader("Sistema de Apoio à Decisão para Regulação do Trabalho em Plataformas")
    st.info("Utilize a barra lateral para fazer login (As credenciais padrão estão no plano de implementação).")
    st.stop()


# ==============================================================================
# CARREGAMENTO DE DADOS (EXTRAÇÃO DO BD)
# ==============================================================================
@st.cache_data(ttl=60)
def carregar_indicadores():
    return pd.DataFrame({
        "ano": [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025],
        "trabalhadores_milhoes": [0.8, 1.0, 1.3, 1.5, 1.7, 1.9, 2.1, 2.3]
    })

def carregar_atores():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM atores_stakeholders", conn)
    conn.close()
    return df

def carregar_proposicoes():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM proposicoes_leis", conn)
    conn.close()
    return df

def carregar_eventos():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM eventos_impacto", conn)
    conn.close()
    return df

df_indicadores = carregar_indicadores()
df_atores = carregar_atores()
df_proposicoes = carregar_proposicoes()
df_eventos = carregar_eventos()


# ==============================================================================
# ROTEAMENTO DE INTERFACE POR PERFIL (A "CARA DO USUÁRIO")
# ==============================================================================
perfil = st.session_state['perfil']

# ------------------------------------------------------------------------------
# PERFIL 1: USUÁRIO DECISOR (MTE / GESTOR PÚBLICO)
# ------------------------------------------------------------------------------
if perfil == 'Usuário Decisor':
    st.title("Painel do Gestor (SAD: Blend de Opções)")
    
    # 1. Função de Sumarização (Muito bem feita)
    st.header("1. Sumarização do Ambiente Regulatório")
    st.markdown("Visão geral da agenda pública com dados extraídos do cadastro oficial do Estado.")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Contingente Afetado (IBGE/PNAD)", "2.30 Milhões", "+200 mil/ano", delta_color="inverse")
    col2.metric("Proposições Ativas no Congresso", len(df_proposicoes), "Monitoradas via API")
    col3.metric("Nível de Desproteção Social", "77%", "Sem INSS Patronal", delta_color="inverse")
    st.markdown("---")
    
    # 2. Blend de Opções (Simulador de Decisão)
    st.header("2. Simulador Decisório: O Blend de Opções")
    st.write("Calibre as variáveis táticas para gerar a recomendação do Sistema de Apoio à Decisão.")
    
    col_sim_l, col_sim_r = st.columns([1, 2])
    
    with col_sim_l:
        st.subheader("Variáveis Independentes")
        piso = st.slider("Piso (R$/Hora Conectada)", 10.0, 45.0, 32.10, 0.5)
        aliq_patronal = st.slider("INSS Patronal (%)", 0.0, 25.0, 20.0, 0.5)
        clima = st.selectbox("Fluxo Político (Congresso)", ["Favorável", "Moderado", "Oposição/Lobby"])
        
    with col_sim_r:
        st.subheader("Módulo de Recomendação (Variáveis Dependentes)")
        arrecadacao = (2300000 * 160 * 12) * piso * (aliq_patronal / 100)
        
        # Lógica Multi-Critério
        if piso >= 35.0 or aliq_patronal >= 20.0:
            recomendacao = "Opção B: Terceira Via Regulada (Modelo Híbrido Autônomo)"
            risco = "ALTO"
            alerta = st.error
        elif piso < 20.0:
            recomendacao = "Opção C: Microempreendedorismo Especial (Apenas MEI)"
            risco = "ALTO (Greves)"
            alerta = st.warning
        else:
            recomendacao = "Opção A: Regulação Híbrida Compulsória (Ótimo de Pareto)"
            risco = "MÉDIO"
            alerta = st.success
            
        alerta(f"🎯 **Ação Recomendada pelo SAD:** {recomendacao}")
        st.write(f"**Projeção de Arrecadação Bruta:** R$ {arrecadacao:,.2f}")
        st.write(f"**Risco Político / Veto Legislativo:** {risco}")


# ------------------------------------------------------------------------------
# PERFIL 2: ANALISTA DE DADOS (ENGENHARIA E KDD)
# ------------------------------------------------------------------------------
elif perfil == 'Analista de Dados':
    st.title("Módulo de Data Mining e KDD Avançado")
    st.info("Este ambiente restrito opera os modelos matemáticos e extração de padrões ocultos (KDD) exigidos pelo quadro teórico.")
    
    tab_kdd1, tab_kdd2, tab_kdd3 = st.tabs(["📉 Regressão Preditiva", "🎯 Agrupamento (K-Means)", "🔗 Regras de Associação (Apriori)"])
    
    # KDD 1: Regressão
    with tab_kdd1:
        st.subheader("Regressão Linear: Crescimento da Força de Trabalho")
        X = df_indicadores['ano'].values
        y = df_indicadores['trabalhadores_milhoes'].values
        slope, intercept = np.polyfit(X, y, 1)
        
        X_proj = np.append(X, [2026, 2027, 2028])
        y_proj = slope * X_proj + intercept
        
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.scatter(X, y, color='red', label="Histórico (IBGE)")
        ax.plot(X_proj, y_proj, color='blue', linestyle='--', label="Regressão Projetada")
        ax.set_title("Projeção de Entregadores de Aplicativos no Brasil")
        ax.set_ylabel("Milhões de Trabalhadores")
        ax.legend()
        st.pyplot(fig)
        st.write(f"**Modelo de Tendência:** y = {slope:.3f}x + {intercept:.1f}")

    # KDD 2: Agrupamento
    with tab_kdd2:
        st.subheader("Agrupamento de Atores: K-Means (k=3)")
        st.write("Baseado no Score Qualitativo de 'Poder' vs 'Aliado' cadastrado na Tabela do Quadro Teórico.")
        
        if len(df_atores) >= 3:
            map_score = {'alto': 3, 'médio': 2, 'baixo': 1}
            df_clus = df_atores.copy()
            df_clus['poder'] = df_clus['poder_influencia'].map(map_score).fillna(1)
            df_clus['aliado'] = df_clus['aliado_trabalhadores'].map(map_score).fillna(1)
            
            X_clus = df_clus[['poder', 'aliado']].values
            kmeans = KMeans(n_clusters=3, random_state=42, n_init=10).fit(X_clus)
            
            fig2, ax2 = plt.subplots(figsize=(8, 4))
            scatter = ax2.scatter(X_clus[:, 0], X_clus[:, 1], c=kmeans.labels_, cmap='viridis', s=150)
            for i, txt in enumerate(df_clus['ator']):
                ax2.annotate(txt, (X_clus[i, 0] + 0.05, X_clus[i, 1] + 0.05))
            ax2.set_xlabel("Poder de Influência Política (1 a 3)")
            ax2.set_ylabel("Alinhamento com Direitos (1 a 3)")
            st.pyplot(fig2)
        else:
            st.warning("Poucos dados na tabela de Atores para rodar o clustering.")

    # KDD 3: Associação
    with tab_kdd3:
        st.subheader("Mineração de Regras de Associação (Algoritmo Apriori)")
        st.write("Minerando co-ocorrência histórica entre os tipos de eventos registrados no Banco de Dados (CSV).")
        
        if not df_eventos.empty:
            # Transformação One-Hot Encoding para o Apriori
            df_assoc = df_eventos[['tipo_evento', 'ator_principal']].dropna()
            df_dummies = pd.get_dummies(df_assoc)
            
            # Garantir booleanos puros para o mlxtend
            df_dummies = df_dummies.astype(bool)
            
            try:
                itemsets = apriori(df_dummies, min_support=0.01, use_colnames=True)
                regras = association_rules(itemsets, metric="confidence", min_threshold=0.5)
                
                if not regras.empty:
                    # Formatar visualmente as regras
                    st.write(f"O algoritmo detectou {len(regras)} regras de associação fortes:")
                    for idx, row in regras.iterrows():
                        antecedentes = ", ".join(list(row['antecedents']))
                        consequentes = ", ".join(list(row['consequents']))
                        st.info(f"**Regra:** SE ({antecedentes}) ENTÃO ({consequentes}) | **Confiança:** {row['confidence']*100:.1f}%")
                else:
                    st.write("O algoritmo não encontrou associações estatisticamente fortes na amostragem atual do CSV.")
            except Exception as e:
                st.error(f"Erro ao processar Apriori: {e}")
        else:
            st.warning("Tabela de eventos (CSV) está vazia.")


# ------------------------------------------------------------------------------
# PERFIL 3: ANALISTA DE DOMÍNIO (PAINEL ADMINISTRADOR)
# ------------------------------------------------------------------------------
elif perfil == 'Analista de Domínio':
    st.title("⚙️ Painel do Administrador (CRUD & Integrações)")
    st.write("Interface de governança da Base de Dados Cadastral e sincronização via API.")
    
    st.subheader("Sincronização Ativa com API da Câmara dos Deputados")
    if st.button("⬇️ Baixar Projetos de Lei em Tempo Real (API)"):
        with st.spinner("Conectando à Câmara dos Deputados..."):
            api = CamaraAPIService()
            dados = api.buscar_projetos_lei(palavra_chave="aplicativo")
            if dados:
                conn = get_db_connection()
                for d in dados:
                    sigla = f"{d.get('siglaTipo', '')} {d.get('numero', '')}/{d.get('ano', '')}"
                    ementa = d.get('ementa', '')
                    ano = d.get('ano', 2025)
                    # Verifica se já existe
                    cur = conn.execute("SELECT id FROM proposicoes_leis WHERE sigla_numero = ?", (sigla,))
                    if not cur.fetchone():
                        conn.execute("INSERT INTO proposicoes_leis (sigla_numero, ano, ementa, viabilidade) VALUES (?, ?, ?, ?)",
                                     (sigla, ano, ementa, "Em Análise"))
                conn.commit()
                conn.close()
                st.success(f"{len(dados)} Projetos de Lei sincronizados e armazenados no Banco de Dados SQLite com sucesso!")
            else:
                st.warning("Nenhum dado retornado da API ou falha na conexão.")
                
    st.markdown("---")
    
    col_crud1, col_crud2 = st.columns(2)
    with col_crud1:
        st.subheader("Gerenciar Tabela: Proposições de Leis (SQLite)")
        df_leis = carregar_proposicoes()
        st.dataframe(df_leis, hide_index=True)
        
        with st.form("add_lei"):
            st.write("Inserir Nova Proposta Manualmente")
            l_sigla = st.text_input("Sigla e Número (Ex: PL 999/2026)")
            l_ano = st.number_input("Ano", 2020, 2030, 2026)
            l_ementa = st.text_input("Ementa/Resumo")
            l_viab = st.selectbox("Viabilidade", ["Alta", "Média", "Baixa"])
            if st.form_submit_button("Salvar no Banco"):
                conn = get_db_connection()
                conn.execute("INSERT INTO proposicoes_leis (sigla_numero, ano, ementa, viabilidade) VALUES (?, ?, ?, ?)",
                             (l_sigla, l_ano, l_ementa, l_viab))
                conn.commit()
                conn.close()
                st.success("Salvo com sucesso!")
                st.rerun()

    with col_crud2:
        st.subheader("Gerenciar Tabela: Usuários (Controle de Acesso)")
        conn = get_db_connection()
        df_users = pd.read_sql_query("SELECT id, nome, perfil FROM usuarios", conn)
        conn.close()
        st.dataframe(df_users, hide_index=True)
        
        with st.form("add_user"):
            st.write("Cadastrar Novo Usuário")
            u_nome = st.text_input("Nome de Usuário")
            u_senha = st.text_input("Senha", type="password")
            u_perfil = st.selectbox("Perfil de Acesso", ["Usuário Decisor", "Analista de Dados", "Analista de Domínio"])
            if st.form_submit_button("Criar Usuário"):
                conn = get_db_connection()
                conn.execute("INSERT INTO usuarios (nome, senha, perfil) VALUES (?, ?, ?)", (u_nome, u_senha, u_perfil))
                conn.commit()
                conn.close()
                st.success("Usuário criado!")
                st.rerun()
