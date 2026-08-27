import requests
import pandas as pd


class CamaraAPIService:
    """Classe responsável por consumir dados em tempo real da API da Câmara dos Deputados
    para alimentar o SAD-AgendaPública.
    """

    BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"

    def __init__(self):
        # Cabeçalho padrão exigido pela API da Câmara para monitoramento de tráfego
        self.headers = {"accept": "application/json"}

    def buscar_projetos_lei(self, palavra_chave="aplicativo"):
        """Busca projetos de lei em tramitação baseados em uma palavra-chave."""
        endpoint = f"{self.BASE_URL}/proposicoes"
        params = {
            "keywords": palavra_chave,
            "siglaTipo": ["PL", "PLP"],  # PL: Projeto de Lei | PLP: Lei Complementar
            "ordem": "DESC",
            "ordenarPor": "ano",
        }

        print(f"[API] Conectando à Câmara para buscar proposições sobre '{palavra_chave}'...")

        try:
            response = requests.get(endpoint, params=params, headers=self.headers, timeout=15)

            if response.status_code == 200:
                dados = response.json().get("dados", [])
                print(f"[API] Sucesso! {len(dados)} proposições encontradas.")
                return dados
            else:
                print(f"[ERRO] Falha na conexão. Código de Status: {response.status_code}")
                return []
        except Exception as e:
            print(f"[ERRO] Falha catastrófica ao conectar à API: {str(e)}")
            return []

    def obter_detalhes_projeto(self, id_proposicao):
        """Busca a situação atualizada e o andamento detalhado de um projeto específico."""
        endpoint = f"{self.BASE_URL}/proposicoes/{id_proposicao}"

        try:
            response = requests.get(endpoint, headers=self.headers, timeout=10)
            if response.status_code == 200:
                return response.json().get("dados", {})
        except Exception as e:
            print(f"[ERRO] Não foi possível obter detalhes do ID {id_proposicao}: {e}")
        return {}


# ==============================================================================
# FLUXO DE INTEGRAÇÃO DO DATA ANALYST COM O MODELO DE DECISÃO (SAD)
# ==============================================================================
if __name__ == "__main__":
    api_camara = CamaraAPIService()
    dados_brutos = api_camara.buscar_projetos_lei(palavra_chave="aplicativo")

    if dados_brutos:
        df_projetos = pd.DataFrame(dados_brutos)
        if not df_projetos.empty:
            df_projetos = df_projetos[["id", "siglaTipo", "numero", "ano", "ementa"]]

            print("\n--- PROCESSAMENTO DE DADOS (DATA ANALYST) ---")
            df_projetos["Viabilidade_Politica"] = "Média"
            df_projetos["Impacto_Economico"] = "Alto"

            df_projetos.loc[df_projetos["siglaTipo"] == "PLP", "Viabilidade_Politica"] = "Dificil"

            print(df_projetos.head(5))

            print("\n--- MÓDULO DECISÓRIO (SAD - BLEND DE OPÇÕES) ---")
            contagem_plp = len(df_projetos[df_projetos["siglaTipo"] == "PLP"])
            total_projetos = len(df_projetos)

            if contagem_plp / total_projetos > 0.2:
                print("[SAD Decisão] Tendência detectada: Forte movimentação via Leis Complementares.")
                print("[Recomendação] Ativar 'Blend de Opção B: Terceira Via Regulada'.")
            else:
                print("[SAD Decisão] Ambiente legislativo padrão.")
                print("[Recomendação] Avançar com 'Opção C: Microempreendedorismo Cooperativo'.")
