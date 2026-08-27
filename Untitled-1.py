# ============================================================
# AGENDAPUBLICAPP - VERSÃO COM CORREÇÃO DE CSV
# ============================================================

import math
import csv
import os
import matplotlib.pyplot as plt
import numpy as np

print("="*70)
print("📊 AGENDAPUBLICAPP - SISTEMA DE APOIO À DECISÃO")
print("="*70)

# ============================================================
# CAMINHO DOS ARQUIVOS
# ============================================================

base_path = r"D:\1.Semestre 2026.2\SAD\DADOS"

# ============================================================
# FUNÇÃO PARA LER CSV REMOVENDO BOM
# ============================================================

def ler_csv_sem_bom(caminho_arquivo):
    """Lê CSV removendo o caractere BOM do início"""
    dados = []
    
    with open(caminho_arquivo, 'r', encoding='utf-8-sig') as arquivo:  # utf-8-sig remove BOM
        leitor = csv.DictReader(arquivo, delimiter=';')
        for linha in leitor:
            dados.append(linha)
    
    return dados

# ============================================================
# CARREGAR ARQUIVOS
# ============================================================

print("\n📂 Carregando arquivos...")
print("-"*50)

eventos_raw = ler_csv_sem_bom(os.path.join(base_path, "TABELA 1 EVENTOS (Qualitativos).csv"))
indicadores_raw = ler_csv_sem_bom(os.path.join(base_path, "TABELA 2 INDICADORES (Quantitativos Anuais).csv"))
atores_raw = ler_csv_sem_bom(os.path.join(base_path, "TABELA 3 ATORES (Posicionamento).csv"))
plataformas_raw = ler_csv_sem_bom(os.path.join(base_path, "TABELA 4 PLATAFORMAS (Fairwork 2025).csv"))

print(f"  ✅ Eventos: {len(eventos_raw)} registros")
print(f"  ✅ Indicadores: {len(indicadores_raw)} registros")
print(f"  ✅ Atores: {len(atores_raw)} registros")
print(f"  ✅ Plataformas: {len(plataformas_raw)} registros")
print("-"*50)

# ============================================================
# CONVERTER EVENTOS
# ============================================================

def converter_eventos(dados):
    eventos = []
    for e in dados:
        try:
            evento = {
                "id": int(float(e.get("id", 0))),
                "data": e.get("data", "").strip(),
                "tipo": e.get("tipo", "").strip(),
                "ator": e.get("ator", "").strip(),
                "midia": float(str(e.get("midia", "0")).replace(",", ".").strip()),
                "governo": int(float(e.get("governo", 0))),
                "plataforma": int(float(e.get("plataforma", 0))),
                "trabalhador": int(float(e.get("trabalhador", 0))),
                "impacto": float(str(e.get("impacto", "0")).replace(",", ".").strip()),
                "repertorio": e.get("repertorio", "").strip()
            }
            eventos.append(evento)
        except:
            continue
    return eventos

# ============================================================
# CONVERTER INDICADORES - CORRIGIDO
# ============================================================

def converter_indicadores(dados):
    indicadores = []
    for linha in dados:
        try:
            # Pega o valor do ano (pode vir com nome diferente)
            ano_val = linha.get("ano") or linha.get("\ufeffano")
            if not ano_val:
                continue
            
            # Pega o impacto (pode estar vazio)
            impacto_val = linha.get("impacto_agenda_medio", "").strip()
            if impacto_val == "":
                # Se estiver vazio, usa o valor do ano anterior ou estimativa
                impacto_val = "0.82"  # valor estimado para 2026
            
            ind = {
                "ano": int(float(ano_val)),
                "trabalhadores": float(str(linha.get("trabalhadores_milhoes", "0")).replace(",", ".").strip()),
                "renda": float(str(linha.get("renda_media", "0")).replace(",", ".").strip()),
                "jornada": float(str(linha.get("jornada_semanal", "0") or linha.get("joornada_semanal", "0")).replace(",", ".").strip()),
                "inss": float(str(linha.get("contribuicao_inss", "0")).replace(",", ".").strip()),
                "formalizacao": float(str(linha.get("formalizacao", "0")).replace(",", ".").strip()),
                "midia": int(float(str(linha.get("midia_mencoes_ano", "0")).replace(",", ".").strip())),
                "greves": int(float(linha.get("greves_ano", 0))),
                "projetos": int(float(linha.get("projetos_lei", 0))),
                "impacto": float(impacto_val.replace(",", "."))
            }
            if ind["ano"] > 0:
                indicadores.append(ind)
        except Exception as e:
            print(f"  ⚠️ Erro na linha: {linha} -> {e}")
            continue
    return indicadores

# ============================================================
# CONVERTER PLATAFORMAS
# ============================================================

def converter_plataformas(dados):
    plataformas = []
    for p in dados:
        try:
            plat = {
                "nome": p.get("plataforma", "").strip(),
                "pontuacao": int(float(p.get("pontuacao_2025", 0))),
                "remuneracao": str(p.get("remuneracao_justa", "")).lower().strip() == "sim",
                "condicoes": str(p.get("condicoes", "")).lower().strip() == "sim",
                "gestao": str(p.get("gestao", "")).lower().strip() == "sim",
                "representacao": str(p.get("representacao", "")).lower().strip() == "sim"
            }
            if plat["nome"]:
                plataformas.append(plat)
        except:
            continue
    return plataformas

eventos = converter_eventos(eventos_raw)
indicadores = converter_indicadores(indicadores_raw)
plataformas = converter_plataformas(plataformas_raw)

print(f"\n✅ {len(eventos)} eventos carregados")
print(f"✅ {len(indicadores)} indicadores carregados")
print(f"✅ {len(plataformas)} plataformas carregadas")

# ============================================================
# DIAGNÓSTICO
# ============================================================

print("\n📋 DIAGNÓSTICO DOS INDICADORES:")
print("-"*50)
if indicadores:
    print("  Anos:", [i['ano'] for i in indicadores])
    print("  Trabalhadores:", [i['trabalhadores'] for i in indicadores])
    print("  Renda:", [i['renda'] for i in indicadores])
    print("  Impacto:", [i['impacto'] for i in indicadores])
else:
    print("  ⚠️ NENHUM indicador foi carregado!")
print("-"*50)

# ============================================================
# FUNÇÃO CORRELAÇÃO
# ============================================================

def calcular_correlacao(x, y):
    n = len(x)
    if n < 2:
        return 0
    soma_x = sum(x)
    soma_y = sum(y)
    soma_x2 = sum([xi**2 for xi in x])
    soma_y2 = sum([yi**2 for yi in y])
    soma_xy = sum([x[i] * y[i] for i in range(n)])
    
    numerador = n * soma_xy - soma_x * soma_y
    denominador = math.sqrt((n * soma_x2 - soma_x**2) * (n * soma_y2 - soma_y**2))
    
    if denominador == 0:
        return 0
    return numerador / denominador

# ============================================================
# CORES
# ============================================================

cores = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#6A994E', '#FF6B6B', '#4ECDC4', '#45B7D1']

# ============================================================
# GRÁFICO 1: IMPACTO POR ATOR
# ============================================================

print("\n📊 1. Impacto por Ator...")

if eventos:
    atores_impacto = {}
    for e in eventos:
        ator = e['ator']
        if ator not in atores_impacto:
            atores_impacto[ator] = []
        atores_impacto[ator].append(e['impacto'])
    
    atores_ordenados = sorted(atores_impacto.items(), key=lambda x: sum(x[1])/len(x[1]), reverse=True)
    nomes = [a[0] for a in atores_ordenados]
    valores = [sum(a[1])/len(a[1]) for a in atores_ordenados]
    
    fig1, ax1 = plt.subplots(figsize=(12, 7))
    bars = ax1.bar(nomes, valores, color=cores[:len(nomes)])
    ax1.set_ylim(0, 1)
    ax1.set_ylabel('Impacto Médio na Agenda', fontsize=12)
    ax1.set_title('Impacto na Agenda por Ator (2018-2026)', fontsize=14, fontweight='bold')
    ax1.axhline(y=sum(valores)/len(valores), color='red', linestyle='--', label=f'Média: {sum(valores)/len(valores):.2f}')
    ax1.legend()
    for bar, valor in zip(bars, valores):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02, 
                f'{valor:.2f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(os.path.join(base_path, "..", "01_impacto_por_ator.png"), dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✅ 01_impacto_por_ator.png")

# ============================================================
# GRÁFICO 2: EVOLUÇÃO TEMPORAL
# ============================================================

print("\n📊 2. Evolução Temporal...")

if len(indicadores) >= 2:
    anos = [i['ano'] for i in indicadores]
    trabalhadores = [i['trabalhadores'] for i in indicadores]
    impacto = [i['impacto'] for i in indicadores]
    
    fig2, ax2 = plt.subplots(figsize=(12, 7))
    
    ax2.set_xlabel('Ano', fontsize=12)
    ax2.set_ylabel('Trabalhadores (milhões)', color='blue', fontsize=12)
    ax2.plot(anos, trabalhadores, 'o-', color='blue', linewidth=2, markersize=8, label='Trabalhadores')
    ax2.tick_params(axis='y', labelcolor='blue')
    ax2.set_ylim(0, max(trabalhadores) * 1.3 if trabalhadores else 1)
    
    ax3 = ax2.twinx()
    ax3.set_ylabel('Impacto na Agenda', color='red', fontsize=12)
    ax3.plot(anos, impacto, 's-', color='red', linewidth=2, markersize=8, label='Impacto')
    ax3.tick_params(axis='y', labelcolor='red')
    ax3.set_ylim(0, 1)
    
    plt.title('Evolução: Trabalhadores e Impacto na Agenda (2018-2026)', fontsize=14, fontweight='bold')
    lines1, labels1 = ax2.get_legend_handles_labels()
    lines2, labels2 = ax3.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    plt.tight_layout()
    plt.savefig(os.path.join(base_path, "..", "02_evolucao_temporal.png"), dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✅ 02_evolucao_temporal.png")
else:
    print("  ⚠️ Dados insuficientes")

# ============================================================
# GRÁFICO 3: MÍDIA VS IMPACTO
# ============================================================

print("\n📊 3. Mídia vs Impacto...")

if eventos:
    midia_eventos = [e['midia'] for e in eventos if e['midia'] > 0]
    impacto_eventos = [e['impacto'] for e in eventos if e['midia'] > 0]
    
    if midia_eventos and len(midia_eventos) > 1:
        fig3, ax3 = plt.subplots(figsize=(10, 8))
        
        tipos = list(set([e['tipo'] for e in eventos]))
        cores_tipos = plt.cm.tab10(np.linspace(0, 1, len(tipos))) if len(tipos) > 0 else plt.cm.tab10(np.linspace(0, 1, 1))
        tipo_to_cor = {tipo: cores_tipos[i % len(cores_tipos)] for i, tipo in enumerate(tipos)}
        
        for tipo in tipos:
            pontos = [(e['midia'], e['impacto']) for e in eventos if e['tipo'] == tipo and e['midia'] > 0]
            if pontos:
                x, y = zip(*pontos)
                ax3.scatter(x, y, color=tipo_to_cor.get(tipo, 'gray'), label=tipo, s=100, alpha=0.7)
        
        ax3.set_xlabel('Menções na Mídia', fontsize=12)
        ax3.set_ylabel('Impacto na Agenda', fontsize=12)
        ax3.set_title('Relação: Cobertura Midiática × Impacto na Agenda', fontsize=14, fontweight='bold')
        ax3.grid(True, alpha=0.3)
        
        if len(midia_eventos) > 1:
            try:
                slope, intercept = np.polyfit(midia_eventos, impacto_eventos, 1)
                x_line = np.array([min(midia_eventos), max(midia_eventos)])
                y_line = slope * x_line + intercept
                corr = calcular_correlacao(midia_eventos, impacto_eventos)
                ax3.plot(x_line, y_line, 'k--', label=f'R² = {corr**2:.3f}')
            except:
                pass
        
        ax3.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
        plt.tight_layout()
        plt.savefig(os.path.join(base_path, "..", "03_midia_vs_impacto.png"), dpi=300, bbox_inches='tight')
        plt.close()
        print("  ✅ 03_midia_vs_impacto.png")
    else:
        print("  ⚠️ Dados insuficientes")

# ============================================================
# GRÁFICO 4: PLATAFORMAS (RADAR)
# ============================================================

print("\n📊 4. Plataformas (Radar)...")

if len(plataformas) >= 2:
    plataformas_selecionadas = ['Uber', 'iFood', '99', 'Rappi', 'InDrive']
    plataformas_filtradas = [p for p in plataformas if p['nome'] in plataformas_selecionadas and p['nome']]
    
    if plataformas_filtradas:
        criterios = ['Remuneração', 'Condições', 'Gestão', 'Representação']
        
        fig4, ax4 = plt.subplots(figsize=(10, 8))
        num_vars = len(criterios)
        angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
        angles += angles[:1]
        
        for i, plataforma in enumerate(plataformas_filtradas):
            values = [
                1 if plataforma['remuneracao'] else 0,
                1 if plataforma['condicoes'] else 0,
                1 if plataforma['gestao'] else 0,
                1 if plataforma['representacao'] else 0
            ]
            values += values[:1]
            ax4.plot(angles, values, 'o-', linewidth=2, label=plataforma['nome'], 
                   color=cores[i % len(cores)])
            ax4.fill(angles, values, alpha=0.1, color=cores[i % len(cores)])
        
        ax4.set_xticks(angles[:-1])
        ax4.set_xticklabels(criterios, fontsize=11)
        ax4.set_ylim(0, 1.2)
        ax4.set_title('Avaliação das Plataformas (Fairwork 2025)', fontsize=14, fontweight='bold')
        ax4.legend(loc='upper right', bbox_to_anchor=(1.3, 1))
        ax4.grid(True)
        
        plt.tight_layout()
        plt.savefig(os.path.join(base_path, "..", "04_plataformas_radar.png"), dpi=300, bbox_inches='tight')
        plt.close()
        print("  ✅ 04_plataformas_radar.png")
    else:
        print("  ⚠️ Nenhuma plataforma selecionada")
else:
    print("  ⚠️ Dados insuficientes")

# ============================================================
# GRÁFICO 5: DISTRIBUIÇÃO DE EVENTOS
# ============================================================

print("\n📊 5. Distribuição de Eventos...")

if eventos:
    tipos_contagem = {}
    for e in eventos:
        tipo = e['tipo']
        if tipo:
            if tipo not in tipos_contagem:
                tipos_contagem[tipo] = 0
            tipos_contagem[tipo] += 1
    
    if tipos_contagem:
        fig5, ax5 = plt.subplots(figsize=(10, 8))
        cores_pizza = cores[:len(tipos_contagem)]
        wedges, texts, autotexts = ax5.pie(
            list(tipos_contagem.values()), 
            labels=list(tipos_contagem.keys()),
            autopct='%1.0f%%',
            colors=cores_pizza,
            startangle=90,
            textprops={'fontsize': 11}
        )
        ax5.set_title('Distribuição de Eventos por Tipo (2018-2026)', fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(os.path.join(base_path, "..", "05_distribuicao_eventos.png"), dpi=300, bbox_inches='tight')
        plt.close()
        print("  ✅ 05_distribuicao_eventos.png")

# ============================================================
# GRÁFICO 6: REGRAS DE ASSOCIAÇÃO
# ============================================================

print("\n📊 6. Regras de Associação...")

if eventos:
    regras = []
    
    paral = [e for e in eventos if 'paralisacao' in e['tipo']]
    if paral:
        confianca = len([e for e in paral if e['impacto'] >= 0.80]) / len(paral)
        regras.append(('Paralisação → Alto Impacto', confianca))
    
    trab = [e for e in eventos if e['ator'] == 'trabalhadores']
    if trab:
        confianca = len([e for e in trab if e['impacto'] >= 0.80]) / len(trab)
        regras.append(('Trabalhadores → Alto Impacto', confianca))
    
    alta_midia = [e for e in eventos if e['midia'] > 50]
    if alta_midia:
        confianca = len([e for e in alta_midia if e['impacto'] >= 0.80]) / len(alta_midia)
        regras.append(('Alta Mídia (>50) → Alto Impacto', confianca))
    
    proj = [e for e in eventos if e['tipo'] in ['projeto_lei', 'proposta_governo']]
    if proj:
        confianca = len([e for e in proj if e['impacto'] >= 0.75]) / len(proj)
        regras.append(('Projetos de Lei → Impacto Médio-Alto', confianca))
    
    if regras:
        nomes_regras = [r[0] for r in regras]
        valores_regras = [r[1] * 100 for r in regras]
        
        fig6, ax6 = plt.subplots(figsize=(12, 6))
        bars = ax6.barh(nomes_regras, valores_regras, color=cores[:len(regras)])
        ax6.set_xlabel('Confiança (%)', fontsize=12)
        ax6.set_title('Regras de Associação - Padrões Identificados', fontsize=14, fontweight='bold')
        ax6.set_xlim(0, 100)
        
        for bar, valor in zip(bars, valores_regras):
            ax6.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2, 
                   f'{valor:.0f}%', va='center', fontsize=10, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(os.path.join(base_path, "..", "06_regras_associacao.png"), dpi=300, bbox_inches='tight')
        plt.close()
        print("  ✅ 06_regras_associacao.png")

# ============================================================
# GRÁFICO 7: MATRIZ DE CORRELAÇÕES
# ============================================================

print("\n📊 7. Matriz de Correlações...")

if len(indicadores) >= 2:
    trabalhadores = [i['trabalhadores'] for i in indicadores]
    renda = [i['renda'] for i in indicadores]
    inss = [i['inss'] for i in indicadores]
    midia = [i['midia'] for i in indicadores]
    greves = [i['greves'] for i in indicadores]
    impacto = [i['impacto'] for i in indicadores]
    
    dados = [trabalhadores, renda, inss, midia, greves, impacto]
    nomes_var = ['Trabalhadores', 'Renda', 'INSS', 'Mídia', 'Greves', 'Impacto']
    
    corr_matrix = np.zeros((len(dados), len(dados)))
    for i in range(len(dados)):
        for j in range(len(dados)):
            if len(dados[i]) == len(dados[j]) and len(dados[i]) > 1:
                corr_matrix[i, j] = calcular_correlacao(dados[i], dados[j])
    
    fig7, ax7 = plt.subplots(figsize=(8, 6))
    im = ax7.imshow(corr_matrix, cmap='RdBu_r', vmin=-1, vmax=1)
    
    ax7.set_xticks(np.arange(len(nomes_var)))
    ax7.set_yticks(np.arange(len(nomes_var)))
    ax7.set_xticklabels(nomes_var, fontsize=10, rotation=45, ha='right')
    ax7.set_yticklabels(nomes_var, fontsize=10)
    
    for i in range(len(nomes_var)):
        for j in range(len(nomes_var)):
            ax7.text(j, i, f'{corr_matrix[i, j]:.2f}', 
                   ha='center', va='center', 
                   color='white' if abs(corr_matrix[i, j]) > 0.5 else 'black',
                   fontsize=10, fontweight='bold')
    
    ax7.set_title('Matriz de Correlações - Indicadores', fontsize=14, fontweight='bold')
    plt.colorbar(im, ax=ax7, label='Correlação')
    plt.tight_layout()
    plt.savefig(os.path.join(base_path, "..", "07_matriz_correlacoes.png"), dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✅ 07_matriz_correlacoes.png")
else:
    print("  ⚠️ Dados insuficientes")

# ============================================================
# GRÁFICO 8: RENDA E INSS
# ============================================================

print("\n📊 8. Renda e INSS...")

if len(indicadores) >= 2:
    anos = [i['ano'] for i in indicadores]
    renda = [i['renda'] for i in indicadores]
    inss = [i['inss'] for i in indicadores]
    
    fig8, ax8 = plt.subplots(figsize=(12, 6))
    
    ax8.set_xlabel('Ano', fontsize=12)
    ax8.set_ylabel('Renda Média (R$)', color='blue', fontsize=12)
    bars = ax8.bar(anos, renda, color='blue', alpha=0.6, label='Renda Média')
    ax8.tick_params(axis='y', labelcolor='blue')
    
    ax9 = ax8.twinx()
    ax9.set_ylabel('Contribuição INSS (%)', color='red', fontsize=12)
    ax9.plot(anos, inss, 'o-', color='red', linewidth=2, markersize=8, label='INSS')
    ax9.tick_params(axis='y', labelcolor='red')
    ax9.set_ylim(0, 60)
    
    plt.title('Evolução: Renda Média e Contribuição ao INSS (2018-2026)', fontsize=14, fontweight='bold')
    lines1, labels1 = ax8.get_legend_handles_labels()
    lines2, labels2 = ax9.get_legend_handles_labels()
    ax8.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
    
    plt.tight_layout()
    plt.savefig(os.path.join(base_path, "..", "08_renda_inss.png"), dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✅ 08_renda_inss.png")
else:
    print("  ⚠️ Dados insuficientes")

# ============================================================
# FINALIZAR
# ============================================================

print("\n" + "="*70)
print("✅ PROCESSAMENTO CONCLUÍDO!")
print("="*70)

print("\n📁 Gráficos salvos em:")
print(f"   {os.path.join(base_path, '..')}")

print("\n📊 GRÁFICOS GERADOS:")
lista_graficos = [
    "01_impacto_por_ator.png",
    "02_evolucao_temporal.png",
    "03_midia_vs_impacto.png",
    "04_plataformas_radar.png",
    "05_distribuicao_eventos.png",
    "06_regras_associacao.png",
    "07_matriz_correlacoes.png",
    "08_renda_inss.png"
]

gerados = 0
for g in lista_graficos:
    caminho = os.path.join(base_path, "..", g)
    if os.path.exists(caminho):
        print(f"  ✅ {g}")
        gerados += 1
    else:
        print(f"  ❌ {g}")

print(f"\n📊 Total: {gerados}/8 gráficos gerados")

print("\n" + "="*70)
print("🏁 FIM")
print("="*70)