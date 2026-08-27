-- =========================================================================
-- MODELO DE BANCO DE DADOS: INTEGRAÇÃO SEGURANÇA PÚBLICA E EDUCAÇÃO
-- OBJETIVO: Cruzamento analítico para prevenção e inteligência social
-- DIRETRIZ: Compatível com LGPD (Anonimização e Controle de Acesso Restrito)
-- =========================================================================

CREATE SCHEMA IF NOT EXISTS integracao_seg_edu;
SET search_path TO integracao_seg_edu;

-- -------------------------------------------------------------------------
-- Tabela: regioes_contexto (Dados Socioeconômicos)
-- -------------------------------------------------------------------------
CREATE TABLE tabelas_contexto_regioes (
    id_regiao INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome_bairro VARCHAR(100) NOT NULL,
    zona_administrativa VARCHAR(50),
    renda_media_familiar NUMERIC(10, 2),
    indice_vulnerabilidade_social NUMERIC(3, 2), -- Escala de 0.00 a 1.00
    presenca_iluminacao_publica BOOLEAN DEFAULT TRUE,
    data_ultima_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- -------------------------------------------------------------------------
-- Tabela: escolas (Dados Educacionais - Infraestrutura)
-- -------------------------------------------------------------------------
CREATE TABLE tabelas_educacao_escolas (
    id_escola INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_regiao INT REFERENCES tabelas_contexto_regioes(id_regiao),
    nome_escola_mascarado VARCHAR(100) NOT NULL,
    latitude DECIMAL(9, 6),
    longitude DECIMAL(9, 6),
    total_alunos_ativos INT,
    turno_funcionamento VARCHAR(50) -- Matutino, Vespertino, Noturno, Integral
);

-- -------------------------------------------------------------------------
-- Tabela: alunos_anonimizados (Dados Educacionais - Perfil)
-- -------------------------------------------------------------------------
CREATE TABLE tabelas_educacao_alunos_anonimizados (
    id_aluno_hash VARCHAR(64) PRIMARY KEY, -- SHA-256 gerado na origem (Educação)
    id_escola INT REFERENCES tabelas_educacao_escolas(id_escola),
    idade_atual INT,
    taxa_assiduidade_trimestre NUMERIC(5, 2), -- Ex: 85.50 para 85.5%
    flag_evasao_risco BOOLEAN DEFAULT FALSE,
    qtd_ocorrencias_disciplinares INT DEFAULT 0
);

-- -------------------------------------------------------------------------
-- Tabela: ocorrencias_seguranca (Dados de Segurança Pública)
-- -------------------------------------------------------------------------
CREATE TABLE tabelas_seguranca_ocorrencias (
    id_ocorrencia INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_regiao INT REFERENCES tabelas_contexto_regioes(id_regiao),
    codigo_bo_mascarado VARCHAR(50) UNIQUE NOT NULL,
    tipo_delito VARCHAR(100) NOT NULL, -- Ex: Tráfico de Drogas, Roubo, Agressão
    data_hora_fato TIMESTAMP NOT NULL,
    latitude DECIMAL(9, 6),
    longitude DECIMAL(9, 6),
    flag_envolvimento_menor_vitima BOOLEAN DEFAULT FALSE,
    flag_envolvimento_menor_autor BOOLEAN DEFAULT FALSE,
    distancia_escola_proxima_metros INT
);

-- -------------------------------------------------------------------------
-- Tabela: logs_auditoria (Governança e Segurança da Informação)
-- -------------------------------------------------------------------------
CREATE TABLE sistema_logs_auditoria (
    id_log BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    usuario_id VARCHAR(50) NOT NULL,
    orgao_usuario VARCHAR(50) NOT NULL, -- 'POLICIA_CIVIL', 'SEC_EDUCACAO', etc.
    acao_executada VARCHAR(100) NOT NULL,
    tabela_acessada VARCHAR(100),
    data_hora_acesso TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_origem VARCHAR(45)
);

-- =========================================================================
-- VISÕES ANALÍTICAS PARA PAINÉIS DE BI (DASHBOARD)
-- =========================================================================

-- Vista 1: Alerta de vulnerabilidade escolar por entorno criminal
CREATE OR REPLACE VIEW vw_alerta_vulnerabilidade_escolas AS
SELECT 
    e.id_escola,
    e.nome_escola_mascarado,
    r.nome_bairro,
    e.total_alunos_ativos,
    COUNT(o.id_ocorrencia) AS qtd_crimes_entorno_90_dias,
    ROUND(AVG(a.taxa_assiduidade_trimestre), 2) AS media_assiduidade_alunos
FROM tabelas_educacao_escolas e
JOIN tabelas_contexto_regioes r ON e.id_regiao = r.id_regiao
LEFT JOIN tabelas_educacao_alunos_anonimizados a ON e.id_escola = a.id_escola
LEFT JOIN tabelas_seguranca_ocorrencias o ON o.id_regiao = r.id_regiao 
    AND o.distancia_escola_proxima_metros <= 500
    AND o.data_hora_fato >= CURRENT_TIMESTAMP - INTERVAL '90 days'
GROUP BY e.id_escola, e.nome_escola_mascarado, r.nome_bairro, e.total_alunos_ativos;
