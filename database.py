import sqlite3
import hashlib
import os
from datetime import datetime, timedelta
import random

# Caminho absoluto para evitar problemas no Streamlit Cloud
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "sad_eduseg.db")


def gerar_hash_aluno(nome_ficticio):
    """Gera um SHA-256 a partir de um nome fictício (simulando anonimização LGPD)."""
    return hashlib.sha256(nome_ficticio.encode('utf-8')).hexdigest()


def init_db():
    print("[DB] Inicializando o Banco de Dados Integrado SAD-EduSeg...")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # =====================================================================
    # MÓDULO A: CONTEXTO SOCIOECONÔMICO (Regiões)
    # =====================================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tabelas_contexto_regioes (
            id_regiao INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_bairro TEXT NOT NULL,
            zona_administrativa TEXT,
            renda_media_familiar REAL,
            indice_vulnerabilidade_social REAL,
            presenca_iluminacao_publica INTEGER DEFAULT 1,
            data_ultima_atualizacao TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # =====================================================================
    # MÓDULO B: EDUCAÇÃO - Escolas (Infraestrutura)
    # =====================================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tabelas_educacao_escolas (
            id_escola INTEGER PRIMARY KEY AUTOINCREMENT,
            id_regiao INTEGER REFERENCES tabelas_contexto_regioes(id_regiao),
            nome_escola_mascarado TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            total_alunos_ativos INTEGER,
            turno_funcionamento TEXT
        )
    ''')

    # =====================================================================
    # MÓDULO B: EDUCAÇÃO - Alunos Anonimizados (SHA-256)
    # =====================================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tabelas_educacao_alunos_anonimizados (
            id_aluno_hash TEXT PRIMARY KEY,
            id_escola INTEGER REFERENCES tabelas_educacao_escolas(id_escola),
            idade_atual INTEGER,
            taxa_assiduidade_trimestre REAL,
            flag_evasao_risco INTEGER DEFAULT 0,
            qtd_ocorrencias_disciplinares INTEGER DEFAULT 0
        )
    ''')

    # =====================================================================
    # MÓDULO C: SEGURANÇA PÚBLICA - Ocorrências (SSP-BA)
    # =====================================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tabelas_seguranca_ocorrencias (
            id_ocorrencia INTEGER PRIMARY KEY AUTOINCREMENT,
            id_regiao INTEGER REFERENCES tabelas_contexto_regioes(id_regiao),
            codigo_bo_mascarado TEXT UNIQUE NOT NULL,
            tipo_delito TEXT NOT NULL,
            data_hora_fato TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            flag_envolvimento_menor_vitima INTEGER DEFAULT 0,
            flag_envolvimento_menor_autor INTEGER DEFAULT 0,
            distancia_escola_proxima_metros INTEGER
        )
    ''')

    # =====================================================================
    # MÓDULO D: GOVERNANÇA - Logs de Auditoria (LGPD)
    # =====================================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sistema_logs_auditoria (
            id_log INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id TEXT NOT NULL,
            orgao_usuario TEXT NOT NULL,
            acao_executada TEXT NOT NULL,
            tabela_acessada TEXT,
            data_hora_acesso TEXT DEFAULT CURRENT_TIMESTAMP,
            ip_origem TEXT
        )
    ''')

    # =====================================================================
    # TABELA DE USUÁRIOS (Controle de Acesso RBAC)
    # =====================================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            senha TEXT NOT NULL,
            perfil TEXT NOT NULL
        )
    ''')

    # ==================================================================
    # POPULAÇÃO INICIAL (SEED) - Dados Simulados de Salvador/BA
    # ==================================================================

    # --- Usuários Padrão ---
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO usuarios (nome, senha, perfil) VALUES ('Gestor Publico', '123', 'Gestor Público')")
        cursor.execute("INSERT INTO usuarios (nome, senha, perfil) VALUES ('Analista KDD', '123', 'Analista KDD')")
        cursor.execute("INSERT INTO usuarios (nome, senha, perfil) VALUES ('Admin Dominio', 'admin', 'Admin Domínio')")
        print("[DB] Usuários padrão RBAC criados.")

    # --- Regiões de Salvador ---
    cursor.execute("SELECT COUNT(*) FROM tabelas_contexto_regioes")
    if cursor.fetchone()[0] == 0:
        regioes = [
            ("Periperi", "Subúrbio Ferroviário", 1200.00, 0.82, 0),
            ("Cajazeiras", "Miolo", 1450.00, 0.75, 1),
            ("Itapuã", "Orla Atlântica", 2100.00, 0.55, 1),
            ("Costa Azul", "Orla Atlântica", 3800.00, 0.30, 1),
            ("Nazaré", "Centro Histórico", 2500.00, 0.40, 1),
            ("Garcia", "Centro", 2800.00, 0.45, 1),
            ("Valéria", "Miolo", 1100.00, 0.88, 0),
            ("Sussuarana", "Miolo", 1300.00, 0.78, 0),
            ("Liberdade", "Centro", 1600.00, 0.65, 1),
            ("São Caetano", "Miolo", 1150.00, 0.85, 0),
        ]
        cursor.executemany(
            "INSERT INTO tabelas_contexto_regioes (nome_bairro, zona_administrativa, renda_media_familiar, indice_vulnerabilidade_social, presenca_iluminacao_publica) VALUES (?, ?, ?, ?, ?)",
            regioes
        )
        print("[DB] Regiões de Salvador populadas.")

    # --- Escolas ---
    cursor.execute("SELECT COUNT(*) FROM tabelas_educacao_escolas")
    if cursor.fetchone()[0] == 0:
        escolas = [
            (1, "CE Nelson Mandela", -12.9200, -38.5100, 820, "Integral"),
            (2, "EM Cajazeiras XI", -12.9080, -38.4400, 1100, "Matutino/Vespertino"),
            (3, "CE Mestre Waldemar", -12.9380, -38.3750, 650, "Matutino"),
            (4, "CE Thales de Azevedo", -12.9850, -38.4500, 900, "Integral"),
            (5, "CE da Bahia (Central)", -12.9730, -38.5120, 1400, "Matutino/Vespertino/Noturno"),
            (6, "EM Edgard Santos", -12.9820, -38.5050, 480, "Vespertino"),
            (7, "EM Valéria I", -12.8900, -38.4300, 550, "Matutino"),
            (8, "CE Sussuarana", -12.9150, -38.4350, 700, "Matutino/Vespertino"),
            (9, "CE da Liberdade", -12.9650, -38.5000, 950, "Integral"),
            (10, "EM São Caetano", -12.9350, -38.4800, 600, "Matutino"),
        ]
        cursor.executemany(
            "INSERT INTO tabelas_educacao_escolas (id_regiao, nome_escola_mascarado, latitude, longitude, total_alunos_ativos, turno_funcionamento) VALUES (?, ?, ?, ?, ?, ?)",
            escolas
        )
        print("[DB] Escolas populadas.")

    # --- Alunos Anonimizados (Seed com SHA-256) ---
    cursor.execute("SELECT COUNT(*) FROM tabelas_educacao_alunos_anonimizados")
    if cursor.fetchone()[0] == 0:
        random.seed(42)
        alunos = []
        for escola_id in range(1, 11):
            for i in range(30):  # 30 alunos por escola
                nome_ficticio = f"aluno_{escola_id}_{i}_{random.randint(1000, 9999)}"
                hash_aluno = gerar_hash_aluno(nome_ficticio)
                idade = random.randint(12, 18)
                assiduidade = round(random.uniform(45.0, 99.0), 2)
                evasao_risco = 1 if assiduidade < 75.0 else 0
                ocorrencias_disc = random.randint(0, 5) if assiduidade < 80 else 0
                alunos.append((hash_aluno, escola_id, idade, assiduidade, evasao_risco, ocorrencias_disc))
        cursor.executemany(
            "INSERT INTO tabelas_educacao_alunos_anonimizados (id_aluno_hash, id_escola, idade_atual, taxa_assiduidade_trimestre, flag_evasao_risco, qtd_ocorrencias_disciplinares) VALUES (?, ?, ?, ?, ?, ?)",
            alunos
        )
        print(f"[DB] {len(alunos)} alunos anonimizados (SHA-256) inseridos.")

    # --- Ocorrências SSP-BA (Seed) ---
    cursor.execute("SELECT COUNT(*) FROM tabelas_seguranca_ocorrencias")
    if cursor.fetchone()[0] == 0:
        random.seed(99)
        tipos_delito = ["Tráfico de Drogas", "Roubo", "Furto", "Agressão", "Porte Ilegal de Arma", "Vandalismo"]
        ocorrencias = []
        for regiao_id in range(1, 11):
            # Regiões com maior vulnerabilidade geram mais ocorrências
            qtd = random.randint(8, 35) if regiao_id in [1, 2, 7, 8, 10] else random.randint(2, 12)
            for j in range(qtd):
                bo = f"BO-SSP-{regiao_id:02d}-{j:04d}-2025"
                tipo = random.choice(tipos_delito)
                dias_atras = random.randint(0, 90)
                data_fato = (datetime.now() - timedelta(days=dias_atras)).strftime("%Y-%m-%d %H:%M:%S")
                lat = round(-12.92 + random.uniform(-0.08, 0.08), 6)
                lon = round(-38.48 + random.uniform(-0.06, 0.06), 6)
                menor_vitima = 1 if random.random() < 0.15 else 0
                menor_autor = 1 if random.random() < 0.10 else 0
                dist_escola = random.randint(50, 1200)
                ocorrencias.append((regiao_id, bo, tipo, data_fato, lat, lon, menor_vitima, menor_autor, dist_escola))
        cursor.executemany(
            "INSERT INTO tabelas_seguranca_ocorrencias (id_regiao, codigo_bo_mascarado, tipo_delito, data_hora_fato, latitude, longitude, flag_envolvimento_menor_vitima, flag_envolvimento_menor_autor, distancia_escola_proxima_metros) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ocorrencias
        )
        print(f"[DB] {len(ocorrencias)} ocorrências SSP-BA inseridas.")

    conn.commit()
    conn.close()
    print("[DB] Banco de Dados Integrado pronto!")


if __name__ == "__main__":
    init_db()
