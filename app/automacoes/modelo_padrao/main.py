class ModeloPadrao:
    from app.automacoes.modelo_padrao.schema import EnvelopePadrao

    def __init__(self, payload: EnvelopePadrao):
        self.payload = payload

    def execucao(self):
        print(f"Consultando CNPJ: {self.payload.cnpj}")
