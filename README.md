# SAD-AgendaPública 📊

**Sistema de Apoio à Decisão para Regulação do Trabalho por Aplicativos no Brasil**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://agenda-publica-vhw4hpnsqdmtwrgwynes2h.streamlit.app/)
**Acesse o aplicativo online:** [https://agenda-publica-vhw4hpnsqdmtwrgwynes2h.streamlit.app/](https://agenda-publica-vhw4hpnsqdmtwrgwynes2h.streamlit.app/)

    Este repositório contém o protótipo executável do **SAD-AgendaPública**, desenvolvido como trabalho prático para a disciplina de Sistemas de Apoio à Decisão da **Escola de Administração da UFBA (EAUFBA)**.

## 🎯 Sobre o Projeto

O aplicativo é um Sistema de Apoio à Decisão (SAD) desenhado para formuladores de políticas públicas (como o MTE - Ministério do Trabalho e Emprego). O painel permite simular e avaliar impactos na arrecadação tributária e proteção trabalhista de motoristas e entregadores de aplicativos no Brasil.

O sistema opera com uma arquitetura que integra as seguintes camadas e funções:
- **Painel de Decisão Multicritério**: Lógica baseada em "Blend de Opções" para identificar o risco político e as melhores escolhas.
- **Engenharia de Dados (KDD)**: 
  - **Regressão Linear:** Para projeção temporal da quantidade de trabalhadores desprotegidos utilizando dados da PNAD.
  - **Agrupamento (K-Means):** Clustering avançado para separar os stakeholders do espectro político nacional.
- **API da Câmara dos Deputados**: Busca de projetos de lei em tempo real.

## ⚙️ Tecnologias Utilizadas

- **Python 3.11+**
- **Streamlit**: Para a interface de usuário (Dashboard e Simulador).
- **Pandas & NumPy**: Tratamento e análise de dados matemáticos.
- **Scikit-Learn**: Para processamento de Machine Learning (Regressão e Clustering K-Means).
- **Matplotlib**: Geração gráfica dos agrupamentos de dados e retas de projeção.
- **Requests**: Integração com a API da Câmara dos Deputados.

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

3. Execute o aplicativo:
```bash
streamlit run agenda-publica-app.py
```

## 📂 Estrutura de Arquivos
- `agenda-publica-app.py`: Interface gráfica e lógica principal (Dashboard, Regressões, Clustering).
- `camara_api.py`: Script para coleta e processamento de Projetos de Lei via API Pública da Câmara.
- `requirements.txt`: Lista de pacotes dependentes para execução no Streamlit Cloud.
