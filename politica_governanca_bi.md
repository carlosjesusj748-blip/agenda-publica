# Política de Governança, Privacidade e Metadados do Projeto SegEdu

Este documento estabelece as diretrizes de segurança, governança de dados segundo a LGPD (Lei Geral de Proteção de Dados) e a especificação dos indicadores de Business Intelligence para o ecossistema integrado de Segurança Pública e Educação.

---

## 1. POLÍTICA DE GOVERNANÇA E PRIVACIDADE (LGPD)

### 1.1 Princípio da Minimização e Finalidade
*   **Finalidade Exclusiva:** Os dados integrados neste ambiente destinam-se unicamente à formulação de políticas públicas de prevenção à violência, proteção de menores e mitigação da evasão escolar. É vedado o uso para fins puramente punitivos automáticos sem o devido processo legal.
*   **Minimização:** Nomes, CPFs, RGs e endereços residenciais exatos de estudantes **não entram** na base compartilhada. Toda a identificação individual é substituída por um identificador hash criptográfico unidirecional (`id_aluno_hash`) gerado na origem pela Secretaria de Educação.

### 1.2 Controle de Acesso Baseado em Funções (RBAC)
*   **Perfil Gestor Educacional:** Acesso exclusivo aos dados de assiduidade, ocorrências disciplinares internas e alertas macro de vulnerabilidade do entorno. Não visualiza boletins de ocorrência detalhados.
*   **Perfil Analista de Segurança:** Acesso às manchas criminais, perfis de delitos no entorno das escolas e estatísticas de envolvimento de menores. Não visualiza o histórico escolar individualizado do aluno hash.
*   **Perfil Administrador do Sistema:** Acesso restrito à manutenção da infraestrutura e auditoria completa de logs, sem acesso de leitura às tabelas de dados de negócio.

### 1.3 Retenção e Descarte de Dados
*   Os dados de alunos anonimizados serão mantidos na base ativa por até 3 anos após o encerramento do vínculo do aluno com a rede pública de ensino, sendo posteriormente eliminados ou agregados para fins estritamente estatísticos históricos.

---

## 2. ESPECIFICAÇÃO DE INDICADORES PARA DASHBOARD (BI)

Para subsidiar tomadas de decisão céleres pelas pastas, o painel de BI deve implementar os seguintes eixos analíticos:

### Eixo A: Alerta Precoce de Evasão e Vulnerabilidade
*   **Métrica 1: Índice de Assiduidade Crítica (IAC)**
    *   *Fórmula:* `(Total de Alunos com Assiduidade < 75% / Total de Alunos Ativos) * 100`
    *   *Objetivo:* Identificar turmas e escolas que necessitam de busca ativa escolar.
*   **Métrica 2: Correlação Disciplinar-Criminal**
    *   *Descrição:* Cruzamento entre o volume de ocorrências disciplinares internas da escola com o índice de criminalidade do entorno em um raio de até 500 metros.

### Eixo B: Segurança de Perímetro e Mancha Criminal
*   **Métrica 3: Densidade Criminal Escolar (DCE)**
    *   *Fórmula:* `Quantidade de Ocorrências no Raio de 500m da Escola / Área do Perímetro Amostrado`
    *   *Segmentação:* Filtros por tipo de delito (Tráfico, Roubo, Furto) e por turno escolar (Entrada/Saída dos estudantes).
*   **Métrica 4: Taxa de Envolvimento de Menores no Entorno**
    *   *Fórmula:* `(Ocorrências com Menor Autor ou Vítima próximo à escola / Total de Ocorrências próximo à escola) * 100`

---

## 3. MATRIZ DE RASTREABILIDADE E AUDITORIA
Toda e qualquer consulta realizada na base integrada acionará um gatilho automático de gravação na tabela `sistema_logs_auditoria`, registrando a identidade digital do agente público, o órgão de lotação e a justificativa do acesso.
