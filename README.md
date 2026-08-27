# SAD-EduSeg: Segurança Pública e Educação 🛡️📚

**Sistema de Apoio à Decisão Cognitivo para o Governo da Bahia**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://agenda-publica-vhw4hpnsqdmtwrgwynes2h.streamlit.app/)
**Acesse o aplicativo online:** [https://agenda-publica-vhw4hpnsqdmtwrgwynes2h.streamlit.app/](https://agenda-publica-vhw4hpnsqdmtwrgwynes2h.streamlit.app/)

Este repositório contém o protótipo executável do **SAD-EduSeg**, desenvolvido como trabalho prático para a disciplina de Sistemas de Apoio à Decisão da **Escola de Administração da UFBA (EAUFBA)**.

## 🎯 Sobre o Projeto

O aplicativo é um Sistema de Apoio à Decisão (SAD) voltado para gestores públicos de altíssimo nível (Secretários Estaduais de Segurança e de Educação). Ele integra dados sobre **Evasão Escolar (MEC/INEP)** e **Criminalidade (SSP-BA)**, suportando a tomada de decisão para a alocação orçamentária preditiva e eficiente em escolas de Salvador.

O sistema opera com uma arquitetura híbrida inteligente, contando com:
- **Painel do Gestor (Simulador)**: Permite dosar orçamentos de Patrulhamento Policial vs Assistência Pedagógica, gerando recomendações baseadas no risco geográfico da região.
- **Engenharia de Dados (KDD)**: 
  - **Agrupamento (K-Means):** Segmenta as escolas de Salvador em clusters de vulnerabilidade (Crítico, Moderado, Estável).
  - **Regressão Linear:** Projeta a tendência de correlação entre os índices criminais (CVLI/Furtos) e as taxas de evasão.
- **Integração de APIs**: Simulação de consumo do Portal de Dados Abertos (`dados.gov.br`) via protocolo CKAN e geolocalização com OpenStreetMap.
- **IA Generativa (Copiloto do Gestor)**: Assistente Inteligente integrado nativamente usando o modelo Llama 3 via **API da Groq**. O Copiloto contextualiza os indicadores da escola selecionada e ajuda o Secretário a formular a melhor decisão de política pública em texto livre, em tempo real.

## ⚙️ Tecnologias Utilizadas

- **Python 3.11+**
- **Streamlit**: Interface, roteamento por perfil e gerenciamento de estado.
- **SQLite3**: Banco de Dados Relacional nativo (`sad_eduseg.db`).
- **Scikit-Learn**: Machine Learning (Regressão e K-Means).
- **Pandas, NumPy, Matplotlib**: Tratamento de Dataframes e mineração visual de dados.
- **Groq API (`groq`)**: LLM Ultra-rápido (Llama 3 8B) para atuar como Copiloto Especialista.

## 🚀 Como executar localmente

1. Clone o repositório:
```bash
git clone https://github.com/carlosjesusj748-blip/agenda-publica.git
cd agenda-publica
```

2. Instale as dependências necessárias:
```bash
pip install -r requirements.txt
```

3. Inicialize o Banco de Dados Cadastral (SQLite):
```bash
python database.py
```

4. Execute o aplicativo:
```bash
streamlit run agenda-publica-app.py
```

## 🔐 Logins Padrão de Teste
- **Gestor Público:** `Gestor Publico` | Senha: `123`
- **Analista KDD:** `Analista KDD` | Senha: `123`
- **Admin APIs:** `Admin Dominio` | Senha: `admin`

## 📂 Estrutura Principal
- `agenda-publica-app.py`: Interface principal do Streamlit, com painéis roteados por perfil e integração do Chatbot Groq/Llama3.
- `database.py`: Motor de inicialização do SQLite com injeção de dados mocados (IDEB, Evasão e CVLI) do Estado da Bahia.
- `requirements.txt`: Dependências essenciais.
