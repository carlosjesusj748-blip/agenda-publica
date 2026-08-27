import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestClassifier
from mlxtend.frequent_patterns import apriori, association_rules
import sqlite3
import database
import time
import os
import json
import unicodedata
from datetime import datetime
from fpdf import FPDF

# Caminho absoluto para o banco de dados
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "sad_eduseg.db")

# Garante inicialização correta do banco
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
# CONFIGURAÇÃO DA PÁGINA & ESTILO
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SAD-EduSeg | Governo da Bahia",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp { background-color: #f8fafc; }
    
    /* KPI Cards */
    .metric-card {
        background: #ffffff;
        border-radius: 1rem;
        padding: 1.25rem 1.5rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02), 0 2px 4px -2px rgba(0,0,0,0.02);
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05);
    }
    .metric-card.blue { border-left: 5px solid #2563eb; }
    .metric-card.orange { border-left: 5px solid #ea580c; }
    .metric-card.red { border-left: 5px solid #dc2626; }
    .metric-card.emerald { border-left: 5px solid #059669; }
    
    .metric-info h4 { margin: 0; font-size: 0.85rem; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }
    .metric-info h2 { margin: 0.25rem 0 0 0; font-size: 1.85rem; color: #0f172a; font-weight: 800; }
    
    .metric-icon {
        width: 3.2rem; height: 3.2rem;
        border-radius: 1rem;
        display: flex; align-items: center; justify-content: center;
        font-size: 1.35rem;
    }
    .metric-icon.blue { background-color: #eff6ff; color: #2563eb; }
    .metric-icon.orange { background-color: #fff7ed; color: #ea580c; }
    .metric-icon.red { background-color: #fef2f2; color: #dc2626; }
    .metric-icon.emerald { background-color: #ecfdf5; color: #059669; }

    /* Simulador Container */
    .sim-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: white;
        padding: 1.1rem 1.5rem;
        border-top-left-radius: 1rem;
        border-top-right-radius: 1rem;
        font-weight: 700;
        display: flex; align-items: center; justify-content: space-between;
    }
    
    .blend-box {
        padding: 1.5rem;
        border-radius: 1rem;
        color: white;
        text-align: left;
        margin-top: 1rem;
    }
    .blend-critico { background: linear-gradient(135deg, #dc2626, #991b1b); box-shadow: 0 10px 15px -3px rgba(220, 38, 38, 0.25); }
    .blend-moderado { background: linear-gradient(135deg, #ea580c, #c2410c); box-shadow: 0 10px 15px -3px rgba(234, 88, 12, 0.25); }
    .blend-estavel { background: linear-gradient(135deg, #059669, #047857); box-shadow: 0 10px 15px -3px rgba(5, 150, 105, 0.25); }
    
    .teoria-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 1rem;
        padding: 1.5rem;
        margin-bottom: 1.25rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }
    .teoria-card h3 { color: #1e40af; border-bottom: 1px solid #f1f5f9; padding-bottom: 0.6rem; font-size: 1.15rem; font-weight: 700; }
    
    .badge-prio {
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
    }
    .badge-alta { background-color: #fee2e2; color: #dc2626; }
    .badge-media { background-color: #ffedd5; color: #ea580c; }
    .badge-baixa { background-color: #d1fae5; color: #059669; }
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
    <div style="display:flex; align-items:center; gap:12px; margin-bottom: 24px;">
        <div style="background:#2563eb; color:white; width:44px; height:44px; border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:22px; box-shadow: 0 4px 6px rgba(37,99,235,0.3);">
            <i class="fas fa-shield-halved"></i>
        </div>
        <div>
            <h2 style="margin:0; font-size:19px; font-weight:800; color:#f8fafc; letter-spacing:-0.5px;">SAD-EduSeg</h2>
            <p style="margin:0; font-size:12px; color:#94a3b8; font-weight:500;">Bahia · Gestão de Políticas</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    if st.session_state['usuario'] is None:
        tab_login, tab_criar, tab_recuperar = st.tabs(["Login", "Criar Conta", "Recuperar"])

        with tab_login:
            st.subheader("Autenticação")
            nome_input = st.text_input("Usuário", key="login_nome", value="Gestor Publico")
            senha_input = st.text_input("Senha", type="password", key="login_senha", value="123")
            if st.button("Entrar no SAD", type="primary", use_container_width=True):
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
                        st.error("Nome já cadastrado.")
                    else:
                        conn.execute("INSERT INTO usuarios (nome, senha, perfil) VALUES (?, ?, ?)", (c_nome, c_senha, c_perfil))
                        conn.commit()
                        st.success("Criado com sucesso! Efetue o login.")
                    conn.close()

        with tab_recuperar:
            st.subheader("Recuperação")
            r_nome = st.text_input("Nome de Usuário", key="recuperar_nome")
            if st.button("Consultar", use_container_width=True):
                if r_nome:
                    conn = get_db_connection()
                    user = conn.execute("SELECT senha, perfil FROM usuarios WHERE nome = ?", (r_nome,)).fetchone()
                    conn.close()
                    if user:
                        st.info(f"🔑 Senha: **{user['senha']}** ({user['perfil']})")
                    else:
                        st.error("Usuário não encontrado.")
    else:
        st.markdown(f"""
        <div style="background:#1e293b; padding:12px 16px; border-radius:10px; border:1px solid #334155; margin-bottom:12px;">
            <div style="font-size:11px; color:#94a3b8; text-transform:uppercase; font-weight:700;">Usuário Autenticado</div>
            <div style="font-size:15px; color:#f8fafc; font-weight:700;">{st.session_state['usuario']}</div>
            <div style="font-size:12px; color:#38bdf8; font-weight:600;"><i class="fas fa-id-badge"></i> {st.session_state['perfil']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Encerrar Sessão", use_container_width=True):
            registrar_log(st.session_state['usuario'], st.session_state['perfil'], "LOGOUT", "usuarios")
            st.session_state['usuario'] = None
            st.session_state['perfil'] = None
            if 'messages' in st.session_state:
                del st.session_state['messages']
            if 'messages_kdd' in st.session_state:
                del st.session_state['messages_kdd']
            st.rerun()

    st.markdown("---")
    st.caption("EAUFBA · SAD Integrado SSP/SEC")
    st.caption("LGPD Compliance · Open Data INEP")

if st.session_state['usuario'] is None:
    st.title("SAD-EduSeg: Inteligência Integrada Segurança & Educação 🛡️📚")
    st.subheader("Sistema de Apoio à Decisão Baseado em Evidências — Estado da Bahia")
    st.info("Utilize a barra lateral para acessar o sistema. Perfis de demonstração: **Gestor Publico** (123) · **Analista KDD** (123) · **Admin Dominio** (admin)")
    
    st.markdown("---")
    st.markdown("""
    ### 🏛️ Fundamentação Científica do SAD
    O **SAD-EduSeg** implementa os preceitos de Perottoni et al. (2001) para decisões semiestruturadas e o framework KDD (Coradine et al., 2011), integrando:
    1. **Sumarização Executiva:** Indicadores consolidados de criminalidade territorial e fluxo escolar.
    2. **Agrupamento (K-Means):** Segmentação de unidades escolares por homogeneidade de vulnerabilidade.
    3. **Regressão Linear:** Relação funcional preditiva entre violência urbana no entorno (500m) e evasão escolar.
    4. **Associação (Apriori):** Mineração de regras de coocorrência multidimensional para ação preventiva.
    """)
    st.stop()

# ==============================================================================
# CARREGAMENTO DE DADOS REAIS
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

# Cálculos Globais
total_alunos = int(df_escolas['total_alunos_ativos'].sum())
total_risco_evasao = int(df_escolas['alunos_risco_evasao'].sum())
iac = round((total_risco_evasao / total_alunos) * 100, 1) if total_alunos > 0 else 0
total_crimes_500m = int(df_escolas['crimes_500m'].sum())
escolas_criticas = len(df_escolas[df_escolas['ivs'] > 0.6])

def sanitizar_texto_pdf(txt: str) -> str:
    """Remove caracteres especiais e acentuação para evitar quebra no FPDF standard."""
    if not txt:
        return ""
    nfkd = unicodedata.normalize('NFKD', str(txt))
    return nfkd.encode('ASCII', 'ignore').decode('ASCII')

def gerar_pdf_relatorio(escola, ivs, crimes, evasao, score, rec_titulo, rec_texto):
    try:
        pdf = FPDF(orientation='P', unit='mm', format='A4')
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Cabeçalho
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(w=0, h=10, text="SAD-EduSeg - Relatorio Oficial de Decisao", ln=True, align="C")
        pdf.set_font("Helvetica", "I", 10)
        pdf.cell(w=0, h=6, text=f"Governo do Estado da Bahia | Emitido em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align="C")
        pdf.ln(8)
        
        # Seção 1: Diagnóstico
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(w=0, h=8, text=f"1. Unidade Escolar: {sanitizar_texto_pdf(escola)}", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(w=0, h=6, text=f"- Indice de Vulnerabilidade Social (IVS): {ivs:.2f}", ln=True)
        pdf.cell(w=0, h=6, text=f"- Ocorrencias Criminais (Raio 500m): {crimes}", ln=True)
        pdf.cell(w=0, h=6, text=f"- Alunos em Risco Iminente de Evasao: {evasao}", ln=True)
        pdf.cell(w=0, h=6, text=f"- Score Integrado de Risco (KDD): {score:.0f} pts", ln=True)
        pdf.ln(6)
        
        # Seção 2: Recomendação
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(w=0, h=8, text="2. Diretriz Estrategica Recomendada (Blend de Opcoes):", ln=True)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(w=0, h=7, text=sanitizar_texto_pdf(rec_titulo), ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(w=0, h=6, text=sanitizar_texto_pdf(rec_texto))
        pdf.ln(8)
        
        # Rodapé de Governança
        pdf.set_font("Helvetica", "I", 8)
        pdf.cell(w=0, h=6, text="Documento gerado em conformidade com as diretrizes de governanca de dados abertos e LGPD.", ln=True, align="C")
        
        return bytes(pdf.output())
    except Exception as e:
        # Fallback de segurança para nunca crashar a UI
        pdf_fallback = FPDF()
        pdf_fallback.add_page()
        pdf_fallback.set_font("Helvetica", size=12)
        pdf_fallback.cell(w=0, h=10, text=f"Relatorio SAD-EduSeg: {sanitizar_texto_pdf(escola)}", ln=True)
        pdf_fallback.cell(w=0, h=10, text=f"Score: {score:.0f} pts", ln=True)
        return bytes(pdf_fallback.output())

@st.cache_data
def treinar_modelo_rf_convivencia():
    np.random.seed(42)
    n_amostras = 300
    
    data = {
        'id_amostra': range(1, n_amostras + 1),
        'faltas_consecutivas': np.random.randint(0, 10, size=n_amostras),
        'queda_notas_pct': np.random.uniform(0, 50, size=n_amostras),
        'historico_conflitos': np.random.randint(0, 5, size=n_amostras),
        'acesso_rede_suspeito': np.random.choice([0, 1], size=n_amostras, p=[0.85, 0.15]),
        'risco_entorno_bairro': np.random.uniform(1, 10, size=n_amostras)
    }
    df_rf = pd.DataFrame(data)
    df_rf['precisa_intervencao'] = ((df_rf['faltas_consecutivas'] > 5) | 
                                    (df_rf['queda_notas_pct'] > 30) | 
                                    (df_rf['acesso_rede_suspeito'] == 1) |
                                    ((df_rf['historico_conflitos'] >= 2) & (df_rf['risco_entorno_bairro'] > 7))).astype(int)
    
    X = df_rf[['faltas_consecutivas', 'queda_notas_pct', 'historico_conflitos', 'acesso_rede_suspeito', 'risco_entorno_bairro']]
    y = df_rf['precisa_intervencao']
    
    rf = RandomForestClassifier(n_estimators=100, random_state=42)
    rf.fit(X, y)
    
    df_rf['score_risco_pct'] = rf.predict_proba(X)[:, 1] * 100
    
    features = ['Faltas Consecutivas', 'Queda de Notas (%)', 'Histórico Conflitos', 'Logs Wi-Fi Suspeitos', 'Risco Entorno Bairro']
    importances = rf.feature_importances_
    df_imp = pd.DataFrame({'Feature': features, 'Importancia': importances}).sort_values('Importancia', ascending=True)
    
    return rf, df_rf, df_imp

# ==============================================================================
# PERFIL: GESTOR PÚBLICO
# ==============================================================================
if perfil == 'Gestor Público':
    st.markdown("""
    <div>
        <h2 style="font-size: 2rem; font-weight: 800; color: #0f172a; margin-bottom: 2px;">Painel Executivo Integrado</h2>
        <p style="color: #64748b; font-weight: 500; margin-bottom: 1.5rem;">Função Analítica Principal: <span style="background:#eff6ff; color:#2563eb; padding: 3px 8px; border-radius: 6px; font-weight: 700;">Sumarização & Alocação de Recursos</span></p>
    </div>
    """, unsafe_allow_html=True)

    tab_dash, tab_prio, tab_clima, tab_ia, tab_teoria = st.tabs([
        "📊 Painel & Simulador", "🎯 Matriz de Priorização", "🛡️ Clima & Convivência (IA)", "🤖 Copiloto IA", "📖 Base Teórica"
    ])

    # ── ABA 1: DASHBOARD E SIMULADOR ──
    with tab_dash:
        # Cards de KPI
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"""
            <div class="metric-card blue">
                <div class="metric-info"><h4>Alunos Monitorados</h4><h2>{total_alunos:,}</h2></div>
                <div class="metric-icon blue"><i class="fas fa-users"></i></div>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="metric-card orange">
                <div class="metric-info"><h4>IAC (Risco Evasão)</h4><h2>{iac}%</h2></div>
                <div class="metric-icon orange"><i class="fas fa-graduation-cap"></i></div>
            </div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
            <div class="metric-card red">
                <div class="metric-info"><h4>Crimes (Raio 500m)</h4><h2>{total_crimes_500m:,}</h2></div>
                <div class="metric-icon red"><i class="fas fa-shield-halved"></i></div>
            </div>""", unsafe_allow_html=True)
        with c4:
            st.markdown(f"""
            <div class="metric-card emerald">
                <div class="metric-info"><h4>Escolas Prioritárias</h4><h2>{escolas_criticas}</h2></div>
                <div class="metric-icon emerald"><i class="fas fa-school-flag"></i></div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
        # Módulo do Simulador
        st.markdown("""
        <div style="background: white; border-radius: 1rem; border: 1px solid #e2e8f0; overflow: hidden; margin-bottom: 1.5rem;">
            <div class="sim-header">
                <div><i class="fas fa-sliders" style="color: #60a5fa; margin-right: 8px;"></i> <strong>Motor de Inferência: Simulador de Intervenções (Blend de Opções)</strong></div>
                <span style="background: #2563eb; font-size: 0.75rem; padding: 3px 10px; border-radius: 9999px; font-weight: 700;">Decisão Preditiva</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col_sim_l, col_sim_r = st.columns([5, 7])
        
        with col_sim_l:
            st.markdown("**1. Selecionar Unidade Escolar**")
            escola_sel = st.selectbox("Escola Alvo", df_escolas['nome_escola'], label_visibility="collapsed")
            esc = df_escolas[df_escolas['nome_escola'] == escola_sel].iloc[0]

            st.markdown("<div style='background:#eff6ff; padding:1.2rem; border-radius:1rem; border:1px solid #bfdbfe; margin-top:1rem;'>", unsafe_allow_html=True)
            st.markdown("<strong style='color:#1e3a8a;'><i class='fas fa-sack-dollar'></i> 2. Alocação Orçamentária Simulada (R$ Milhões)</strong>", unsafe_allow_html=True)
            orc_ssp = st.slider("Policiamento Preventivo e COI (SSP)", 0.0, 10.0, 3.5, 0.5)
            orc_sec = st.slider("Apoio Pedagógico e Tempo Integral (SEC)", 0.0, 10.0, 4.0, 0.5)
            st.markdown("</div>", unsafe_allow_html=True)

        with col_sim_r:
            score = (esc['crimes_500m'] * 0.4) + (esc['alunos_risco_evasao'] * 1.5) + (esc['ivs'] * 100)
            
            # Gauge Interativo do Score de Risco
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = score,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': f"Score de Risco Integrado: {escola_sel[:25]}...", 'font': {'size': 14, 'color': '#1e293b'}},
                gauge = {
                    'axis': {'range': [None, 300], 'tickwidth': 1, 'tickcolor': "#94a3b8"},
                    'bar': {'color': "#1e293b"},
                    'bgcolor': "white",
                    'borderwidth': 2,
                    'bordercolor': "#e2e8f0",
                    'steps': [
                        {'range': [0, 100], 'color': '#d1fae5'},
                        {'range': [100, 180], 'color': '#ffedd5'},
                        {'range': [180, 300], 'color': '#fee2e2'}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 200
                    }
                }
            ))
            fig_gauge.update_layout(height=200, margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_gauge, use_container_width=True)

            # Lógica do Blend de Decisão
            if score > 150:
                if orc_ssp > orc_sec:
                    rt = "Blend A: Intervenção Ostensiva e Segurança Perimetral"
                    rx = f"Risco elevado ({score:.0f} pts). Como a alocação para a SSP (R$ {orc_ssp}M) é prioritária, recomenda-se Base Móvel da PM no portão e ampliação das câmeras do COI. A redução da sensação de medo viabiliza o retorno seguro dos alunos."
                    st.markdown(f"""
                    <div class="blend-box blend-critico">
                        <div style="font-size: 0.75rem; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase;"><i class="fas fa-triangle-exclamation"></i> Diretriz de Alta Prioridade</div>
                        <h3 style="margin: 0.25rem 0 0.5rem 0; font-size: 1.35rem; font-weight: 800;">{rt}</h3>
                        <p style="margin: 0; font-size: 0.9rem; line-height: 1.5; color: #fee2e2;">{rx}</p>
                    </div>""", unsafe_allow_html=True)
                else:
                    rt = "Blend B: Blindagem Social e Permanência Estudantil"
                    rx = f"Risco elevado ({score:.0f} pts). Com o orçamento direcionado à SEC (R$ {orc_sec}M), a prioridade é a conversão para Tempo Integral imediato, ampliação do Bolsa Presença e atividades de contraturno para conter a atratividade do crime na região."
                    st.markdown(f"""
                    <div class="blend-box blend-moderado">
                        <div style="font-size: 0.75rem; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase;"><i class="fas fa-triangle-exclamation"></i> Diretriz Pedagógica Prioritária</div>
                        <h3 style="margin: 0.25rem 0 0.5rem 0; font-size: 1.35rem; font-weight: 800;">{rt}</h3>
                        <p style="margin: 0; font-size: 0.9rem; line-height: 1.5; color: #fff7ed;">{rx}</p>
                    </div>""", unsafe_allow_html=True)
            else:
                rt = "Blend C: Manutenção Preventiva e Policiamento Comunitário"
                rx = f"Risco sob controle ({score:.0f} pts). Manter patrulhamento escolar padrão da PM e acompanhamento contínuo da frequência pela SEC. Recursos podem ser realocados para regiões de maior vulnerabilidade."
                st.markdown(f"""
                <div class="blend-box blend-estavel">
                    <div style="font-size: 0.75rem; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase;"><i class="fas fa-circle-check"></i> Ação Preventiva</div>
                    <h3 style="margin: 0.25rem 0 0.5rem 0; font-size: 1.35rem; font-weight: 800;">{rt}</h3>
                    <p style="margin: 0; font-size: 0.9rem; line-height: 1.5; color: #ecfdf5;">{rx}</p>
                </div>""", unsafe_allow_html=True)
                
            st.markdown("<br>", unsafe_allow_html=True)
            pdf_bytes = gerar_pdf_relatorio(escola_sel, esc['ivs'], esc['crimes_500m'], esc['alunos_risco_evasao'], score, rt, rx)
            st.download_button(label="📄 Exportar Relatório Oficial em PDF", data=pdf_bytes, file_name=f"Relatorio_SAD_{escola_sel[:12].replace(' ', '_')}.pdf", mime="application/pdf", use_container_width=True)

    # ── ABA 2: MATRIZ DE PRIORIZAÇÃO DE INVESTIMENTOS ──
    with tab_prio:
        st.markdown("""
        <div>
            <h3 style="margin:0; font-size:1.35rem; color:#0f172a; font-weight:800;">Matriz de Priorização Estratégica de Investimentos</h3>
            <p style="color:#64748b; font-size:0.9rem;">Cruzamento multicritério para decisão orçamentária entre todas as unidades da rede.</p>
        </div>
        """, unsafe_allow_html=True)
        
        df_prio = df_escolas.copy()
        df_prio['score_total'] = (df_prio['crimes_500m'] * 0.4) + (df_prio['alunos_risco_evasao'] * 1.5) + (df_prio['ivs'] * 100)
        df_prio['nivel_prioridade'] = pd.cut(
            df_prio['score_total'],
            bins=[-np.inf, 120, 180, np.inf],
            labels=['Baixa (Preventiva)', 'Média (Atenção)', 'Alta (Urgente)']
        )
        df_prio = df_prio.sort_values(by='score_total', ascending=False).reset_index(drop=True)

        col_p1, col_p2 = st.columns([7, 5])
        
        with col_p1:
            fig_scat_prio = px.scatter(
                df_prio,
                x='crimes_500m',
                y='alunos_risco_evasao',
                size='score_total',
                color='nivel_prioridade',
                hover_name='nome_escola',
                hover_data={'bairro': True, 'ivs': ':.2f', 'score_total': ':.0f'},
                color_discrete_map={'Alta (Urgente)': '#dc2626', 'Média (Atenção)': '#ea580c', 'Baixa (Preventiva)': '#059669'},
                title="Matriz de Decisão: Volume de Crimes vs Risco de Evasão",
                labels={'crimes_500m': 'Crimes no Entorno (500m)', 'alunos_risco_evasao': 'Alunos em Risco de Evasão'}
            )
            fig_scat_prio.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(248,250,252,0.8)')
            st.plotly_chart(fig_scat_prio, use_container_width=True)
            
        with col_p2:
            st.markdown("#### Ranking de Alocação Prioritária")
            tabela_apresentacao = df_prio[['nome_escola', 'bairro', 'score_total', 'nivel_prioridade']].copy()
            tabela_apresentacao.columns = ['Escola', 'Bairro', 'Score', 'Prioridade']
            tabela_apresentacao['Score'] = tabela_apresentacao['Score'].round(0).astype(int)
            st.dataframe(tabela_apresentacao, use_container_width=True, hide_index=True)

    # ── ABA 3: CLIMA & CONVIVÊNCIA ESCOLAR (IA) ──
    with tab_clima:
        st.markdown("""
        <div>
            <h3 style="margin:0; font-size:1.35rem; color:#0f172a; font-weight:800;">Monitoramento de Convivência & Clima Escolar</h3>
            <p style="color:#64748b; font-size:0.9rem;">Detecção antecipada de vulnerabilidades, conflitos e prevenção de evasão via IA (Random Forest).</p>
        </div>
        """, unsafe_allow_html=True)

        _, df_rf_sim, _ = treinar_modelo_rf_convivencia()
        
        c_clima1, c_clima2, c_clima3 = st.columns([4, 4, 4])
        
        taxa_critica = (df_rf_sim['score_risco_pct'] > 75).mean() * 100
        taxa_moderada = ((df_rf_sim['score_risco_pct'] >= 40) & (df_rf_sim['score_risco_pct'] <= 75)).mean() * 100
        clima_geral = 100 - (df_rf_sim['score_risco_pct'].mean() * 0.8)
        
        with c_clima1:
            fig_therm = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = clima_geral,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Índice de Clima Escolar Médio", 'font': {'size': 13}},
                gauge = {
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "#059669"},
                    'steps': [
                        {'range': [0, 50], 'color': '#fee2e2'},
                        {'range': [50, 75], 'color': '#ffedd5'},
                        {'range': [75, 100], 'color': '#d1fae5'}
                    ]
                }
            ))
            fig_therm.update_layout(height=180, margin=dict(l=10, r=10, t=30, b=10), paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_therm, use_container_width=True)
            
        with c_clima2:
            st.metric("Alerta Crítico (> 75% Risco)", f"{taxa_critica:.1f}% das turmas", delta="Atenção imediata", delta_color="inverse")
            st.metric("Alerta Moderado (40-75%)", f"{taxa_moderada:.1f}% das turmas", delta="Mediação preventiva")

        with c_clima3:
            df_rf_sim['Faixa'] = pd.cut(
                df_rf_sim['score_risco_pct'],
                bins=[-np.inf, 40, 75, np.inf],
                labels=['Baixo Risco', 'Moderado', 'Crítico']
            )
            fig_donut = px.pie(
                df_rf_sim,
                names='Faixa',
                title="Distribuição dos Níveis de Vulnerabilidade",
                color='Faixa',
                color_discrete_map={'Crítico': '#dc2626', 'Moderado': '#ea580c', 'Baixo Risco': '#059669'},
                hole=0.5
            )
            fig_donut.update_layout(height=180, margin=dict(l=10, r=10, t=30, b=10), paper_bgcolor='rgba(0,0,0,0)', showlegend=False)
            st.plotly_chart(fig_donut, use_container_width=True)

        st.markdown("---")
        st.markdown("#### 🚨 Painel de Alertas Pró-Ativos da Coordenação")
        
        col_alt1, col_alt2 = st.columns(2)
        with col_alt1:
            st.markdown("""
            <div style="background:#ffffff; border:1px solid #fee2e2; border-left:5px solid #dc2626; padding:14px 18px; border-radius:10px; margin-bottom:10px;">
                <strong style="color:#dc2626;"><i class="fas fa-triangle-exclamation"></i> Risco Crítico (Score > 75%)</strong>
                <p style="margin:4px 0 0 0; font-size:0.875rem; color:#475569;">
                    <strong>Diretriz Recomendada:</strong> Acionamento de intervenção psicossocial direta conjunta (Psicólogo + Assistente Social) e reforço de ronda escolar nos portões em horários de troca de turno.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
        with col_alt2:
            st.markdown("""
            <div style="background:#ffffff; border:1px solid #ffedd5; border-left:5px solid #ea580c; padding:14px 18px; border-radius:10px; margin-bottom:10px;">
                <strong style="color:#ea580c;"><i class="fas fa-circle-exclamation"></i> Risco Moderado (Score 40% a 75%)</strong>
                <p style="margin:4px 0 0 0; font-size:0.875rem; color:#475569;">
                    <strong>Diretriz Recomendada:</strong> Inclusão em círculos de justiça restaurativa, monitoria acadêmica para recuperação de notas e palestras sobre cyberbullying e segurança digital.
                </p>
            </div>
            """, unsafe_allow_html=True)

    # ── ABA 4: COPILOTO IA ──
    with tab_ia:
        st.header("Copiloto EduSeg — Consultor IA Baseado em Evidências")
        st.caption("Motor Llama 3.3 (Groq) + Pesquisa em Tempo Real (DuckDuckGo) · Custo Zero")

        try:
            api_key = st.secrets["GROQ_API_KEY"]
        except Exception:
            api_key = st.sidebar.text_input("🔑 Chave Groq (Opcional se nos Secrets)", type="password")

        if api_key:
            from agente_eduseg import AgenteEduSeg
            agente = AgenteEduSeg(api_key=api_key)
            contexto_banco = f"Escola em Foco: {escola_sel}, IVS: {esc['ivs']:.2f}, Risco Evasão: {esc['alunos_risco_evasao']}, Crimes 500m: {esc['crimes_500m']}"

            if "messages" not in st.session_state:
                st.session_state.messages = []
            for m in st.session_state.messages:
                with st.chat_message(m["role"]):
                    st.markdown(m["content"])
            if prompt := st.chat_input("Pergunte sobre dados de Salvador ou solicite recomendações de políticas"):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)
                with st.chat_message("assistant"):
                    ph = st.empty()
                    with st.spinner("Analisando bases..."):
                        try:
                            res = agente.chat(prompt, st.session_state.messages[:-1], contexto_banco)
                            ph.markdown(res["response"])
                            if res["buscou_web"]:
                                st.caption(f"🌐 {res['fase']}")
                            st.session_state.messages.append({"role": "assistant", "content": res["response"]})
                        except Exception as e:
                            st.error(f"Erro na execução da IA: {e}")
        else:
            st.info("👈 Defina sua chave Groq nos Secrets da aplicação ou no painel lateral.")

    # ── ABA 5: QUADRO TEÓRICO AMPLIADO ──
    with tab_teoria:
        st.markdown("""
        <div class="teoria-card">
            <h3>🛡️ 1. Sistemas de Apoio à Decisão em Segurança Pública e Corporativa</h3>
            <ul style="color: #475569; font-size: 0.9rem; line-height: 1.6;">
                <li><strong>Predição de Manchas Criminais (Policiamento Preditivo):</strong> Algoritmos que processam histórico georreferenciado de delitos (tipo, horário, local, condições do entorno) para antecipar onde viaturas devem ser posicionadas preventivamente.</li>
                <li><strong>Análise de Risco de Fraudes & Anomalias:</strong> Monitoramento contínuo cruzando perfis comportamentais para acionar alertas de investigação precoce.</li>
                <li><strong>Gestão de Crises e Grandes Eventos:</strong> Simulação preditiva para direcionamento de equipes de resgate, fechamento de vias e blindagem perimetral.</li>
            </ul>
        </div>
        
        <div class="teoria-card">
            <h3>📚 2. Sistemas de Apoio à Decisão na Gestão Educacional</h3>
            <ul style="color: #475569; font-size: 0.9rem; line-height: 1.6;">
                <li><strong>Prevenção de Evasão Escolar:</strong> Cruzamento de assiduidade, variação de rendimento bimestral, histórico disciplinar e vulnerabilidade local para emitir alertas preditivos antes do abandono escolar.</li>
                <li><strong>Plataformas de Aprendizagem Adaptativa:</strong> Ajuste em tempo real da trilha pedagógica com base no engajamento individual do estudante.</li>
                <li><strong>Planejamento e Alocação de Recursos Públicos:</strong> Otimização da construção de novas unidades escolares, expansão de tempo integral e rotas de transporte escolar.</li>
            </ul>
        </div>

        <div class="teoria-card">
            <h3>💡 3. Inteligência Artificial Explicável (XAI) & Algoritmos de Ensemble (Random Forest)</h3>
            <ul style="color: #475569; font-size: 0.9rem; line-height: 1.6;">
                <li><strong>O Princípio da Explicabilidade (XAI):</strong> No setor público e na educação, não basta o modelo classificar uma situação como de risco; ele precisa justificar as variáveis determinantes (ex: 85% de risco decorrente do aumento de faltas somado ao histórico de conflitos e vulnerabilidade territorial).</li>
                <li><strong>Random Forest (Floresta Aleatória):</strong> Algoritmo de aprendizado supervisionado baseado no consenso de múltiplas árvores de decisão. É amplamente reconhecido no meio acadêmico por mitigar o sobreajuste (overfitting) e oferecer mensuração precisa da importância relativa de cada feature.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

# ==============================================================================
# PERFIL: ANALISTA KDD
# ==============================================================================
elif perfil == 'Analista KDD':
    st.markdown("""
    <div>
        <h2 style="font-size: 2rem; font-weight: 800; color: #0f172a; margin-bottom: 2px;">Descoberta de Conhecimento em Bases de Dados (KDD)</h2>
        <p style="color: #64748b; font-weight: 500; margin-bottom: 1.5rem;">Pipeline Analítico: <span style="background:#faf5ff; color:#9333ea; padding: 3px 8px; border-radius: 6px; font-weight: 700;">Agrupamento</span> · <span style="background:#fff1f2; color:#e11d48; padding: 3px 8px; border-radius: 6px; font-weight: 700;">Regressão</span> · <span style="background:#f0fdfa; color:#0d9488; padding: 3px 8px; border-radius: 6px; font-weight: 700;">Associação</span> · <span style="background:#eff6ff; color:#2563eb; padding: 3px 8px; border-radius: 6px; font-weight: 700;">Correlação</span></p>
    </div>
    """, unsafe_allow_html=True)
    
    registrar_log(usuario_atual, perfil, "ACESSO_KDD", "vw_alerta_vulnerabilidade")

    tab1, tab2, tab3, tab4, tab5, tab6, tab_rf, tab_ia = st.tabs([
        "📍 Agrupamento (K-Means)", "📈 Regressão Linear", "🔗 Associação (Apriori)", "🔥 Correlação", "📊 Delitos por Bairro", "🧠 Grafo 3D", "🌲 Random Forest & XAI", "🤖 Copiloto IA"
    ])

    # ── AGRUPAMENTO ──
    with tab1:
        st.markdown("### Agrupamento Não-Supervisionado de Escolas (K-Means)")
        st.caption("O algoritmo particiona as unidades em 3 clusters por proximidade euclidiana no espaço Crimes x Evasão.")
        
        X = df_escolas[['crimes_500m', 'alunos_risco_evasao']].values
        kmeans = KMeans(n_clusters=3, random_state=42, n_init=10).fit(X)
        
        df_cluster = df_escolas.copy()
        df_cluster['Cluster'] = [f"Cluster {l+1}" for l in kmeans.labels_]
        
        fig_km = px.scatter(
            df_cluster,
            x='crimes_500m',
            y='alunos_risco_evasao',
            color='Cluster',
            text='nome_escola',
            size='total_alunos_ativos',
            color_discrete_sequence=['#10b981', '#f59e0b', '#ef4444'],
            labels={'crimes_500m': 'Crimes no Raio de 500m (SSP-BA)', 'alunos_risco_evasao': 'Alunos em Risco de Evasão (SEC)'},
            title="Distribuição em Clusters de Vulnerabilidade Escolar"
        )
        fig_km.update_traces(textposition='top center')
        fig_km.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(248,250,252,0.8)')
        st.plotly_chart(fig_km, use_container_width=True)

    # ── REGRESSÃO ──
    with tab2:
        st.markdown("### Modelo de Regressão Linear Preditiva")
        st.caption("Mapeamento da relação matemática funcional entre o entorno criminoso (Variável Independente X) e a evasão (Variável Dependente Y).")

        X_reg = df_escolas[['crimes_500m']].values
        y_reg = df_escolas['alunos_risco_evasao'].values
        model = LinearRegression().fit(X_reg, y_reg)
        r2 = model.score(X_reg, y_reg)
        
        x_range = np.linspace(X_reg.min(), X_reg.max(), 50)
        y_pred = model.predict(x_range.reshape(-1, 1))

        fig_reg = go.Figure()
        fig_reg.add_trace(go.Scatter(
            x=df_escolas['crimes_500m'],
            y=df_escolas['alunos_risco_evasao'],
            mode='markers+text',
            text=df_escolas['nome_escola'],
            textposition='bottom right',
            marker=dict(size=12, color='#2563eb'),
            name='Dados Observados'
        ))
        fig_reg.add_trace(go.Scatter(
            x=x_range,
            y=y_pred,
            mode='lines',
            line=dict(color='#dc2626', width=3, dash='dash'),
            name=f'Reta de Tendência (R² = {r2:.2f})'
        ))
        fig_reg.update_layout(
            xaxis_title="Crimes no Raio de 500m",
            yaxis_title="Volume de Alunos em Evasão",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(248,250,252,0.8)'
        )
        st.plotly_chart(fig_reg, use_container_width=True)
        st.info(f"💡 **Equação do Modelo:** `Evasão Estimada = {model.intercept_:.2f} + ({model.coef_[0]:.4f} * Crimes_500m)`. Coeficiente de Determinação **R² = {r2:.2f}**.")

    # ── ASSOCIAÇÃO (APRIORI) ──
    with tab3:
        st.markdown("### Descoberta de Regras de Associação (Algoritmo Apriori)")
        st.caption("Identificação de relações de causa e coocorrência (SE Antecedente ENTÃO Consequente).")

        df_bin = pd.DataFrame({
            'IVS_Alto': df_escolas['ivs'] > 0.6,
            'Crimes_Elevados': df_escolas['crimes_500m'] > df_escolas['crimes_500m'].median(),
            'Evasao_Alta': df_escolas['alunos_risco_evasao'] > df_escolas['alunos_risco_evasao'].median(),
            'Assiduidade_Critica': df_escolas['media_assiduidade'] < 75,
            'Deficit_Iluminacao': df_escolas['iluminacao'] == 0,
        })

        try:
            itemsets = apriori(df_bin, min_support=0.2, use_colnames=True)
            if len(itemsets) > 0:
                regras = association_rules(itemsets, metric="confidence", min_threshold=0.5, num_itemsets=len(itemsets))
                if not regras.empty:
                    for _, row in regras.head(6).iterrows():
                        ant = ", ".join([str(i) for i in row['antecedents']])
                        con = ", ".join([str(i) for i in row['consequents']])
                        st.markdown(f"""
                        <div style="background:#ffffff; border:1px solid #e2e8f0; border-left:5px solid #0d9488; padding:12px 18px; border-radius:10px; margin-bottom:10px; box-shadow:0 1px 3px rgba(0,0,0,0.02);">
                            <span style="background:#e2e8f0; color:#334155; font-size:0.75rem; padding:2px 6px; border-radius:4px; font-weight:700;">SE</span> 
                            <strong style="color:#0f172a;">{ant}</strong> 
                            <span style="background:#e2e8f0; color:#334155; font-size:0.75rem; padding:2px 6px; border-radius:4px; font-weight:700;">ENTÃO</span> 
                            <strong style="color:#0d9488;">{con}</strong>
                            <div style="margin-top:6px; font-size:0.8rem; color:#64748b;">
                                Suporte: <strong>{row['support']*100:.0f}%</strong> · Confiança: <strong>{row['confidence']*100:.0f}%</strong> · Lift: <strong>{row['lift']:.2f}</strong>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("Nenhuma regra atingiu o limiar de confiança mínima.")
            else:
                st.info("Nenhum itemset frequente encontrado.")
        except Exception as e:
            st.error(f"Erro no cálculo do Apriori: {e}")

    # ── CORRELAÇÃO ──
    with tab4:
        st.markdown("### Matriz de Correlação Multivariada (Plotly Heatmap)")
        st.caption("Interdependência estatística de Pearson entre os atributos do banco integrado.")
        
        colunas_corr = ['ivs', 'renda', 'crimes_500m', 'media_assiduidade', 'alunos_risco_evasao', 'total_ocorrencias_disc']
        nomes_legiveis = ['IVS', 'Renda Média', 'Crimes 500m', 'Assiduidade', 'Evasão', 'Ocorr. Disc.']
        matriz = df_escolas[colunas_corr].corr()
        
        fig_heat = px.imshow(
            matriz,
            text_auto='.2f',
            aspect="auto",
            color_continuous_scale='RdBu_r',
            x=nomes_legiveis,
            y=nomes_legiveis,
            title="Matriz de Correlação Linear"
        )
        fig_heat.update_layout(paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_heat, use_container_width=True)

    # ── DELITOS POR BAIRRO ──
    with tab5:
        st.markdown("### Distribuição Espacial de Ocorrências por Bairro e Tipo")
        df_merged = df_ocorrencias.merge(df_regioes, on='id_regiao')
        df_grp = df_merged.groupby(['nome_bairro', 'tipo_delito']).size().reset_index(name='total')
        
        fig_bar = px.bar(
            df_grp,
            x='nome_bairro',
            y='total',
            color='tipo_delito',
            title="Volume de Delitos Policiais Registrados",
            labels={'nome_bairro': 'Bairro / Região', 'total': 'Total de Ocorrências', 'tipo_delito': 'Natureza do Delito'},
            barmode='stack'
        )
        fig_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(248,250,252,0.8)')
        st.plotly_chart(fig_bar, use_container_width=True)

    # ── GRAFO 3D ──
    with tab6:
        def gerar_grafo_inline():
            nodes = []
            links = []
            nodes.append({"id": "sad", "label": "SAD-EduSeg", "type": "auditoria", "detail": "Plataforma de Decisão"})
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
                nodes.append({"id": oid, "label": f"BOs ({int(o['total'])})", "type": "ocorrencia", "detail": f"Registros: {int(o['total'])}"})
                links.append({"source": rid, "target": oid})
            return {"nodes": nodes, "links": links}
            
        st.subheader("Grafo de Conhecimento 3D — Topologia do Sistema")
        st.caption("Interações relacionais entre Regiões, Unidades Escolares e Incidências de Segurança.")
        graph_data = gerar_grafo_inline()
        html_path = os.path.join(BASE_DIR, "grafo_eduseg.html")
        try:
            with open(html_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            html_content = html_content.replace("GRAPH_DATA_PLACEHOLDER", json.dumps(graph_data, ensure_ascii=False))
            components.html(html_content, height=600, scrolling=False)
        except Exception:
            st.error("Componente do grafo 3D em renderização.")

    # ── RANDOM FOREST & XAI ──
    with tab_rf:
        st.markdown("### Classificação Preditiva de Vulnerabilidade & IA Explicável (XAI)")
        st.caption("Algoritmo de Ensemble (Random Forest Classifier) com análise da importância das variáveis na decisão.")

        rf_mod, df_rf_amostra, df_imp = treinar_modelo_rf_convivencia()

        col_rf1, col_rf2 = st.columns([6, 6])

        with col_rf1:
            st.markdown("#### 🔍 Explicabilidade da IA (Feature Importance - XAI)")
            fig_imp = px.bar(
                df_imp,
                x='Importancia',
                y='Feature',
                orientation='h',
                title="Peso Relativo de Cada Fator no Score de Risco",
                color='Importancia',
                color_continuous_scale='Tealgrn'
            )
            fig_imp.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(248,250,252,0.8)')
            st.plotly_chart(fig_imp, use_container_width=True)
            st.caption("A IA atribui maior relevância a faltas súbitas e histórico de conflitos na predição do risco de evasão e violência.")

        with col_rf2:
            st.markdown("#### 🧪 Simulador de Inferência de Perfil Anônimo")
            with st.container():
                s_faltas = st.slider("Faltas Consecutivas (Última quinzena)", 0, 15, 6)
                s_queda = st.slider("Queda de Rendimento / Notas (%)", 0, 80, 35)
                s_conflitos = st.slider("Ocorrências / Advertências Disciplinares", 0, 6, 2)
                s_rede = st.selectbox("Tentativa de Acesso a Conteúdo Suspeito na Rede Wi-Fi?", ["Não (0)", "Sim (1)"])
                s_rede_bin = 1 if "Sim" in s_rede else 0
                s_bairro = st.slider("Índice de Risco do Bairro / Entorno (1 a 10)", 1.0, 10.0, 7.5)

                input_perfil = pd.DataFrame([[s_faltas, s_queda, s_conflitos, s_rede_bin, s_bairro]],
                                            columns=['faltas_consecutivas', 'queda_notas_pct', 'historico_conflitos', 'acesso_rede_suspeito', 'risco_entorno_bairro'])
                
                prob_risco = rf_mod.predict_proba(input_perfil)[0, 1] * 100

                if prob_risco >= 75:
                    st.error(f"🚨 **Probabilidade Preditiva de Risco: {prob_risco:.1f}% (CRÍTICO)**")
                    st.markdown("**Decisão Automatizada (XAI):** Acionar intervenção direta do psicólogo escolar e assistente social imediatamente.")
                elif prob_risco >= 40:
                    st.warning(f"⚠️ **Probabilidade Preditiva de Risco: {prob_risco:.1f}% (MODERADO)**")
                    st.markdown("**Decisão Automatizada (XAI):** Encaminhar para monitoria de recuperação acadêmica e mediação de conflitos.")
                else:
                    st.success(f"✅ **Probabilidade Preditiva de Risco: {prob_risco:.1f}% (BAIXO)**")
                    st.markdown("**Decisão Automatizada (XAI):** Situação estável. Manter acompanhamento de rotina.")

    # ── COPILOTO IA (Analista) ──
    with tab_ia:
        st.header("Agente de Mineração de Dados KDD")
        st.caption("Interaja com a IA para interpretação de regras Apriori ou ajuste de hiperparâmetros.")

        try:
            api_key = st.secrets["GROQ_API_KEY"]
        except Exception:
            api_key = st.sidebar.text_input("🔑 Chave Groq - KDD", type="password", key="kdd_groq")

        if api_key:
            from agente_eduseg import AgenteEduSeg
            agente = AgenteEduSeg(api_key=api_key)
            contexto_kdd = f"Escolas em Risco: {escolas_criticas}, Correlação Evasão x Crimes: {r2:.2f}, Evasão Total: {total_risco_evasao}."
            
            if "messages_kdd" not in st.session_state:
                st.session_state.messages_kdd = []
            for m in st.session_state.messages_kdd:
                with st.chat_message(m["role"]):
                    st.markdown(m["content"])
            if prompt := st.chat_input("Ex: Qual o impacto do IVS alto na dispersão do Cluster 3?"):
                st.session_state.messages_kdd.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)
                with st.chat_message("assistant"):
                    ph = st.empty()
                    with st.spinner("Minerando padrões..."):
                        try:
                            res = agente.chat(prompt, st.session_state.messages_kdd[:-1], contexto_kdd)
                            ph.markdown(res["response"])
                            st.session_state.messages_kdd.append({"role": "assistant", "content": res["response"]})
                        except Exception as e:
                            st.error(f"Erro no Agente: {e}")
        else:
            st.info("👈 Defina sua chave Groq nos Secrets ou barra lateral.")

# ==============================================================================
# PERFIL: ADMIN DOMÍNIO
# ==============================================================================
elif perfil == 'Admin Domínio':
    st.markdown("""
    <div>
        <h2 style="font-size: 2rem; font-weight: 800; color: #0f172a; margin-bottom: 2px;">Governança de Dados e Trilha de Auditoria</h2>
        <p style="color: #64748b; font-weight: 500; margin-bottom: 1.5rem;">Controle RBAC e Rastreabilidade LGPD</p>
    </div>
    """, unsafe_allow_html=True)
    registrar_log(usuario_atual, perfil, "ACESSO_ADMIN", "sistema_logs_auditoria")

    tab_dados, tab_audit, tab_users = st.tabs(["📋 Bases Integradas", "🔒 Trilha de Auditoria", "👥 Usuários & RBAC"])

    with tab_dados:
        st.markdown("### Cadastro de Escolas (Base Educacional)")
        st.dataframe(df_escolas, hide_index=True, use_container_width=True)
        
        st.markdown("### Regiões Administrativas de Salvador")
        st.dataframe(df_regioes, hide_index=True, use_container_width=True)

    with tab_audit:
        st.markdown("### Trilha Imutável de Auditoria (LGPD Compliance)")
        conn = get_db_connection()
        df_logs = pd.read_sql_query("SELECT * FROM sistema_logs_auditoria ORDER BY data_hora_acesso DESC LIMIT 50", conn)
        conn.close()
        st.dataframe(df_logs, hide_index=True, use_container_width=True)

    with tab_users:
        st.markdown("### Gestão de Perfis de Acesso")
        conn = get_db_connection()
        df_users = pd.read_sql_query("SELECT id, nome, perfil FROM usuarios", conn)
        conn.close()
        st.dataframe(df_users, hide_index=True, use_container_width=True)

        with st.form("add_user"):
            st.write("Criar Novo Usuário")
            u_nome = st.text_input("Nome")
            u_senha = st.text_input("Senha", type="password")
            u_perfil = st.selectbox("Perfil", ["Gestor Público", "Analista KDD", "Admin Domínio"])
            if st.form_submit_button("Cadastrar Usuário"):
                conn = get_db_connection()
                conn.execute("INSERT INTO usuarios (nome, senha, perfil) VALUES (?, ?, ?)", (u_nome, u_senha, u_perfil))
                conn.commit()
                conn.close()
                st.success("Usuário criado com sucesso!")
                registrar_log(usuario_atual, perfil, "CRIAR_USUARIO", "usuarios")
                st.rerun()
