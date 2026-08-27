"""
agente_eduseg.py
----------------
Motor de Agente Multi-Fases do SAD-EduSeg.
Usa Groq (Llama 3, gratuito) + DuckDuckGo Search (gratuito, sem API key).
Padrão adaptado do vacation-planner-web/agents.py.
"""

import json
import re
from duckduckgo_search import DDGS


def buscar_web(query: str) -> str:
    """Busca gratuita na internet via DuckDuckGo (sem API key)."""
    try:
        results = DDGS().text(query, max_results=3)
        resumo = []
        for r in results:
            resumo.append(f"- {r.get('title', '')}: {r.get('body', '')}")
        return "\n".join(resumo) if resumo else "Nenhum resultado encontrado."
    except Exception as e:
        return f"Erro na busca: {str(e)}"


SYSTEM_PROMPT_TEMPLATE = """Você é o **Copiloto EduSeg**, um conselheiro especialista em políticas públicas integradas de Segurança Pública e Educação do Estado da Bahia.

## Contexto Atual do SAD (Dados do Banco de Dados SQLite)
{contexto_banco}

## Suas Capacidades
Você opera em 3 fases automáticas:

### FASE 1 — Diagnóstico
Quando o gestor perguntar sobre uma escola ou bairro específico, analise os dados do banco acima e apresente um diagnóstico claro: IVS, assiduidade, crimes no entorno, nível de risco.

### FASE 2 — Pesquisa em Tempo Real
Quando o gestor pedir dados atualizados, informações do INEP, notícias recentes da SSP-BA ou estatísticas públicas, você receberá resultados de busca da web. Use-os para enriquecer sua análise com dados reais e públicos.

### FASE 3 — Recomendação de Política Pública
Com base no diagnóstico e nos dados reais, recomende ações concretas seguindo o framework de Blend de Opções:
- **Blend A (Policial):** Ronda Escolar, câmeras COI, iluminação.
- **Blend B (Pedagógico):** Escola integral, busca ativa, quadras abertas.
- **Blend C (Preventivo):** Policiamento comunitário + monitoramento de frequência.

## Regras
- Responda SEMPRE em Português do Brasil.
- Seja analítico, conciso e baseado em dados.
- Quando citar dados da web, indique a fonte.
- Use Markdown para formatar a resposta.
- Quando mencionar dados de busca na web, prefixe com 🌐.
"""

DETECT_SEARCH_PROMPT = """Analise a mensagem do usuário abaixo e determine se é necessário fazer uma busca na web para respondê-la.

Retorne APENAS um JSON com este formato, sem texto adicional:
{"needs_search": true, "search_query": "texto para buscar"}

Se NÃO precisar de busca (a pergunta pode ser respondida apenas com os dados do banco), retorne:
{"needs_search": false, "search_query": ""}

Exemplos que PRECISAM de busca:
- "Quais são os dados atualizados do IDEB em Salvador?"
- "Qual a taxa de criminalidade atual no subúrbio ferroviário?"
- "Tem alguma notícia recente sobre evasão escolar na Bahia?"

Exemplos que NÃO precisam:
- "Qual o nível de risco da escola Nelson Mandela?"
- "Quantos alunos estão em risco de evasão?"
- "Qual a melhor política para essa escola?"

Mensagem do usuário: {mensagem}
"""


class AgenteEduSeg:
    """Agente multi-fases com busca web gratuita para o SAD-EduSeg."""

    def __init__(self, api_key: str, model: str = "llama3-8b-8192"):
        self.api_key = api_key
        self.model = model

    def _chamar_groq(self, system_prompt: str, messages: list) -> str:
        """Chama a API Groq diretamente (sem LangChain, zero custo adicional)."""
        from groq import Groq
        client = Groq(api_key=self.api_key)

        msgs_api = [{"role": "system", "content": system_prompt}]
        for m in messages:
            msgs_api.append({"role": m["role"], "content": m["content"]})

        response = client.chat.completions.create(
            model=self.model,
            messages=msgs_api,
            temperature=0.7,
            max_tokens=2048,
        )
        return response.choices[0].message.content

    def _detectar_busca(self, mensagem: str) -> dict:
        """Usa o LLM para decidir se precisa buscar na web."""
        try:
            from groq import Groq
            client = Groq(api_key=self.api_key)

            prompt = DETECT_SEARCH_PROMPT.format(mensagem=mensagem)
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=256,
            )
            text = response.choices[0].message.content.strip()
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception:
            pass
        return {"needs_search": False, "search_query": ""}

    def chat(self, mensagem: str, historico: list, contexto_banco: str) -> dict:
        """
        Processa a mensagem do gestor e retorna resposta enriquecida.

        Returns:
            {"response": str, "fase": str, "buscou_web": bool}
        """
        # Fase 1: Detectar se precisa buscar na web
        busca_info = self._detectar_busca(mensagem)
        resultado_busca = ""
        buscou = False

        # Fase 2: Se precisa, buscar dados reais gratuitos via DuckDuckGo
        if busca_info.get("needs_search"):
            query = busca_info.get("search_query", mensagem)
            resultado_busca = buscar_web(query)
            buscou = True

        # Montar contexto completo
        contexto_completo = contexto_banco
        if resultado_busca:
            contexto_completo += f"\n\n## 🌐 Dados Atualizados da Web (DuckDuckGo)\n{resultado_busca}"

        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(contexto_banco=contexto_completo)

        # Fase 3: Gerar resposta final
        resposta = self._chamar_groq(system_prompt, historico + [{"role": "user", "content": mensagem}])

        fase = "Pesquisa + Recomendação" if buscou else "Diagnóstico + Recomendação"

        return {
            "response": resposta,
            "fase": fase,
            "buscou_web": buscou,
        }
