import sqlite3
import pandas as pd
import os

DB_NAME = "sad_database.db"

def init_db():
    print("[DB] Inicializando o Banco de Dados Cadastral do SAD...")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Tabela 1: Usuários do Sistema (Controle de Acesso)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            senha TEXT NOT NULL,
            perfil TEXT NOT NULL
        )
    ''')

    # Tabela 2: Proposições de Leis (Integração com API)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS proposicoes_leis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sigla_numero TEXT NOT NULL,
            ano INTEGER,
            ementa TEXT,
            viabilidade TEXT
        )
    ''')

    # Tabela 3: Atores Políticos (Base para K-Means)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS atores_stakeholders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ator TEXT NOT NULL,
            poder_influencia TEXT,
            aliado_trabalhadores TEXT
        )
    ''')

    # Tabela 4: Eventos Históricos (Base para Apriori/Associação - Via CSV)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS eventos_impacto (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            tipo_evento TEXT,
            ator_principal TEXT,
            impacto_agenda REAL
        )
    ''')

    # Populando Usuários Padrão se a tabela estiver vazia
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO usuarios (nome, senha, perfil) VALUES ('Decisor MTE', '123', 'Usuário Decisor')")
        cursor.execute("INSERT INTO usuarios (nome, senha, perfil) VALUES ('Data Analyst', '123', 'Analista de Dados')")
        cursor.execute("INSERT INTO usuarios (nome, senha, perfil) VALUES ('Admin Dominio', 'admin', 'Analista de Domínio')")
        print("[DB] Usuários padrão criados.")

    # Populando Atores se vazio (Base Teórica)
    cursor.execute("SELECT COUNT(*) FROM atores_stakeholders")
    if cursor.fetchone()[0] == 0:
        atores_iniciais = [
            ("Plataformas (iFood/Uber)", "alto", "baixo"),
            ("Sindicatos Trabalhistas", "médio", "alto"),
            ("Ministério do Trabalho", "alto", "alto"),
            ("Mídia Hegemônica", "médio", "baixo"),
            ("Entregadores Autônomos", "baixo", "médio")
        ]
        cursor.executemany("INSERT INTO atores_stakeholders (ator, poder_influencia, aliado_trabalhadores) VALUES (?, ?, ?)", atores_iniciais)

    # Lendo o CSV real e populando a tabela de Eventos, se existir
    csv_file = "banco de dados.xlsx.csv"
    cursor.execute("SELECT COUNT(*) FROM eventos_impacto")
    if cursor.fetchone()[0] == 0 and os.path.exists(csv_file):
        df_csv = pd.read_csv(csv_file)
        # Filtra apenas as colunas que importam para o banco simplificado de Associação
        for index, row in df_csv.iterrows():
            cursor.execute("INSERT INTO eventos_impacto (data, tipo_evento, ator_principal, impacto_agenda) VALUES (?, ?, ?, ?)",
                           (str(row.get('data', '')), str(row.get('tipo_evento', '')), str(row.get('ator_principal', '')), float(row.get('impacto_agenda', 0.0))))
        print("[DB] Tabela de Eventos populada a partir do CSV real.")

    conn.commit()
    conn.close()
    print("[DB] Banco de Dados atualizado com sucesso!")

if __name__ == "__main__":
    init_db()
