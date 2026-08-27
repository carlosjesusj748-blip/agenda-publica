import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression
from mlxtend.frequent_patterns import apriori, association_rules
import sqlite3
import database
import time
import os
import json
from datetime import datetime

# Caminho absoluto para o banco de dados
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "sad_eduseg.db")

# Garante que o banco de dados existe e tem os cadastros iniciais
database.init_db()

def get_db_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def registrar_log(usuario, orgao, acao, tabela):
    try:
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO sistema_logs_auditoria (usuario_id, orgao_usuario, acao_executada, tabela_acessada) VALUES (?, ?, ?, ?)",
            (usuario, orgao, acao, tabela)
        )
        conn.commit()
        conn.close()
    except Exception:
        pass

# ──────────────────────────────────────────────────────────────────────────────
# CONFIGURAÇÃO DA PÁGINA
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SAD-EduSeg | Bahia",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado injetando a identidade do HTML fornecido
st.markdown("""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Fundo leve da aplicação */
    .stApp { background-color: #f8fafc; }
    
    /* Cards de KPI no estilo Tailwind */
    .metric-card {
        background: white;
        border-radius: 1rem;
        padding: 1.5rem;
        border: 1px solid #f1f5f9;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }
    .metric-card.blue { border-left: 4px solid #3b82f6; }
    .metric-card.orange { border-left: 4px solid #f97316; }
    .metric-card.red { border-left: 4px solid #ef4444; }
    .metric-card.emerald { border-left: 4px solid #10b981; }
    
    .metric-info h4 { margin: 0; font-size: 0.875rem; color: #64748b; font-weight: 600; }
    .metric-info h2 { margin: 0; font-size: 1.875rem; color: #1e293b; font-weight: 700; line-height: 1.2; }
    
    .metric-icon {
        width: 3rem; height: 3rem;
        border-radius: 9999px;
        display: flex; align-items: center; justify-content: center;
        font-size: 1.25rem;
    }
    .metric-icon.blue { background-color: #eff6ff; color: #2563eb; }
    .metric-icon.orange { background-color: #fff7ed; color: #ea580c; }
    .metric-icon.red { background-color: #fef2f2; color: #dc2626; }
    .metric-icon.emerald { background-color: #ecfdf5; color: #059669; }

    /* Estilo do Simulador */
    .sim-header {
        background-color: #0f172a;
        color: white;
        padding: 1rem 1.5rem;
        border-top-left-radius: 1.5rem;
        border-top-right-radius: 1.5rem;
        font-weight: 700;
        display: flex; align-items: center; gap: 0.5rem;
    }
    
    /* Box de Recomendação (Blend) */
    .blend-box {
        padding: 1.5rem;
        border-radius: 1rem;
        color: white;
        text-align: center;
        display: flex; flex-direction: column; justify-content: center; align-items: center;
        min-height: 12rem;
        transition: all 0.3s ease;
    }
    .blend-critico { background: linear-gradient(to bottom right, #dc2626, #9f1239); box-shadow: 0 10px 15px -3px rgba(220, 38, 38, 0.3); }
    .blend-moderado { background: linear-gradient(to bottom right, #f97316, #b45309); box-shadow: 0 10px 15px -3px rgba(249, 115, 22, 0.3); }
    .blend-estavel { background: linear-gradient(to bottom right, #10b981, #0f766e); box-shadow: 0 10px 15px -3px rgba(16, 185, 129, 0.3); }
    
    .teoria-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 1rem;
        padding: 1.5rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    .teoria-card h3 { color: #1e40af; border-bottom: 1px solid #e2e8f0; padding-bottom: 0.5rem; font-size: 1.25rem; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# LOGIN RBAC
# ──────────────────────────────────────────────────────────────────────────────
if 'usuario' not in st.session_state:
    st.session_state['usuario'] = None
    st.session_state['perfil'] = None

with st.sidebar:
    st.markdown("""
    <div style="display:flex; align-items:center; gap:10px; margin-bottom: 20px;">
        <div style="background:#2563eb; color:white; width:40px; height:40px; border-radius:8px; display:flex; align-items:center; justify-content:center; font-size:20px;">
            <i class="fas fa-shield-halved"></i>
        </div>
        <div>
            <h2 style="margin:0; font-size:18px; font-weight:700;">SAD-EduSeg</h2>
            <p style="margin:0; font-size:12px; color:#64748b;">Bahia Governo</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    if st.session_state['usuario'] is None:
        tab_login, tab_criar, tab_recuperar = st.tabs(["Login", "Criar Conta", "Recuperar Senha"])

        with tab_login:
            st.subheader("Acesso RBAC")
            nome_input = st.text_input("Usuário", key="login_nome", value="Gestor Publico")
            senha_input = st.text_input("Senha", type="password", key="login_senha", value="123")
            if st.button("Entrar", type="primary", use_container_width=True):
                conn = get_db_connection()
                user = conn.execute("SELECT * FROM usuarios WHERE nome = ? AND senha = ?", (nome_input, senha_input)).fetchone()
                conn.close()
                if user:
                    st.session_state['usuario'] = user['nome']
                    st.session_state['perfil'] = user['perfil']
                    registrar_log(user['nome'], user['perfil'], "LOGIN", "usuarios")
                    st.rerun()
                else:
                    st.error("Credenciais inválidas.")

        with tab_criar:
            st.subheader("Nova Conta")
            c_nome = st.text_input("Nome", key="c_nome")
            c_senha = st.text_input("Senha", type="password", key="c_senha")
            c_perfil = st.selectbox("Perfil", ["Gestor Público", "Analista KDD", "Admin Domínio"])
            if st.button("Cadastrar", use_container_width=True):
                if c_nome and c_senha:
                    conn = get_db_connection()
                    existe = conn.execute("SELECT id FROM usuarios WHERE nome = ?", (c_nome,)).fetchone()
                    if existe:
                        st.error("Nome já existe.")
                    else:
                        conn.execute("INSERT INTO usuarios (nome, senha, perfil) VALUES (?, ?, ?)", (c_nome, c_senha, c_perfil))
                        conn.commit()
                        st.success("Criado! Faça login.")
                    conn.close()

        with tab_recuperar:
            st.subheader("Recuperar Senha")
            r_nome = st.text_input("Nome de Usuário", key="recuperar_nome")
            if st.button("Buscar Senha", use_container_width=True):
                if r_nome:
                    conn = get_db_connection()
                    user = conn.execute("SELECT senha, perfil FROM usuarios WHERE nome = ?", (r_nome,)).fetchone()
                    conn.close()
                    if user:
                        st.info(f"🔑 Sua senha é: **{user['senha']}**")
                        st.caption(f"Perfil: {user['perfil']}")
                    else:
                        st.error("Usuário não encontrado.")
    else:
        st.write(f"👤 **{st.session_state['usuario']}**")
        st.write(f"🔒 *{st.session_state['perfil']}*")
        if st.button("Encerrar Sessão", use_container_width=True):
            registrar_log(st.session_state['usuario'], st.session_state['perfil'], "LOGOUT", "usuarios")
            st.session_state['usuario'] = None
            st.session_state['perfil'] = None
            if 'messages' in st.session_state:
                del st.session_state['messages']
            st.rerun()

    st.markdown("---")
    st.caption("EAUFBA · Sistemas de Apoio à Decisão")
    st.caption("Conformidade LGPD · RBAC · Auditoria Ativa")

if st.session_state['usuario'] is None:
    st.title("SAD-EduSeg: Segurança Pública & Educação 🛡️📚")
    st.subheader("Sistema de Apoio à Decisão Cognitivo — Estado da Bahia")
    st.info("Utilize o painel lateral para fazer login. Credenciais: **Gestor Publico** / 123 · **Analista KDD** / 123 · **Admin Dominio** / admin")
    
    # Exibir a teoria mesmo na tela de login para enriquecer
    st.markdown("---")
    st.markdown("### Fundamentação Teórica do Projeto")
    st.markdown("""
    **A Evolução dos Sistemas e a Identidade do SAD**
    De acordo com o estudo comparativo de Perottoni et al. (2001), as organizações operam sob diferentes camadas de sistemas. Os **Sistemas de Apoio à Decisão (SAD)** diferenciam-se por focar no suporte a decisões semiestruturadas (que combinam dados exatos e o julgamento humano).
    
    **O Framework Teórico do KDD**
    As pesquisas de Coradine, Lopes e Maciel (2011) e de Santos (2009) definem a Descoberta de Conhecimento em Bancos de Dados (KDD) como um processo interativo. Este sistema implementa:
    1. **Sumarização:** Descrição compacta e limpa das bases de dados (Dashboard).
    2. **Agrupamento (Clustering):** Divide a população em subgrupos homogêneos (K-Means).
    3. **Associação:** Mapeia relacionamentos item a item (Apriori).
    4. **Regressão:** Mapeia a relação funcional entre variáveis (Previsão de Evasão).
    """)
    st.stop()

# ==============================================================================
# EXTRAÇÃO DE DADOS
# ==============================================================================
usuario_atual = st.session_state['usuario']
perfil = st.session_state['perfil']

@st.cache_data(ttl=60)
def carregar_visao_escolas():
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT
        e.id_escola,
        e.nome_escola_mascarado AS nome_escola,
        r.nome_bairro AS bairro,
        r.indice_vulnerabilidade_social AS ivs,
        r.renda_media_familiar AS renda,
        r.presenca_iluminacao_publica AS iluminacao,
        e.total_alunos_ativos,
        e.turno_funcionamento,
        e.latitude, e.longitude,
        COUNT(CASE WHEN o.distancia_escola_proxima_metros <= 500 THEN o.id_ocorrencia END) AS crimes_500m,
        ROUND(AVG(a.taxa_assiduidade_trimestre), 2) AS media_assiduidade,
        SUM(CASE WHEN a.flag_evasao_risco = 1 THEN 1 ELSE 0 END) AS alunos_risco_evasao,
        SUM(a.qtd_ocorrencias_disciplinares) AS total_ocorrencias_disc
    FROM tabelas_educacao_escolas e
    JOIN tabelas_contexto_regioes r ON e.id_regiao = r.id_regiao
    LEFT JOIN tabelas_educacao_alunos_anonimizados a ON e.id_escola = a.id_escola
    LEFT JOIN tabelas_seguranca_ocorrencias o ON o.id_regiao = r.id_regiao
    GROUP BY e.id_escola
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

@st.cache_data(ttl=60)
def carregar_ocorrencias():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM tabelas_seguranca_ocorrencias", conn)
    conn.close()
    return df

@st.cache_data(ttl=60)
def carregar_regioes():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM tabelas_contexto_regioes", conn)
    conn.close()
    return df

df_escolas = carregar_visao_escolas()
df_ocorrencias = carregar_ocorrencias()
df_regioes = carregar_regioes()

registrar_log(usuario_atual, perfil, "CONSULTA_PAINEL", "vw_alerta_vulnerabilidade")

# Métricas globais
total_alunos = df_escolas['total_alunos_ativos'].sum()
total_risco_evasao = int(df_escolas['alunos_risco_evasao'].sum())
iac = round((total_risco_evasao / total_alunos) * 100, 1) if total_alunos > 0 else 0
total_crimes_500m = int(df_escolas['crimes_500m'].sum())
escolas_criticas = len(df_escolas[df_escolas['ivs'] > 0.6])


# ==============================================================================
# PERFIL: GESTOR PÚBLICO
# ==============================================================================
if perfil == 'Gestor Público':
    st.markdown("""
    <div>
        <h2 style="font-size: 2rem; font-weight: 800; color: #0f172a; margin-bottom: 0;">Painel Executivo Integrado</h2>
        <p style="color: #64748b; font-weight: 500;">Função Analítica: <span style="background:#eff6ff; color:#2563eb; padding: 2px 6px; border-radius: 4px; font-weight: bold;">Sumarização</span> de dados SSP e SEC.</p>
    </div>
    """, unsafe_allow_html=True)

    tab_dash, tab_ia, tab_teoria = st.tabs([
        "📊 Dashboard & Simulador", "🤖 Copiloto IA", "📖 Quadro Teórico"
    ])

    # ── ABA 1: DASHBOARD E SIMULADOR ──
    with tab_dash:
        # KPIs customizados em HTML
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div class="metric-card blue">
                <div class="metric-info"><h4>Alunos Monitorados</h4><h2>{total_alunos:,}</h2></div>
                <div class="metric-icon blue"><i class="fas fa-users"></i></div>
            </div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="metric-card orange">
                <div class="metric-info"><h4>IAC (Risco Evasão)</h4><h2>{iac}%</h2></div>
                <div class="metric-icon orange"><i class="fas fa-graduation-cap"></i></div>
            </div>""", unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="metric-card red">
                <div class="metric-info"><h4>Crimes (Raio 500m)</h4><h2>{total_crimes_500m}</h2></div>
                <div class="metric-icon red"><i class="fas fa-person-rifle"></i></div>
            </div>""", unsafe_allow_html=True)
        with col4:
            st.markdown(f"""
            <div class="metric-card emerald">
                <div class="metric-info"><h4>Escolas Críticas</h4><h2>{escolas_criticas}</h2></div>
                <div class="metric-icon emerald"><i class="fas fa-school-flag"></i></div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
        # MÓDULO DE SIMULAÇÃO (Blend de Opções)
        st.markdown("""
        <div style="background: white; border-radius: 1rem; border: 1px solid #e2e8f0; overflow: hidden; margin-bottom: 2rem;">
            <div class="sim-header">
                <i class="fas fa-sliders" style="color: #60a5fa;"></i> Simulador de Intervenções e Políticas Públicas
                <span style="margin-left: auto; background: #2563eb; font-size: 0.75rem; padding: 2px 8px; border-radius: 99px;">SAD Core</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col_sim_l, col_sim_r = st.columns([5, 7])
        
        with col_sim_l:
            st.markdown("**1. Selecione a Escola/Região Alvo**")
            escola_sel = st.selectbox("Escola", df_escolas['nome_escola'], label_visibility="collapsed")
            esc = df_escolas[df_escolas['nome_escola'] == escola_sel].iloc[0]

            st.markdown("<div style='background:#eff6ff; padding:1rem; border-radius:1rem; border:1px solid #bfdbfe; margin-top:1rem;'>", unsafe_allow_html=True)
            st.markdown("**<i class='fas fa-money-bill-wave' style='color:#1e3a8a;'></i> 2. Alocação de Recursos (Milhões R$)**", unsafe_allow_html=True)
            orc_ssp = st.slider("Policiamento (SSP)", 0.0, 10.0, 3.5, 0.5)
            orc_sec = st.slider("Pedagógico (SEC)", 0.0, 10.0, 4.0, 0.5)
            st.markdown("</div>", unsafe_allow_html=True)

        with col_sim_r:
            st.markdown("**Status Atual da Escola**")
            col_d1, col_d2, col_d3 = st.columns(3)
            col_d1.metric("IVS", f"{esc['ivs']:.2f}")
            col_d2.metric("Crimes 500m", int(esc['crimes_500m']))
            col_d3.metric("Risco Evasão", int(esc['alunos_risco_evasao']))

            score = (esc['crimes_500m'] * 0.4) + (esc['alunos_risco_evasao'] * 1.5) + (esc['ivs'] * 100)

            # Lógica do Blend de Decisão conforme HTML do usuário
            if score > 150:
                if orc_ssp > orc_sec:
                    st.markdown(f"""
                    <div class="blend-box blend-critico">
                        <div style="font-size: 0.75rem; font-weight: bold; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 0.5rem;"><i class="fas fa-triangle-exclamation"></i> Ação Crítica Recomendada</div>
                        <h3 style="margin: 0 0 0.5rem 0; font-size: 1.5rem; font-weight: 700;">Blend A: Intervenção Ostensiva (Policial)</h3>
                        <p style="margin: 0; font-size: 0.875rem; line-height: 1.5; color: #fee2e2;">Risco altíssimo calculado ({score:.0f} pts). Como o orçamento SSP é maior, recomenda-se alocar <strong>Base Móvel da PM</strong> na porta da escola e expandir monitoramento COI. Evasão deve cair via sensação de segurança.</p>
                    </div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="blend-box blend-moderado">
                        <div style="font-size: 0.75rem; font-weight: bold; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 0.5rem;"><i class="fas fa-triangle-exclamation"></i> Ação Crítica Recomendada</div>
                        <h3 style="margin: 0 0 0.5rem 0; font-size: 1.5rem; font-weight: 700;">Blend B: Blindagem Social (Pedagógica)</h3>
                        <p style="margin: 0; font-size: 0.875rem; line-height: 1.5; color: #fff7ed;">Risco altíssimo calculado ({score:.0f} pts). Como orçamento SEC é prioritário, recomenda-se <strong>Turno Integral imediato</strong> e bolsa permanência para conter a força de atração do crime local (IVS alto).</p>
                    </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="blend-box blend-estavel">
                    <div style="font-size: 0.75rem; font-weight: bold; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 0.5rem;"><i class="fas fa-check-circle"></i> Ação Preventiva Recomendada</div>
                    <h3 style="margin: 0 0 0.5rem 0; font-size: 1.5rem; font-weight: 700;">Blend C: Manutenção Padrão</h3>
                    <p style="margin: 0; font-size: 0.875rem; line-height: 1.5; color: #ecfdf5;">Risco aceitável ({score:.0f} pts). Manter patrulha escolar padrão e acompanhamento de rotina da SEC. Orçamento pode ser contingenciado para zonas de maior IVS.</p>
                </div>""", unsafe_allow_html=True)

    # ── ABA 2: COPILOTO IA ──
    with tab_ia:
        st.header("Copiloto EduSeg — IA Multi-Fases")
        st.caption("Groq Llama 3 (Gratuito) + DuckDuckGo Search (Gratuito) · Zero Custo")

        api_key = st.sidebar.text_input("🔑 Groq API Key (Grátis)", type="password", help="Crie em console.groq.com")

        if api_key:
            from agente_eduseg import AgenteEduSeg
            agente = AgenteEduSeg(api_key=api_key)
            contexto_banco = f"Escola Selecionada: {escola_sel}, IVS: {esc['ivs']:.2f}, Risco Evasão: {esc['alunos_risco_evasao']}, Crimes 500m: {esc['crimes_500m']}"

            if "messages" not in st.session_state:
                st.session_state.messages = []
            for m in st.session_state.messages:
                with st.chat_message(m["role"]):
                    st.markdown(m["content"])
            if prompt := st.chat_input("Pergunte sobre dados reais ou peça recomendações"):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)
                with st.chat_message("assistant"):
                    ph = st.empty()
                    with st.spinner("Processando..."):
                        try:
                            res = agente.chat(prompt, st.session_state.messages[:-1], contexto_banco)
                            ph.markdown(res["response"])
                            if res["buscou_web"]:
                                st.caption(f"🌐 {res['fase']}")
                            st.session_state.messages.append({"role": "assistant", "content": res["response"]})
                        except Exception as e:
                            st.error(f"Erro: {e}")
        else:
            st.warning("👈 Insira sua Chave Groq gratuita na barra lateral para usar a IA.")

    # ── ABA 3: QUADRO TEÓRICO ──
    with tab_teoria:
        st.markdown("""
        <div class="teoria-card">
            <h3>Tipologia de Sistemas de Informação</h3>
            <ul style="color: #475569; font-size: 0.9rem; line-height: 1.6;">
                <li><strong>SPT / SIT (Processamento de Transações):</strong> Registra rotinas diárias operacionais. Ex: Sistema de catraca de ônibus escolar, folha de pagamento.</li>
                <li><strong>SIG (Informações Gerenciais):</strong> Consolida dados do SPT em relatórios de desempenho tático. Ex: Relatório mensal de notas.</li>
                <li><strong>SAD (Apoio à Decisão):</strong> Este protótipo! Analisa dados (Crimes + Evasão) para recomendar decisões semi-estruturadas (Onde alocar orçamento).</li>
                <li><strong>SIE (Informação Estratégica):</strong> Foca na alta direção. Dashboards macroeconômicos de longo prazo.</li>
                <li><strong>SE (Sistemas Especialistas):</strong> Captura o conhecimento de um especialista humano via regras "Se-Então". Integrado ao nosso KDD.</li>
                <li><strong>ERP (Enterprise Resource Planning):</strong> Integra todos os departamentos em um banco único. Ex: SAP.</li>
                <li><strong>KDD & BI (Business Intelligence):</strong> BI olha o passado. KDD descobre padrões ocultos para prever o futuro (Agrupamento, Associação).</li>
            </ul>
        </div>
        
        <div class="teoria-card">
            <h3>Funções Analíticas Aplicadas no Protótipo</h3>
            <ul style="color: #475569; font-size: 0.9rem; line-height: 1.6;">
                <li><strong>Sumarização:</strong> Visível no Dashboard. Técnicas estatísticas de agregação (Somas, Médias). Software comum: PowerBI.</li>
                <li><strong>Agrupamento (Clustering):</strong> Visível na aba KDD. Técnica K-Means. Agrupa entidades sem rótulo prévio baseado em similaridade geométrica. Software: Scikit-learn (Python).</li>
                <li><strong>Regressão:</strong> Visível na aba KDD. Acha a função matemática (Linha de tendência) que melhor explica a relação entre X (Crimes) e Y (Evasão).</li>
                <li><strong>Associação:</strong> Regras Apriori na aba KDD. Acha itens que ocorrem juntos frequentemente (Market Basket Analysis).</li>
            </ul>
        </div>

        <div class="teoria-card">
            <h3>Evidências Científicas: A Interrelação Segurança & Educação</h3>
            <ul style="color: #475569; font-size: 0.9rem; line-height: 1.6;">
                <li><strong>A Escola como Vetor de Proteção Social:</strong> Santos e Silva (2025/REASE) demonstram que ações puramente repressivas possuem baixa efetividade.</li>
                <li><strong>Redução da Criminalidade Baseada em Evidências:</strong> A pesquisa cita casos empíricos reais como a avaliação do Programa Fica Vivo! conduzida por Silva et al. (2018).</li>
                <li><strong>Currículo e Conscientização:</strong> Haroldo (Monografia UFMG) defende que o Estado deve usar a escola como ferramenta sistemática para distanciar o jovem da criminalidade.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)


# ==============================================================================
# PERFIL: ANALISTA KDD
# ==============================================================================
elif perfil == 'Analista KDD':
    st.markdown("""
    <div>
        <h2 style="font-size: 2rem; font-weight: 800; color: #0f172a; margin-bottom: 0;">Knowledge Discovery in Databases (KDD)</h2>
        <p style="color: #64748b; font-weight: 500;">Funções Analíticas: <span style="background:#faf5ff; color:#9333ea; padding: 2px 6px; border-radius: 4px; font-weight: bold;">Agrupamento</span>, <span style="background:#fff1f2; color:#e11d48; padding: 2px 6px; border-radius: 4px; font-weight: bold;">Regressão</span>, <span style="background:#f0fdfa; color:#0d9488; padding: 2px 6px; border-radius: 4px; font-weight: bold;">Associação</span>.</p>
    </div>
    """, unsafe_allow_html=True)
    
    registrar_log(usuario_atual, perfil, "ACESSO_KDD", "vw_alerta_vulnerabilidade")

    tab1, tab2, tab3, tab4, tab5, tab6, tab_ia = st.tabs([
        "📍 Agrupamento (K-Means)", "📈 Regressão Linear", "🔗 Associação (Apriori)", "📊 Delitos por Bairro", "🧠 Grafo 3D", "🔥 Matriz de Correlação", "🤖 Copiloto IA"
    ])

    # ── AGRUPAMENTO ──
    with tab1:
        st.markdown("""
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 1rem;">
            <div>
                <h3 style="margin:0; font-size:1.125rem; color:#1e293b;"><i class="fas fa-project-diagram" style="color:#a855f7;"></i> Agrupamento (Clustering)</h3>
                <p style="margin:0; font-size:0.75rem; color:#64748b;">Segmentação de Escolas (K-Means Mock)</p>
            </div>
            <span style="background:#f1f5f9; font-size:0.75rem; padding: 4px 8px; border-radius:4px; font-weight:bold;">X: Crimes | Y: Evasão</span>
        </div>
        """, unsafe_allow_html=True)

        X = df_escolas[['crimes_500m', 'alunos_risco_evasao']].values
        kmeans = KMeans(n_clusters=3, random_state=42, n_init=10).fit(X)

        fig, ax = plt.subplots(figsize=(10, 4.5))
        cores = ['#2ecc71', '#f39c12', '#e74c3c']
        labels_c = ['Estável', 'Moderado', 'Crítico']
        for i in range(3):
            mask = kmeans.labels_ == i
            ax.scatter(X[mask, 0], X[mask, 1], c=cores[i], s=250, alpha=0.85, label=labels_c[i], edgecolors='white', linewidths=1.5)
        for i, txt in enumerate(df_escolas['nome_escola']):
            ax.annotate(txt, (X[i, 0] + 3, X[i, 1] + 1), fontsize=8, color="#475569")
        ax.set_xlabel("Crimes no Raio de 500m (SSP)", color="#64748b")
        ax.set_ylabel("Risco Evasão (SEC)", color="#64748b")
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.legend(title="Cluster")
        st.pyplot(fig)

        st.markdown("<p style='font-size:0.8rem; color:#64748b;'><strong>Técnica:</strong> K-Means. O algoritmo agrupa as escolas em 3 clusters (Seguro, Atenção, Crítico) baseado na similaridade matemática das variáveis de violência e evasão, sem rótulos prévios.</p>", unsafe_allow_html=True)

    # ── REGRESSÃO ──
    with tab2:
        st.markdown("""
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 1rem;">
            <div>
                <h3 style="margin:0; font-size:1.125rem; color:#1e293b;"><i class="fas fa-chart-line" style="color:#f43f5e;"></i> Regressão Linear</h3>
                <p style="margin:0; font-size:0.75rem; color:#64748b;">Correlação: Entorno vs Desistência</p>
            </div>
            <span style="background:#f1f5f9; font-size:0.75rem; padding: 4px 8px; border-radius:4px; font-weight:bold;">Tendência</span>
        </div>
        """, unsafe_allow_html=True)

        X_reg = df_escolas[['crimes_500m']].values
        y_reg = df_escolas['alunos_risco_evasao'].values
        model = LinearRegression().fit(X_reg, y_reg)
        r2 = model.score(X_reg, y_reg)

        fig2, ax2 = plt.subplots(figsize=(10, 4.5))
        ax2.scatter(X_reg, y_reg, color='#f43f5e', s=150, label="Dados Reais", edgecolors='white', linewidths=1.5)
        ax2.plot(sorted(X_reg), model.predict(sorted(X_reg)), color='#3b82f6', linewidth=2, linestyle='--', label=f"Regressão (R²={r2:.2f})")
        ax2.set_xlabel("Volume de Crimes", color="#64748b")
        ax2.set_ylabel("Volume de Evasão", color="#64748b")
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        ax2.legend()
        st.pyplot(fig2)
        st.markdown("<p style='font-size:0.8rem; color:#64748b;'><strong>Técnica:</strong> Regressão Linear Simples. Permite prever a variável dependente (Alunos em Risco de Evasão) com base na variável independente (Crimes no raio de 500m).</p>", unsafe_allow_html=True)

    # ── ASSOCIAÇÃO (APRIORI) ──
    with tab3:
        st.markdown("""
        <div style="display:flex; align-items:center; gap:12px; margin-bottom: 1rem;">
            <div style="width:40px; height:40px; background:#ccfbf1; color:#0d9488; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:1.2rem;">
                <i class="fas fa-link"></i>
            </div>
            <div>
                <h3 style="margin:0; font-size:1.125rem; color:#1e293b;">Regras de Associação (Algoritmo Apriori)</h3>
                <p style="margin:0; font-size:0.875rem; color:#64748b;">Descoberta de padrões frequentes na base de dados (Se A, então B).</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        df_bin = pd.DataFrame({
            'IVS_Alto': df_escolas['ivs'] > 0.6,
            'Crimes_Alto': df_escolas['crimes_500m'] > df_escolas['crimes_500m'].median(),
            'Evasao_Alta': df_escolas['alunos_risco_evasao'] > df_escolas['alunos_risco_evasao'].median(),
            'Assiduidade_Baixa': df_escolas['media_assiduidade'] < 75,
            'Sem_Iluminacao': df_escolas['iluminacao'] == 0,
            'Ocorr_Disc_Alta': df_escolas['total_ocorrencias_disc'] > df_escolas['total_ocorrencias_disc'].median(),
        })

        try:
            itemsets = apriori(df_bin, min_support=0.2, use_colnames=True)
            if len(itemsets) > 0:
                regras = association_rules(itemsets, metric="confidence", min_threshold=0.5, num_itemsets=len(itemsets))
                if not regras.empty:
                    for _, row in regras.head(5).iterrows():
                        ant = ", ".join([str(i) for i in row['antecedents']])
                        con = ", ".join([str(i) for i in row['consequents']])
                        st.markdown(f"""
                        <div style="background:#f8fafc; border:1px solid #e2e8f0; border-left:4px solid #14b8a6; padding:12px 16px; border-radius:8px; margin-bottom:8px;">
                            <span style="background:#e2e8f0; font-size:0.7rem; padding:2px 6px; border-radius:4px; font-weight:bold; margin-right:4px;">SE</span> 
                            {ant} 
                            <span style="background:#e2e8f0; font-size:0.7rem; padding:2px 6px; border-radius:4px; font-weight:bold; margin:0 4px;">ENTÃO</span> 
                            <span style="color:#0d9488; font-weight:bold;">{con}</span><br>
                            <div style="margin-top:6px; font-size:0.8rem; color:#64748b;">
                                Suporte: <strong>{row['support']*100:.0f}%</strong> · Confiança: <strong>{row['confidence']*100:.0f}%</strong> · Lift: <strong>{row['lift']:.2f}</strong>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("Nenhuma regra com confiança ≥ 50% encontrada.")
            else:
                st.info("Nenhum itemset frequente encontrado com suporte ≥ 20%.")
        except Exception as e:
            st.error(f"Erro no Apriori: {e}")

    # ── DELITOS POR BAIRRO ──
    with tab4:
        st.subheader("Distribuição de Delitos por Tipo e Bairro")
        df_merged = df_ocorrencias.merge(df_regioes, left_on='id_regiao', right_on='id_regiao')
        pivot = df_merged.groupby(['nome_bairro', 'tipo_delito']).size().unstack(fill_value=0)
        fig3, ax3 = plt.subplots(figsize=(10, 4.5))
        pivot.plot(kind='bar', stacked=True, ax=ax3, colormap='Set2')
        ax3.spines['top'].set_visible(False)
        ax3.spines['right'].set_visible(False)
        ax3.set_xlabel("")
        ax3.legend(title="Tipo", fontsize=8, loc='upper right')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        st.pyplot(fig3)

    # ── GRAFO 3D ──
    with tab5:
        def gerar_grafo_inline():
            nodes = []
            links = []
            nodes.append({"id": "sad", "label": "SAD-EduSeg", "type": "auditoria", "detail": "Sistema Central"})
            for _, r in df_regioes.iterrows():
                rid = f"reg_{r['id_regiao']}"
                nodes.append({"id": rid, "label": r['nome_bairro'], "type": "regiao", "detail": f"IVS: {r['indice_vulnerabilidade_social']:.2f}"})
                links.append({"source": "sad", "target": rid})
            for _, e in df_escolas.iterrows():
                eid = f"esc_{e['id_escola']}"
                rid = f"reg_{e['id_escola']}"
                nodes.append({"id": eid, "label": e['nome_escola'], "type": "escola", "detail": f"Alunos: {e['total_alunos_ativos']}"})
                links.append({"source": rid, "target": eid})
            ocorr = df_ocorrencias.groupby('id_regiao').size().reset_index(name='total')
            for _, o in ocorr.iterrows():
                oid = f"ocorr_{int(o['id_regiao'])}"
                rid = f"reg_{int(o['id_regiao'])}"
                nodes.append({"id": oid, "label": f"BOs ({int(o['total'])})", "type": "ocorrencia", "detail": f"Total: {int(o['total'])}"})
                links.append({"source": rid, "target": oid})
            return {"nodes": nodes, "links": links}
            
        st.subheader("Grafo de Conhecimento 3D — Arquitetura do Banco")
        st.caption("Regiões → Escolas → Ocorrências SSP-BA")
        graph_data = gerar_grafo_inline()
        html_path = os.path.join(BASE_DIR, "grafo_eduseg.html")
        try:
            with open(html_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            html_content = html_content.replace("GRAPH_DATA_PLACEHOLDER", json.dumps(graph_data, ensure_ascii=False))
            components.html(html_content, height=600, scrolling=False)
        except FileNotFoundError:
            st.error("grafo_eduseg.html não encontrado.")

    # ── CORRELAÇÃO ──
    with tab6:
        st.subheader("Matriz de Correlação de Indicadores (Heatmap)")
        st.caption("Analise as interdependências numéricas entre crimes, vulnerabilidade e evasão escolar.")
        
        # Seleciona apenas colunas numéricas de interesse
        colunas_interesse = ['ivs', 'renda', 'crimes_500m', 'media_assiduidade', 'alunos_risco_evasao', 'total_ocorrencias_disc']
        df_corr = df_escolas[colunas_interesse].corr()
        
        fig_corr, ax_corr = plt.subplots(figsize=(10, 6))
        sns.heatmap(df_corr, annot=True, cmap="coolwarm", fmt=".2f", linewidths=.5, ax=ax_corr)
        ax_corr.set_xticklabels(['IVS', 'Renda', 'Crimes', 'Assiduidade', 'Evasão', 'Ocorr. Disc.'], rotation=45, ha='right')
        ax_corr.set_yticklabels(['IVS', 'Renda', 'Crimes', 'Assiduidade', 'Evasão', 'Ocorr. Disc.'], rotation=0)
        plt.tight_layout()
        st.pyplot(fig_corr)

    # ── COPILOTO IA (Analista) ──
    with tab_ia:
        st.header("Agente de Mineração de Dados")
        st.caption("Solicite análises complexas sobre a matriz de correlação ou regras Apriori. Zero custo (Groq).")

        api_key = st.sidebar.text_input("🔑 Groq API Key (Grátis) - KDD", type="password", key="kdd_groq")

        if api_key:
            from agente_eduseg import AgenteEduSeg
            agente = AgenteEduSeg(api_key=api_key)
            contexto_kdd = f"Escolas em Risco: {escolas_criticas}, Maior correlação evasão x crimes, Evasão Total: {total_risco_evasao}."
            
            if "messages_kdd" not in st.session_state:
                st.session_state.messages_kdd = []
            for m in st.session_state.messages_kdd:
                with st.chat_message(m["role"]):
                    st.markdown(m["content"])
            if prompt := st.chat_input("Ex: Qual modelo preditivo usar para as escolas críticas?"):
                st.session_state.messages_kdd.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)
                with st.chat_message("assistant"):
                    ph = st.empty()
                    with st.spinner("Minerando..."):
                        try:
                            res = agente.chat(prompt, st.session_state.messages_kdd[:-1], contexto_kdd)
                            ph.markdown(res["response"])
                            st.session_state.messages_kdd.append({"role": "assistant", "content": res["response"]})
                        except Exception as e:
                            st.error(f"Erro: {e}")
        else:
            st.warning("👈 Insira sua Chave Groq na barra lateral para ativar o Agente KDD.")


# ==============================================================================
# PERFIL: ADMIN DOMÍNIO
# ==============================================================================
elif perfil == 'Admin Domínio':
    st.markdown("""
    <div>
        <h2 style="font-size: 2rem; font-weight: 800; color: #0f172a; margin-bottom: 0;">Governança e Tabelas do Banco</h2>
        <p style="color: #64748b; font-weight: 500;">Visualização da estrutura do banco (por cadastro) e logs da LGPD.</p>
    </div>
    """, unsafe_allow_html=True)
    registrar_log(usuario_atual, perfil, "ACESSO_ADMIN", "sistema_logs_auditoria")

    tab_dados, tab_audit, tab_users = st.tabs(["📋 Tabelas (Cadastros)", "🔒 Auditoria LGPD", "👥 Usuários"])

    with tab_dados:
        st.markdown("### <i class='fas fa-database' style='color:#3b82f6;'></i> Cadastro: Entidade Escolas (Critérios Base)", unsafe_allow_html=True)
        st.caption("Dados reais formatados para o modelo de decisão.")
        st.dataframe(df_escolas, hide_index=True, use_container_width=True)
        
        st.markdown("### Cadastro: Regiões de Salvador")
        st.dataframe(df_regioes, hide_index=True, use_container_width=True)

    with tab_audit:
        st.markdown("### <i class='fas fa-user-shield' style='color:#10b981;'></i> Trilha de Auditoria Imutável (Log LGPD)", unsafe_allow_html=True)
        st.caption("Registro imutável — Quem acessou, quando e qual tabela.")
        conn = get_db_connection()
        df_logs = pd.read_sql_query("SELECT * FROM sistema_logs_auditoria ORDER BY data_hora_acesso DESC LIMIT 50", conn)
        conn.close()
        st.dataframe(df_logs, hide_index=True, use_container_width=True)

    with tab_users:
        st.subheader("Gerenciar Usuários (Controle de Acesso)")
        conn = get_db_connection()
        df_users = pd.read_sql_query("SELECT id, nome, perfil FROM usuarios", conn)
        conn.close()
        st.dataframe(df_users, hide_index=True, use_container_width=True)

        with st.form("add_user"):
            st.write("Cadastrar Novo Usuário")
            u_nome = st.text_input("Nome")
            u_senha = st.text_input("Senha", type="password")
            u_perfil = st.selectbox("Perfil", ["Gestor Público", "Analista KDD", "Admin Domínio"])
            if st.form_submit_button("Criar Usuário"):
                conn = get_db_connection()
                conn.execute("INSERT INTO usuarios (nome, senha, perfil) VALUES (?, ?, ?)", (u_nome, u_senha, u_perfil))
                conn.commit()
                conn.close()
                st.success("Usuário criado!")
                registrar_log(usuario_atual, perfil, "CRIAR_USUARIO", "usuarios")
                st.rerun()
