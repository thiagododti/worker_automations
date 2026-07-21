class ConsultaFgtsInfoSimples:
    from app.automacoes.consulta_fgts.schema import EnvelopeConsultaFgts
    from app.shared.botlogger import Botlogger

    def __init__(self, payload: EnvelopeConsultaFgts):
        import os

        self.payload = payload
        self.url = "https://api.infosimples.com/api/v2/consultas/caixa/regularidade"
        self.params = {
            "token": os.getenv("INFOSIMPLES_TOKEN"),
            "timeout": 600,
            "ignore_site_receipt": 0,
            "preferencia_emissao": "nova",
        }
        if self.payload.cnpj:
            self.params["cnpj"] = self.payload.cnpj
        elif self.payload.cpf:
            self.params["cpf"] = self.payload.cpf
        else:
            raise ValueError("É necessário fornecer um CNPJ ou CPF para a consulta.")

    def execucao(self):
        import requests

        try:
            botlogger = self.Botlogger(
                empresa=self.payload.empresa_cnpj,
                automacao_id=19,
            )
            botlogger.inicio_execucao()
            botlogger.inicio_etapa(
                identificacao=self.payload.cnpj or self.payload.cpf or "consultando_api"
            )
            response = requests.get(self.url, params=self.params, timeout=30)
            dados = response.json()
            if self.payload.cnpj:
                print(f"Consulta realizada para CNPJ: {self.payload.cnpj}")
            elif self.payload.cpf:
                print(f"Consulta realizada para CPF: {self.payload.cpf}")
            if dados.get("code") == 200:
                botlogger.fim_etapa()
            else:
                botlogger.alerta_etapa(
                    f"Consulta retornou código {dados.get('code')} Consulta não foi realizada com sucesso."
                )
            botlogger.fim_etapa()
            botlogger.fim_execucao()
            return dados

        except requests.RequestException as e:
            if self.payload.cnpj:
                print(f"Erro ao consultar cnd fgts {self.payload.cnpj}: {e}")
                botlogger.erro_etapa(
                    f"Erro ao consultar cnd fgts {self.payload.cnpj}: {e}"
                )
            elif self.payload.cpf:
                print(f"Erro ao consultar cnd fgts {self.payload.cpf}: {e}")
                botlogger.erro_etapa(
                    f"Erro ao consultar cnd fgts {self.payload.cpf}: {e}"
                )
            botlogger.erro_execucao(f"Execução com erro: {e}")
            return {"error": "Erro ao conectar com a API.", "data": str(e)}
