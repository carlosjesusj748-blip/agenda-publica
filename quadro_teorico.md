# SAD-AgendaPública: Fundamentação Teórica e Modelo Conceitual

## 1. Definição do Tema
**Tema:** Regulação do Trabalho por Plataformas Digitais no Brasil sob a Ótica da Gestão Pública.
**Objeto do Sistema:** Um Sistema de Apoio à Decisão (SAD) Híbrido, combinando técnicas Data-Driven (orientadas a dados históricos e API) e Model-Driven (modelagem estocástica multicritério), projetado para auxiliar gestores governamentais (como os do Ministério do Trabalho e Emprego - MTE) na formulação de propostas legislativas orçamentárias.

## 2. Quadro Teórico e Literatura
O referencial teórico do projeto sustenta-se nas seguintes frentes:
1.  **Teoria dos Fluxos Múltiplos (John Kingdon, 2011):** Explica como um problema entra na "Agenda Pública". O SAD avalia o *Fluxo do Problema* (alta desproteção social), o *Fluxo das Políticas* (propostas em tramitação na Câmara) e o *Fluxo Político* (clima no Congresso) para calcular as "Janelas de Oportunidade" de regulação.
2.  **Sistemas de Apoio à Decisão (Turban et al., 2009):** Justifica a arquitetura do software. Decisões orçamentárias de Estado são tipicamente "não estruturadas" ou "semi-estruturadas", requerendo um SAD que mescle modelos analíticos (KDD) e o julgamento humano do gestor (Simulador Interativo).
3.  **Capitalismo de Plataforma e Precarização Social (Srnicek, 2017; Antunes, 2020):** Fundamenta o conceito de "Trabalho por Demanda" e justifica a necessidade técnica de calcular pisos salariais mínimos (R$/Hora Conectada) para mitigar externalidades negativas na saúde pública e na previdência (INSS).

## 3. Seleção e Definição das Variáveis

O SAD utiliza as seguintes variáveis em seus Modelos Multicritério e KDD:

### Variáveis Independentes (Inputs do Gestor / Variáveis Táticas)
*   `piso_sugerido`: Valor monetário (R$) imposto por hora trabalhada. (Contínua)
*   `aliquota_patronal`: Percentual (%) de contribuição obrigatória das plataformas ao INSS. (Contínua)
*   `aliquota_trabalhador`: Percentual (%) descontado do autônomo para o INSS. (Contínua)
*   `clima_politico`: Nível de aderência da coalizão legislativa (Altamente Favorável, Moderado, Oposição). (Categórica Ordinal)

### Variáveis Dependentes (Outputs Preditivos do Sistema)
*   `arrecadacao_estimada`: Volume financeiro projetado para o caixa da união. (Contínua)
*   `risco_paralisia`: Probabilidade da proposta ser vetada no congresso. (Categórica: Alto, Médio, Baixo)
*   `blend_recomendado`: Recomendação tática ativa do SAD (Opção A, B ou C). (Categórica)

### Variáveis do Processo de KDD (Base de Dados Relacional)
*   `trabalhadores_ativos`: Quantidade em milhões de entregadores no país segundo a PNAD. Usada na **Regressão Linear Preditiva**.
*   `poder_influencia` e `aliado_trabalhadores`: Scores qualitativos atribuídos aos Atores Políticos (ex: Sindicatos, iFood). Usados no Algoritmo de Agrupamento **K-Means**.
*   `eventos_historicos`: Conjunto de eventos de pressão (decisões do STF, greves, GTs do governo). Usados no Algoritmo de **Associação (Apriori)** para minerar regras de causa-consequência na formulação da agenda.

## 4. Metodologia do Banco de Dados
A modelagem de dados adota a abordagem **Cadastral (Banco de Dados Relacional Estruturado)**, em oposição à amostragem estatística tradicional. Todas as informações inseridas representam o catálogo integral dos objetos mapeados pelo Quadro Teórico (e.g., *todas* as propostas de lei relevantes ativas, *todos* os atores mapeados), minimizando viés de seleção nas funções de Inteligência Artificial.
