import sqlite3
import pandas as pd
import os

DB_NAME = "sad_eduseg.db"

def init_db():
    print("[DB] Inicializando o Banco de Dados Cadastral do SAD-EduSeg...")
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

    # Tabela 2: Escolas e Risco (Para Clustering K-Means)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS escolas_risco (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_escola TEXT NOT NULL,
            bairro TEXT NOT NULL,
            taxa_evasao REAL,
            ideb REAL,
            ocorrencias_entorno INTEGER
        )
    ''')

    # Tabela 3: Ocorrências SSP-BA
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ocorrencias_ssp (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            tipo_crime TEXT,
            bairro TEXT,
            latitude REAL,
            longitude REAL
        )
    ''')

    # Populando Usuários Padrão se a tabela estiver vazia
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO usuarios (nome, senha, perfil) VALUES ('Gestor Publico', '123', 'Gestor Público')")
        cursor.execute("INSERT INTO usuarios (nome, senha, perfil) VALUES ('Analista KDD', '123', 'Analista KDD')")
        cursor.execute("INSERT INTO usuarios (nome, senha, perfil) VALUES ('Admin Dominio', 'admin', 'Admin Domínio')")
        print("[DB] Usuários padrão criados.")

    # Populando Escolas Mock para Salvador se vazio
    cursor.execute("SELECT COUNT(*) FROM escolas_risco")
    if cursor.fetchone()[0] == 0:
        escolas = [
            ("Colégio Estadual Nelson Mandela", "Periperi", 15.4, 3.8, 120),
            ("Colégio Thales de Azevedo", "Costa Azul", 2.1, 5.9, 15),
            ("Escola Municipal de Cajazeiras", "Cajazeiras", 18.2, 3.5, 145),
            ("Centro Educacional Edgard Santos", "Garcia", 8.5, 4.5, 40),
            ("Colégio Estadual da Bahia (Central)", "Nazaré", 5.2, 5.0, 55),
            ("Escola Municipal de Itapuã", "Itapuã", 11.3, 4.0, 90)
        ]
        cursor.executemany("INSERT INTO escolas_risco (nome_escola, bairro, taxa_evasao, ideb, ocorrencias_entorno) VALUES (?, ?, ?, ?, ?)", escolas)
        print("[DB] Tabela de Escolas populada com dados simulados.")

    conn.commit()
    conn.close()
    print("[DB] Banco de Dados atualizado com sucesso!")

if __name__ == "__main__":
    init_db()
