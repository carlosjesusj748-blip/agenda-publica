# SAD-AgendaPública 📊

**Sistema de Apoio à Decisão para Regulação do Trabalho por Aplicativos no Brasil**

Este repositório contém o protótipo executável do **SAD-AgendaPública**, desenvolvido como Trabalho de Conclusão de Curso para a **Escola de Administração da UFBA (EAUFBA)**.

## 🎯 Sobre o Projeto

O aplicativo é um Sistema de Apoio à Decisão (SAD) desenhado para formuladores de políticas públicas (como o MTE - Ministério do Trabalho e Emprego). O painel permite simular e avaliar impactos na arrecadação tributária e proteção trabalhista de motoristas e entregadores de aplicativos no Brasil.

O sistema opera com uma arquitetura que integra três camadas de dados:
- **Ipea e PNAD Contínua**: Dados macroeconômicos e demográficos da categoria.
- **API da Câmara dos Deputados**: Busca de projetos de lei em tempo real.
- **Motor de Decisão Ativo**: Algoritmos que mesclam "Blend de Opções" regulatórias.

## ⚙️ Tecnologias Utilizadas

- **Python 3.11+**
- **Streamlit**: Para a interface de usuário (Dashboard e Simulador).
- **Pandas & NumPy**: Tratamento e análise de dados.
- **Scikit-Learn**: Para processamento de KDD (Clustering/Agrupamento).
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
