class ConsultaCNDTInfoSimples:
    from app.automacoes.consulta_cndt.schema import EnvelopeConsultaCNDT

    def __init__(self, payload: EnvelopeConsultaCNDT):
        import os

        self.payload = payload
        self.url = "https://api.infosimples.com/api/v2/consultas/tribunal/tst/cndt"
        self.params = {
            "token": os.getenv("INFOSIMPLES_TOKEN"),
            "timeout": 600,
            "ignore_site_receipt": 0,
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
            response = requests.get(self.url, params=self.params, timeout=30)

            if self.payload.cnpj:
                print(f"Consulta realizada para CNPJ: {self.payload.cnpj}")
            elif self.payload.cpf:
                print(f"Consulta realizada para CPF: {self.payload.cpf}")

            return response.json()

        except requests.RequestException as e:
            if self.payload.cnpj:
                print(f"Erro ao consultar cndt {self.payload.cnpj}: {e}")
            elif self.payload.cpf:
                print(f"Erro ao consultar cndt {self.payload.cpf}: {e}")
            return {"error": "Erro ao conectar com a API.", "data": str(e)}
