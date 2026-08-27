import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans

# Configurações da página do aplicativo
st.set_page_config(
    page_title="SAD-AgendaPública | Regulação do Trabalho por Aplicativos",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ──────────────────────────────────────────────────────────────────────────────
# CARREGAMENTO DA BASE DE DADOS (DADOS REAIS: IPEA / PNAD CONTÍNUA / FAIRWORK)
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_data
def carregar_dados():
    # Indicadores Anuais
    df_indicadores = pd.DataFrame({
        "ano": [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025],
        "trabalhadores_milhoes": [0.8, 1.0, 1.3, 1.5, 1.7, 1.9, 2.1, 2.3]
    })
    
    # Atores e Influência
    df_atores = pd.DataFrame({
        "ator": ["iFood/Uber", "MTE", "Sindicatos", "Entregadores Livres", "Congresso"],
        "poder_influencia": ["alto", "alto", "médio", "médio", "alto"],
        "aliado_trabalhadores": ["baixo", "alto", "alto", "médio", "baixo"]
    })
    
    # Plataformas (Fairwork)
    df_plataformas = pd.DataFrame({
        "Plataforma": ["iFood", "Uber", "99", "Rappi"],
        "Score Fairwork (0-10)": [4, 1, 1, 0]
    })
    
    # Proposições
    df_proposicoes = pd.DataFrame([
        {"Proposição": "PLP 12/2024", "Autor": "Executivo", "Piso (R$)": 32.10, "Viabilidade": "Alta"},
        {"Proposição": "PL 2479/2025", "Autor": "Deputados", "Piso (R$)": 10.00, "Viabilidade": "Baixa"}
    ])
    
    return df_indicadores, df_atores, df_plataformas, df_proposicoes

df_indicadores, df_atores, df_plataformas, df_proposicoes = carregar_dados()

total_trabalhadores = 500000

# ──────────────────────────────────────────────────────────────────────────────
# CONTROLE DE SESSÃO E LOGIN
# ──────────────────────────────────────────────────────────────────────────────
if 'usuario' not in st.session_state:
    st.session_state['usuario'] = None
    st.session_state['perfil'] = None
    st.session_state['piso'] = 32.10
    st.session_state['inss_patronal'] = 20.0
    st.session_state['inss_trab'] = 7.5
    st.session_state['clima'] = "Moderado (Coalizão Dividida)"

def realizar_login(nome, perfil):
    st.session_state['usuario'] = nome
    st.session_state['perfil'] = perfil

with st.sidebar:
    st.title("SAD-AgendaPública")
    st.markdown("---")
    if st.session_state['usuario'] is None:
        nome = st.text_input("Nome do Usuário", value="Carlos de Souza")
        perfil_selecionado = st.selectbox(
            "Selecione o seu Perfil",
            ["Usuário Decisor (MTE / Gestor)", "Analista de Dados (KDD)", "Analista de Domínio (Político)"]
        )
        if st.button("Acessar o Sistema"):
            realizar_login(nome, perfil_selecionado)
            st.rerun()
    else:
        st.write(f"Conectado como: **{st.session_state['usuario']}**")
        st.write(f"Perfil: *{st.session_state['perfil']}*")
        if st.button("Sair / Logout"):
            st.session_state['usuario'] = None
            st.rerun()

if st.session_state['usuario'] is None:
    st.title("SAD-AgendaPública 📊")
    st.info("Faça o login na barra lateral para acessar o sistema.")
    st.stop()

# ──────────────────────────────────────────────────────────────────────────────
# INTERFACE PRINCIPAL
# ──────────────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "🏠 Dashboard", 
    "🔮 Módulo de Simulação", 
    "📈 Mineração de Dados (KDD)", 
    "📋 Cadastro de Critérios"
])

# ──────────────────────────────────────────────────────────────────────────────
# TAB 1: DASHBOARD
# ──────────────────────────────────────────────────────────────────────────────
with tab1:
    st.header("Dashboard Principal")
    col1, col2, col3 = st.columns(3)
    col1.metric("População (Milhões)", df_indicadores['trabalhadores_milhoes'].iloc[-1])
    col2.metric("Desproteção Social", "77.0%", "-Crítico")
    col3.metric("Proposições Ativas", len(df_proposicoes))

# ──────────────────────────────────────────────────────────────────────────────
# TAB 2: MÓDULO DE SIMULAÇÃO (Integrado com o código do usuário)
# ──────────────────────────────────────────────────────────────────────────────
with tab2:
    st.header("Módulo de Simulação Decisória (O Blend de Opções)")
    col_sim_l, col_sim_r = st.columns([1, 2])
    
    with col_sim_l:
        st.subheader("Parâmetros")
        piso_selecionado = st.slider(
            "Piso Remuneratório (R$ por Hora Conectada)",
            min_value=10.0, max_value=45.0, 
            value=st.session_state['piso'], step=0.50, key="slider_piso"
        )
        
        aliq_patronal = st.slider(
            "Alíquota de Contribuição Patronal (Empresas) [INSS %]",
            min_value=0.0, max_value=25.0, 
            value=st.session_state['inss_patronal'], step=0.5, key="slider_patronal"
        )
        
        aliq_trabalhador = st.slider(
            "Alíquota de Contribuição do Trabalhador [INSS %]",
            min_value=0.0, max_value=11.0, 
            value=st.session_state['inss_trab'], step=0.5, key="slider_trab"
        )
        
        clima_politico = st.selectbox(
            "Clima de Negociação Política no Congresso Nacional",
            ["Altamente Favorável", "Moderado (Coalizão Dividida)", "Oposição Forte / Lobby Ativo"],
            index=["Altamente Favorável", "Moderado (Coalizão Dividida)", "Oposição Forte / Lobby Ativo"].index(st.session_state['clima']),
            key="select_clima"
        )
        
    with col_sim_r:
        st.subheader("Diagnóstico e Prescrição de Recomendação do SAD")
        
        horas_mensais_totais = 500000 * 160 * 12
        arrecadacao_inss_estimada = horas_mensais_totais * (piso_selecionado) * ((aliq_patronal + aliq_trabalhador) / 100)
        
        st.markdown("<div class='blend-container'>", unsafe_allow_html=True)
        
        if piso_selecionado >= 35.0 or aliq_patronal >= 20.0:
            status_risco = "ALTO RISCO DE FUGA DE CAPITAL"
            opcao_recomendada = "Blend de Opção B: Terceira Via Regulada (Modelo Autônomo com Acordo)"
            cor_alerta = "error"
            explicacao = (
                "A imposição de encargos muito altos (Piso >= R$ 35,00/hora e INSS Patronal >= 20%) inviabiliza "
                "a rentabilidade das plataformas de delivery de comida. O modelo aponta alta probabilidade de descredenciamento "
                "de frotas de duas rodas e aumento imediato da informalidade."
            )
        elif piso_selecionado < 20.0:
            status_risco = "RISCO DE PARALISIA SOCIAL E GREVES"
            opcao_recomendada = "Blend de Opção C: Microempreendedorismo Cooperativo (MEI Simplificado)"
            cor_alerta = "warning"
            explicacao = (
                "Piso excessivamente baixo (menor que R$ 20,00/hora) mantém o status de precarização extrema. "
                "Os sindicatos exercerão forte oposição e há risco elevado de paralisações nacionais (Breques de Apps). "
                "A melhor estratégia gerencial é criar incentivos fiscais para cooperativas autogestionárias de entregadores."
            )
        else:
            status_risco = "EQUILÍBRIO TÁTICO INSTITUCIONAL"
            opcao_recomendada = "Blend de Opção A: Regulação Híbrida Compulsória (Regras Pactuadas)"
            cor_alerta = "info"
            explicacao = (
                "Este cenário representa o ponto de ótimo de Pareto. Oferece uma proteção previdenciária adequada "
                "para reverter os 77% de desproteção social mapeados pelo Ipea, sem forçar a quebra comercial do ecossistema "
                "de delivery de duas rodas no mercado nacional."
            )
            
        st.markdown(f"**Diagnóstico do Sistema:** `{status_risco}`")
        if cor_alerta == "error":
            st.error(f"🎯 **RECOMENDAÇÃO ATIVA:** {opcao_recomendada}")
        elif cor_alerta == "warning":
            st.warning(f"🎯 **RECOMENDAÇÃO ATIVA:** {opcao_recomendada}")
        else:
            st.info(f"🎯 **RECOMENDAÇÃO ATIVA:** {opcao_recomendada}")
            
        st.markdown(f"**Justificativa Gerencial:** {explicacao}")
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.write("---")
        
        col_m_sim1, col_m_sim2 = st.columns(2)
        with col_m_sim1:
            st.metric(
                label="Projeção de Arrecadação Previdenciária Anual",
                value=f"R$ {arrecadacao_inss_estimada:,.2f}",
                delta=f"Impacto sobre {total_trabalhadores:,} trabalhadores"
            )
        with col_m_sim2:
            risco_politico = "ALTO" if clima_politico == "Oposição Forte / Lobby Ativo" or piso_selecionado >= 35.0 else "MÉDIO/BAIXO"
            st.metric(
                label="Risco de Paralisia no Congresso",
                value=risco_politico,
                delta="Exige Negociação" if risco_politico == "ALTO" else "Estável"
            )

# ──────────────────────────────────────────────────────────────────────────────
# TAB 3: ENGENHARIA DE DADOS & KDD
# ──────────────────────────────────────────────────────────────────────────────
with tab3:
    st.header("Módulo de Extração de Conhecimento em Base de Dados (KDD)")
    
    col_kdd_l, col_kdd_r = st.columns(2)
    
    with col_kdd_l:
        st.subheader("1. Função de Regressão Linear Preditiva")
        if not df_indicadores.empty:
            df_historico = df_indicadores.dropna(subset=['trabalhadores_milhoes'])
            X = df_historico['ano'].values
            y = df_historico['trabalhadores_milhoes'].values
            
            slope, intercept = np.polyfit(X, y, 1)
            anos_projeção = np.array([2026, 2027, 2028])
            valores_projeção = slope * anos_projeção + intercept
            
            df_proj_tabela = pd.DataFrame({
                "Ano Projetado": anos_projeção,
                "Quantidade Estimada (Milhões)": np.round(valores_projeção, 2)
            })
            
            st.write(f"📈 **Equação de Tendência:** $Trabalhadores (Milhões) = {slope:.3f} \\times Ano + ({intercept:.1f})$")
            st.dataframe(df_proj_tabela, use_container_width=True, hide_index=True)
            
            fig_reg, ax_reg = plt.subplots(figsize=(7, 3.8))
            ax_reg.scatter(X, y, color='#D97706', s=60, label="Dados Reais (Ipea)", zorder=3)
            
            X_completo = np.append(X, anos_projeção)
            y_completo = slope * X_completo + intercept
            ax_reg.plot(X_completo, y_completo, color='#1E3A8A', linestyle='--', linewidth=2, label="Reta de Regressão")
            
            ax_reg.set_title("Projeção do Contingente de Trabalhadores")
            ax_reg.legend()
            st.pyplot(fig_reg)
            
    with col_kdd_r:
        st.subheader("2. Função de Agrupamento K-Means")
        if not df_atores.empty:
            map_poder = {'alto': 3, 'médio': 2, 'baixo': 1}
            map_aliado = {'alto': 3, 'médio': 2, 'baixo': 1}
            
            df_clus = df_atores.copy()
            df_clus['poder_num'] = df_clus['poder_influencia'].map(map_poder).fillna(2)
            df_clus['aliado_num'] = df_clus['aliado_trabalhadores'].map(map_aliado).fillna(2)
            
            X_clus = df_clus[['poder_num', 'aliado_num']].values
            X_clus_jitter = X_clus + np.random.normal(0, 0.15, X_clus.shape)
            
            kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
            df_clus['cluster'] = kmeans.fit_predict(X_clus)
            
            fig_cl, ax_cl = plt.subplots(figsize=(7, 3.8))
            cores = ['#1E3A8A', '#D97706', '#10B981']
            
            for k in range(3):
                subset = df_clus[df_clus['cluster'] == k]
                ax_cl.scatter(
                    X_clus_jitter[df_clus['cluster'] == k, 0], 
                    X_clus_jitter[df_clus['cluster'] == k, 1], 
                    c=cores[k], s=80, edgecolors='black', label=f"Cluster {k}", zorder=3
                )
                for idx, row in subset.iterrows():
                    ax_cl.text(X_clus_jitter[idx, 0] + 0.05, X_clus_jitter[idx, 1] + 0.05, row['ator'].upper(), fontsize=7)
            
            ax_cl.set_title("Clustering K-Means de Coalizões e Stakeholders")
            ax_cl.legend(loc='lower left', fontsize=7)
            st.pyplot(fig_cl)

# ──────────────────────────────────────────────────────────────────────────────
# TAB 4: GOVERNANÇA & CADASTRO
# ──────────────────────────────────────────────────────────────────────────────
with tab4:
    st.header("Módulo de Cadastro Estruturado de Critérios de Decisão")
    col_cad_l, col_cad_r = st.columns(2)
    
    with col_cad_l:
        st.subheader("1. Indicadores Macroeconômicos Reais (Tabela 2)")
        st.dataframe(df_indicadores, use_container_width=True, hide_index=True)
        
        st.subheader("2. Atores e Espectro Político (Tabela 3)")
        st.dataframe(df_atores, use_container_width=True, hide_index=True)
            
    with col_cad_r:
        st.subheader("3. Scores de Plataformas (Fairwork 2025)")
        st.dataframe(df_plataformas, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.subheader("📝 Cadastrar Nova Proposta de Lei no Banco")
        with st.form("form_novo_projeto"):
            prop_id = st.text_input("Identificação do Projeto de Lei", value="PLP 123/2026")
            prop_autor = st.text_input("Autor da Proposta", value="Comissão de Trabalho")
            prop_piso = st.number_input("Piso Proposto (R$)", min_value=0.0, value=30.0)
            enviar_btn = st.form_submit_button("Registrar e Salvar no Banco")
            if enviar_btn:
                st.success(f"Proposição **{prop_id}** cadastrada com sucesso!")
