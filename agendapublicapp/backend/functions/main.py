# ============================================================
# AGENDAPUBLICAPP - BACKEND (Flask)
# Deploy no Firebase Cloud Functions
# ============================================================

import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, request, jsonify, send_file
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import io
import base64
from datetime import datetime

# ============================================================
# Configuração Firebase
# ============================================================

# Inicializar Firebase Admin SDK
if not firebase_admin._apps:
    # Em produção, usar variável de ambiente
    cred_path = os.environ.get('FIREBASE_SERVICE_ACCOUNT', 'serviceAccountKey.json')
    try:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        print(f"Warning: Could not initialize Firebase Admin SDK with {cred_path}: {e}")
        # firebase_admin.initialize_app() # Try default

try:
    db = firestore.client()
except Exception as e:
    print(f"Warning: Could not initialize Firestore client: {e}")
    db = None

app = Flask(__name__)

# ============================================================
# ROTAS DA API
# ============================================================

@app.route('/')
def home():
    return jsonify({
        'nome': 'AgendaPúblicaApp',
        'versao': '1.0.0',
        'status': 'online',
        'descricao': 'Sistema de Apoio à Decisão - Agenda dos Trabalhadores de Aplicativos'
    })

@app.route('/api/eventos', methods=['GET'])
def get_eventos():
    """Retorna todos os eventos do Firestore"""
    if not db:
         return jsonify({'erro': 'Banco de dados não inicializado'}), 500
    try:
        eventos_ref = db.collection('eventos').stream()
        eventos = []
        for doc in eventos_ref:
            data = doc.to_dict()
            data['id'] = doc.id
            eventos.append(data)
        return jsonify(eventos)
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@app.route('/api/indicadores', methods=['GET'])
def get_indicadores():
    """Retorna todos os indicadores anuais"""
    if not db:
         return jsonify({'erro': 'Banco de dados não inicializado'}), 500
    try:
        ind_ref = db.collection('indicadores').order_by('ano').stream()
        indicadores = []
        for doc in ind_ref:
            data = doc.to_dict()
            data['id'] = doc.id
            indicadores.append(data)
        return jsonify(indicadores)
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@app.route('/api/analise', methods=['GET'])
def get_analise():
    """Executa a análise completa e retorna resultados"""
    if not db:
         return jsonify({'erro': 'Banco de dados não inicializado'}), 500
    try:
        # Buscar dados do Firestore
        eventos = [doc.to_dict() for doc in db.collection('eventos').stream()]
        indicadores = [doc.to_dict() for doc in db.collection('indicadores').order_by('ano').stream()]

        # Calcular impacto por ator
        atores = {}
        for e in eventos:
            ator = e.get('ator', 'desconhecido')
            if ator not in atores:
                atores[ator] = []
            atores[ator].append(e.get('impacto', 0))
            
        impacto_atores = {}
        for ator, valores in atores.items():
            impacto_atores[ator] = sum(valores) / len(valores) if len(valores) > 0 else 0

        # Calcular correlação mídia x impacto
        midia = [e.get('midia', 0) for e in eventos]
        impacto = [e.get('impacto', 0) for e in eventos]

        # Score combinado
        score_paralisacao = calcular_score_estrategia(eventos, 'paralisacao')
        score_projetos = calcular_score_estrategia(eventos, 'projeto_lei')

        return jsonify({
            'impacto_atores': impacto_atores,
            'total_eventos': len(eventos),
            'total_indicadores': len(indicadores),
            'score_paralisacao': score_paralisacao,
            'score_projetos': score_projetos,
            'recomendacao': gerar_recomendacao(score_paralisacao, score_projetos)
        })
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def calcular_score_estrategia(eventos, tipo):
    """Calcula score de efetividade por tipo de evento"""
    eventos_tipo = [e for e in eventos if tipo in e.get('tipo', '')]
    if not eventos_tipo:
        return 0.0
    return sum(e.get('impacto', 0) for e in eventos_tipo) / len(eventos_tipo)

def gerar_recomendacao(score_paral, score_proj):
    """Gera recomendação baseada nos scores"""
    if score_paral > 0.70:
        return {
            'nivel': 'alta',
            'mensagem': 'Paralisação é a estratégia mais efetiva (score {:.2f})'.format(score_paral),
            'acao': 'Manter ações diretas e ampliar visibilidade midiática'
        }
    elif score_proj > 0.70:
        return {
            'nivel': 'alta',
            'mensagem': 'Projetos de lei são a estratégia mais efetiva (score {:.2f})'.format(score_proj),
            'acao': 'Fortalecer articulação institucional'
        }
    else:
        return {
            'nivel': 'media',
            'mensagem': 'Combinar paralisações e projetos de lei',
            'acao': 'Estratégia híbrida recomendada'
        }

# ============================================================
# ROTA PARA GRÁFICOS
# ============================================================

@app.route('/api/grafico/<tipo>', methods=['GET'])
def get_grafico(tipo):
    """Gera gráfico e retorna como imagem base64"""
    if not db:
         return jsonify({'erro': 'Banco de dados não inicializado'}), 500
    try:
        if tipo == 'impacto_atores':
            return gerar_grafico_impacto_atores()
        elif tipo == 'evolucao':
            return gerar_grafico_evolucao()
        elif tipo == 'correlacao':
            return gerar_grafico_correlacao()
        else:
            return jsonify({'erro': 'Tipo de gráfico não encontrado'}), 404
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

def gerar_grafico_impacto_atores():
    """Gera gráfico de impacto por ator"""
    # Buscar dados
    eventos = [doc.to_dict() for doc in db.collection('eventos').stream()]
    
    # Calcular médias
    atores = {}
    for e in eventos:
        ator = e.get('ator', 'desconhecido')
        if ator not in atores:
            atores[ator] = []
        atores[ator].append(e.get('impacto', 0))
        
    if not atores:
        return jsonify({'erro': 'Sem dados'})

    nomes = list(atores.keys())
    valores = [sum(v)/len(v) for v in atores.values()]

    # Criar gráfico
    fig, ax = plt.subplots(figsize=(10, 6))
    cores = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#6A994E', '#FF6B6B', '#4ECDC4']
    bars = ax.bar(nomes, valores, color=cores[:len(nomes)])
    
    ax.set_ylim(0, 1)
    ax.set_ylabel('Impacto Médio')
    ax.set_title('Impacto na Agenda por Ator', fontsize=14, fontweight='bold')
    
    ax.axhline(y=sum(valores)/len(valores), color='red', linestyle='--')
    
    for bar, val in zip(bars, valores):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02, 
                f'{val:.2f}', ha='center', va='bottom')
                
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    # Salvar em buffer e converter para base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    plt.close()
    
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return jsonify({'imagem': img_base64, 'formato': 'png'})

def gerar_grafico_evolucao():
    """Gera gráfico de evolução temporal"""
    indicadores = [doc.to_dict() for doc in db.collection('indicadores').order_by('ano').stream()]
    
    if not indicadores:
         return jsonify({'erro': 'Sem dados'})

    anos = [i['ano'] for i in indicadores]
    trabalhadores = [i.get('trabalhadores_milhoes', 0) for i in indicadores]
    impacto = [i.get('impacto_agenda_medio', 0) for i in indicadores]

    fig, ax1 = plt.subplots(figsize=(10, 6))

    ax1.set_xlabel('Ano')
    ax1.set_ylabel('Trabalhadores (milhões)', color='blue')
    ax1.plot(anos, trabalhadores, 'o-', color='blue', linewidth=2, label='Trabalhadores')
    ax1.tick_params(axis='y', labelcolor='blue')

    ax2 = ax1.twinx()
    ax2.set_ylabel('Impacto na Agenda', color='red')
    ax2.plot(anos, impacto, 's-', color='red', linewidth=2, label='Impacto')
    ax2.tick_params(axis='y', labelcolor='red')
    ax2.set_ylim(0, 1)

    plt.title('Evolução: Trabalhadores e Impacto (2018-2026)', fontsize=14, fontweight='bold')
    ax1.legend(loc='upper left')
    ax2.legend(loc='upper right')
    
    plt.tight_layout()
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    plt.close()
    
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return jsonify({'imagem': img_base64, 'formato': 'png'})

def gerar_grafico_correlacao():
    """Gera gráfico de correlação mídia x impacto"""
    eventos = [doc.to_dict() for doc in db.collection('eventos').stream()]
    
    midia = [e.get('midia', 0) for e in eventos if e.get('midia', 0) > 0]
    impacto = [e.get('impacto', 0) for e in eventos if e.get('midia', 0) > 0]
    
    if not midia or not impacto:
        return jsonify({'erro': 'Sem dados'})

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(midia, impacto, s=80, alpha=0.7, color='#2E86AB')
    
    ax.set_xlabel('Menções na Mídia')
    ax.set_ylabel('Impacto na Agenda')
    ax.set_title('Relação: Mídia × Impacto', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    plt.close()
    
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return jsonify({'imagem': img_base64, 'formato': 'png'})

# ============================================================
# INICIALIZAÇÃO
# ============================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
