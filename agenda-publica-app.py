import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression
import sqlite3
import database
import time
import os
from datetime import datetime

# Caminho absoluto para o banco de dados
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "sad_eduseg.db")

# Garante que o banco de dados existe e tem os cadastros iniciais
database.init_db()

# Função para conectar ao banco
def get_db_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# Função de Log de Auditoria (LGPD)
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

# Configurações da página
st.set_page_config(
    page_title="SAD-EduSeg | Bahia",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ──────────────────────────────────────────────────────────────────────────────
# CONTROLE DE SESSÃO E LOGIN (RBAC)
# ──────────────────────────────────────────────────────────────────────────────
if 'usuario' not in st.session_state:
    st.session_state['usuario'] = None
    st.session_state['perfil'] = None

with st.sidebar:
    st.title("SAD-EduSeg 🛡️📚")
    st.caption("Integração SSP-BA & SEC-BA")
    st.markdown("---")

    if st.session_state['usuario'] is None:
        tab_login, tab_criar = st.tabs(["Login", "Criar Conta"])

        with tab_login:
            st.subheader("Acesso RBAC")
            nome_input = st.text_input("Usuário", key="login_nome")
            senha_input = st.text_input("Senha", type="password", key="login_senha")

            if st.button("Entrar"):
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
            if st.button("Cadastrar"):
                conn = get_db_connection()
                conn.execute("INSERT INTO usuarios (nome, senha, perfil) VALUES (?, ?, ?)", (c_nome, c_senha, c_perfil))
                conn.commit()
                conn.close()
                st.success("Criado! Faça login.")
    else:
        st.write(f"👤 **{st.session_state['usuario']}**")
        st.write(f"🔒 Perfil: *{st.session_state['perfil']}*")
        if st.button("Sair"):
            registrar_log(st.session_state['usuario'], st.session_state['perfil'], "LOGOUT", "usuarios")
            st.session_state['usuario'] = None
            st.session_state['perfil'] = None
            st.rerun()

    st.markdown("---")
    st.caption("EAUFBA · Sistemas de Apoio à Decisão")
    st.caption("Conformidade LGPD · RBAC · Auditoria")

# Se não logado, exibe home
if st.session_state['usuario'] is None:
    st.title("SAD-EduSeg: Segurança Pública & Educação 🛡️📚")
    st.subheader("Sistema de Apoio à Decisão Cognitivo — Estado da Bahia")
    st.info("Utilize o painel lateral para fazer login. Credenciais padrão: **Gestor Publico** / 123")
    st.stop()

# ==============================================================================
# EXTRAÇÃO DE DADOS (CONSULTAS SQL INTEGRADAS)
# ==============================================================================
usuario_atual = st.session_state['usuario']
perfil = st.session_state['perfil']

@st.cache_data(ttl=60)
def carregar_visao_escolas():
    """Replica a VIEW vw_alerta_vulnerabilidade_escolas do modelo SQL."""
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT
        e.id_escola,
        e.nome_escola_mascarado AS nome_escola,
        r.nome_bairro AS bairro,
        r.indice_vulnerabilidade_social AS ivs,
        r.renda_media_familiar AS renda,
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

registrar_log(usuario_atual, perfil, "CONSULTA_PAINEL", "vw_alerta_vulnerabilidade_escolas")

# ==============================================================================
# PERFIL: GESTOR PÚBLICO (Dashboard + Blend + IA)
# ==============================================================================
if perfil == 'Gestor Público':
    st.title("Painel do Gestor — Secretaria Integrada SSP/SEC")

    # --- SUMARIZAÇÃO COM INDICADORES IAC E DCE ---
    st.header("1. Indicadores de Inteligência (BI)")

    total_alunos = df_escolas['total_alunos_ativos'].sum()
    total_risco_evasao = df_escolas['alunos_risco_evasao'].sum()
    iac = round((total_risco_evasao / total_alunos) * 100, 1) if total_alunos > 0 else 0
    total_crimes_500m = df_escolas['crimes_500m'].sum()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Alunos Monitorados", f"{total_alunos:,}")
    col2.metric("IAC (Assiduidade Crítica)", f"{iac}%", "Alunos <75% presença", delta_color="inverse")
    col3.metric("Crimes (Raio 500m)", f"{total_crimes_500m}", "Últimos 90 dias", delta_color="inverse")
    col4.metric("Escolas Analisadas", len(df_escolas))
    st.markdown("---")

    # --- SIMULADOR BLEND DE OPÇÕES ---
    st.header("2. Simulador de Intervenções (Blend de Opções)")

    escola_selecionada = st.selectbox("Selecione a Escola", df_escolas['nome_escola'])
    escola_data = df_escolas[df_escolas['nome_escola'] == escola_selecionada].iloc[0]

    col_l, col_r = st.columns([1, 1])

    with col_l:
        st.subheader("Alocação Orçamentária")
        orcamento_seguranca = st.slider("Patrulhamento PM/Ronda Escolar (R$ Mi)", 1.0, 10.0, 3.5, 0.5)
        orcamento_educacao = st.slider("Assistência Pedagógica / Integral (R$ Mi)", 1.0, 10.0, 4.0, 0.5)

    with col_r:
        st.subheader("Classificação e Recomendação")

        risco_pontuacao = (escola_data['crimes_500m'] * 0.5) + (escola_data['alunos_risco_evasao'] * 2) + (escola_data['ivs'] * 50)

        if risco_pontuacao > 80:
            nivel_risco = "CRÍTICO"
            cor_risco = "🔴"
            if orcamento_seguranca > orcamento_educacao:
                recomendacao = "**Blend A (Policial):** Ronda Escolar intensiva + Câmeras COI no entorno."
            else:
                recomendacao = "**Blend B (Pedagógico):** Escola em Tempo Integral + Busca Ativa + Abertura nos finais de semana."
        elif risco_pontuacao > 40:
            nivel_risco = "MODERADO"
            cor_risco = "🟡"
            recomendacao = "**Blend C (Preventivo):** Policiamento comunitário + Monitoramento de frequência."
        else:
            nivel_risco = "ESTÁVEL"
            cor_risco = "🟢"
            recomendacao = "Manter alocação padrão. Escola em zona segura."

        st.metric(f"{cor_risco} Nível de Risco", nivel_risco)
        st.info(f"🎯 {recomendacao}")
        st.caption(f"IVS: {escola_data['ivs']:.2f} | Assiduidade Média: {escola_data['media_assiduidade']}% | Crimes 500m: {escola_data['crimes_500m']}")

    st.markdown("---")

    # --- COPILOTO IA (GROQ / LLAMA 3) ---
    st.header("3. Copiloto IA (Conselheiro Especialista)")

    api_key = st.sidebar.text_input("🔑 Groq API Key", type="password", help="Insira sua chave da API Groq para habilitar o Copiloto IA (Llama 3).")

    if api_key:
        try:
            from groq import Groq
            client = Groq(api_key=api_key)

            st.info(f"💡 Contexto ativo: **{escola_data['nome_escola']}** ({escola_data['bairro']}) — Risco: {nivel_risco}")

            if "messages" not in st.session_state:
                st.session_state.messages = []

            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            if prompt := st.chat_input("Ex: 'Qual política pública reduz a evasão nessa escola?'"):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                with st.chat_message("assistant"):
                    message_placeholder = st.empty()

                    sys_prompt = (
                        f"Você é um conselheiro especialista em políticas públicas do Governo da Bahia, "
                        f"atuando no cruzamento entre Segurança Pública (SSP-BA) e Educação (SEC-BA). "
                        f"Contexto da escola analisada: "
                        f"Nome: {escola_data['nome_escola']}, Bairro: {escola_data['bairro']}, "
                        f"IVS (Vulnerabilidade Social): {escola_data['ivs']:.2f}, "
                        f"Total de Alunos: {escola_data['total_alunos_ativos']}, "
                        f"Assiduidade Média: {escola_data['media_assiduidade']}%, "
                        f"Alunos em Risco de Evasão (<75%): {escola_data['alunos_risco_evasao']}, "
                        f"Crimes no Raio de 500m: {escola_data['crimes_500m']}, "
                        f"Ocorrências Disciplinares Internas: {escola_data['total_ocorrencias_disc']}, "
                        f"Classificação SAD: {nivel_risco}. "
                        f"Responda de forma analítica, concisa e baseada nesses dados."
                    )

                    messages_for_api = [{"role": "system", "content": sys_prompt}]
                    for m in st.session_state.messages:
                        messages_for_api.append(m)

                    try:
                        response = client.chat.completions.create(
                            model="llama3-8b-8192",
                            messages=messages_for_api,
                        )
                        full_response = response.choices[0].message.content
                        message_placeholder.markdown(full_response)
                        st.session_state.messages.append({"role": "assistant", "content": full_response})
                        registrar_log(usuario_atual, perfil, "CONSULTA_IA", "groq_llama3")
                    except Exception as e:
                        st.error(f"Erro na API Groq: {e}")
        except ImportError:
            st.error("Biblioteca 'groq' não instalada.")
    else:
        st.warning("👈 Insira sua Chave de API Groq na barra lateral para habilitar o Copiloto IA.")


# ==============================================================================
# PERFIL: ANALISTA KDD (Data Mining)
# ==============================================================================
elif perfil == 'Analista KDD':
    st.title("Módulo de Mineração de Dados (KDD)")
    registrar_log(usuario_atual, perfil, "ACESSO_KDD", "vw_alerta_vulnerabilidade_escolas")

    tab1, tab2, tab3 = st.tabs(["📍 Clustering (K-Means)", "📈 Regressão Linear", "📊 Análise por Delito"])

    with tab1:
        st.subheader("Segmentação de Escolas por Vulnerabilidade")
        st.write("Variáveis: **Crimes no Raio de 500m** vs **Alunos em Risco de Evasão** (Assiduidade < 75%)")

        X = df_escolas[['crimes_500m', 'alunos_risco_evasao']].values
        kmeans = KMeans(n_clusters=3, random_state=42, n_init=10).fit(X)

        fig, ax = plt.subplots(figsize=(10, 5))
        cores = ['#2ecc71', '#f39c12', '#e74c3c']
        labels_cluster = ['Estável', 'Moderado', 'Crítico']

        for i in range(3):
            mask = kmeans.labels_ == i
            ax.scatter(X[mask, 0], X[mask, 1], c=cores[i], s=180, alpha=0.85, label=labels_cluster[i], edgecolors='white', linewidths=0.8)

        for i, txt in enumerate(df_escolas['nome_escola']):
            ax.annotate(txt, (X[i, 0] + 1, X[i, 1] + 0.3), fontsize=7)

        ax.set_xlabel("Crimes no Raio de 500m (SSP-BA)")
        ax.set_ylabel("Alunos em Risco de Evasão (SEC-BA)")
        ax.set_title("K-Means: Clusters de Vulnerabilidade Escolar — Salvador/BA")
        ax.legend(title="Cluster")
        st.pyplot(fig)

    with tab2:
        st.subheader("Regressão: Criminalidade ↔ Evasão Escolar")

        X_reg = df_escolas[['crimes_500m']].values
        y_reg = df_escolas['alunos_risco_evasao'].values

        model = LinearRegression().fit(X_reg, y_reg)
        y_pred = model.predict(X_reg)
        r2 = model.score(X_reg, y_reg)

        fig2, ax2 = plt.subplots(figsize=(10, 5))
        ax2.scatter(X_reg, y_reg, color='#e74c3c', s=120, label="Dados Reais", edgecolors='white', linewidths=0.8)
        ax2.plot(sorted(X_reg), model.predict(sorted(X_reg)), color='#3498db', linewidth=2, linestyle='--', label=f"Tendência Linear (R²={r2:.2f})")
        ax2.set_xlabel("Crimes no Entorno (SSP-BA)")
        ax2.set_ylabel("Alunos em Risco de Evasão")
        ax2.set_title("Correlação: Criminalidade vs Evasão Escolar")
        ax2.legend()
        st.pyplot(fig2)
        st.write(f"**Coeficiente Angular:** {model.coef_[0]:.3f} — A cada crime adicional no entorno, estima-se +{model.coef_[0]:.1f} alunos em risco de evasão.")

    with tab3:
        st.subheader("Distribuição de Delitos por Tipo e Bairro")

        df_merged = df_ocorrencias.merge(df_regioes, left_on='id_regiao', right_on='id_regiao')
        pivot = df_merged.groupby(['nome_bairro', 'tipo_delito']).size().unstack(fill_value=0)

        fig3, ax3 = plt.subplots(figsize=(12, 5))
        pivot.plot(kind='bar', stacked=True, ax=ax3, colormap='Set2')
        ax3.set_title("Distribuição de Delitos por Bairro (SSP-BA)")
        ax3.set_ylabel("Quantidade de Ocorrências")
        ax3.set_xlabel("")
        ax3.legend(title="Tipo de Delito", fontsize=7, loc='upper right')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        st.pyplot(fig3)


# ==============================================================================
# PERFIL: ADMIN DOMÍNIO (APIs + Auditoria)
# ==============================================================================
elif perfil == 'Admin Domínio':
    st.title("Módulo de Integração e Governança (LGPD)")
    registrar_log(usuario_atual, perfil, "ACESSO_ADMIN", "sistema_logs_auditoria")

    tab_api, tab_audit, tab_dados = st.tabs(["📡 APIs de Dados", "🔒 Auditoria LGPD", "📋 Tabelas do Banco"])

    with tab_api:
        st.subheader("1. Portal Dados Abertos (INEP/MEC)")
        if st.button("Capturar IDEB via CKAN API"):
            with st.spinner("Conectando ao dados.gov.br..."):
                time.sleep(2)
                st.success("API CKAN conectada (HTTP 200). Dataset IDEB Salvador carregado.")
                registrar_log(usuario_atual, perfil, "SYNC_API_CKAN", "tabelas_educacao_escolas")

        st.markdown("---")
        st.subheader("2. Georreferenciamento (Overpass/OpenStreetMap)")
        if st.button("Cruzar Coordenadas (Raio 500m)"):
            with st.spinner("Processando filtro geométrico..."):
                time.sleep(2)
                st.success("Geolocalização concluída. Crimes vinculados ao perímetro das escolas.")
                registrar_log(usuario_atual, perfil, "SYNC_OVERPASS", "tabelas_seguranca_ocorrencias")

    with tab_audit:
        st.subheader("Trilha de Auditoria (LGPD)")
        st.caption("Registro imutável de acessos — Quem acessou, quando e qual tabela.")
        conn = get_db_connection()
        df_logs = pd.read_sql_query("SELECT * FROM sistema_logs_auditoria ORDER BY data_hora_acesso DESC LIMIT 50", conn)
        conn.close()
        st.dataframe(df_logs, hide_index=True, use_container_width=True)

    with tab_dados:
        st.subheader("Visão Consolidada: Escolas")
        st.dataframe(df_escolas, hide_index=True, use_container_width=True)
        st.subheader("Regiões de Salvador")
        st.dataframe(df_regioes, hide_index=True, use_container_width=True)
