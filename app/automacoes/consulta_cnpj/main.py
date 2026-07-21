class ConsultaCnpjWs:
    from app.automacoes.consulta_cnpj.schema import EnvelopeConsultaCnpj

    def __init__(self, payload: EnvelopeConsultaCnpj):

        self.payload = payload
        self.url = f"https://publica.cnpj.ws/cnpj/{self.payload.cnpj}"

    def execucao(self):
        import requests

        try:
            response = requests.get(self.url, timeout=30)

            print(f"Consulta realizada para CNPJ: {self.payload.cnpj}")

            return response.json()

        except requests.RequestException as e:
            print(f"Erro ao consultar CNPJ {self.payload.cnpj}: {e}")
            return {"error": "Erro ao conectar com a API.", "data": str(e)}
