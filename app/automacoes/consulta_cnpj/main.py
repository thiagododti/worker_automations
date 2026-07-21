class ConsultaCnpjWs:
    from app.automacoes.consulta_cnpj.schema import EnvelopeConsultaCnpj
    from app.shared.botlogger import Botlogger

    def __init__(self, payload: EnvelopeConsultaCnpj):

        self.payload = payload
        self.url = f"https://publica.cnpj.ws/cnpj/{self.payload.cnpj}"

    def execucao(self):
        import requests

        try:
            botlogger = self.Botlogger(
                empresa=self.payload.empresa_cnpj,
                automacao_id=9,
            )
            botlogger.inicio_execucao()
            botlogger.inicio_etapa(identificacao=self.payload.cnpj)

            response = requests.get(self.url, timeout=30)

            print(f"Consulta realizada para CNPJ: {self.payload.cnpj}")
            botlogger.fim_etapa()
            botlogger.fim_execucao()
            return response.json()

        except requests.RequestException as e:
            print(f"Erro ao consultar CNPJ {self.payload.cnpj}: {e}")
            botlogger.erro_etapa(f"Erro ao consultar CNPJ {self.payload.cnpj}: {e}")
            botlogger.erro_execucao(f"Execução com erro: {e}")

            return {"error": "Erro ao conectar com a API.", "data": str(e)}
